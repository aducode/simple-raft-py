#!/usr/bin/python
# -*- coding:utf-8 -*-
import socket
import select
import Queue
import time
import types


class TimeEvent(object):
    def __init__(self, func, args, kwargs, target_time, is_cron=True):
        self.func = func
        self.is_cron = is_cron
        self.time = target_time
        self.args = args
        self.kwargs = kwargs

    def invoke(self, excepted_time, real_time):
        self.func(excepted_time, real_time, *self.args, **self.kwargs)


class Channel(object):
    def __init__(self, server, client, next):
        self.server = server
        self.client = client
        self.next = next

    def input(self, data):
        pass

    def output(self):
        pass


class Handler(object):
    def __init__(self, server, client):
        self.server = server
        self.client = client

    def handle(self, request):
        pass


class DefaultHandler(Handler):
    def __init__(self, server, client):
        super(DefaultHandler, self).__init__(server, client)

    def handle(self, request):
        print '[%s]handle the request\n%s' % (self.client.getpeername(), request)
        if request == 'quit':
            self.server.stop()
        return request


class LineChannel(Channel):
    """
    保存客户端连接
    """

    def __init__(self, server, client, next):
        super(LineChannel, self).__init__(server, client, next)
        self.input_buffer = ''
        self.output_queue = Queue.Queue()

    def input(self, request):
        if '\n' not in request:
            self.input_buffer += request
        else:
            msgs = request.split('\n')
            msg = (self.input_buffer + msgs[0]).strip()
            if msg:
                self.input_buffer = ''
                if isinstance(self.next, Channel):
                    self.next.input(msg)
                elif isinstance(self.next, Handler):
                    self.output_queue.put(self.next.handle(msg))
            for msg in msgs[1:-1]:
                msg = msg.strip()
                if msg:
                    if isinstance(self.next, Channel):
                        self.next.input(msg)
                    elif isinstance(self.next, Handler):
                        self.output_queue.put(self.next.handle(msg))
            msg = msgs[-1]
            if msg:
                self.input_buffer = msg.strip()

    def output(self):
        if isinstance(self.next, Channel):
            return self.next.output()
        elif isinstance(self.next, Handler):
            try:
                return self.output_queue.get_nowait()
            except Queue.Empty:
                return


class Server(object):
    def __init__(self, address='', port=2333, **kwargs):
        self.address = address
        self.port = port
        self.inputs = []
        self.outputs = []
        self.exceptions = []
        self.context = {}
        if 'handler' in kwargs and isinstance(kwargs['handler'], Handler):
            self.handler_class = kwargs['handler']
        else:
            self.handler_class = DefaultHandler
        if 'channels' in kwargs:
            cc = kwargs['channels']
            if isinstance(cc, Channel):
                self.channel_class = [cc, ]
            elif (isinstance(cc, types.TupleType) or isinstance(cc, types.ListType)) and len(cc)>0:
                self.channel_class = [c for c in cc if isinstance(c, Channel)]
        else:
            self.channel_class = [LineChannel, ]
        # self.input_buffer = {}
        # self.request_queue = {}
        # self.response_queue = {}
        self.timers = {}
        # 0 running 1 stopping 2 stopped
        self.state = 0

    def get_channel(self, client):
        """
        初始化链式的channel
        :param client:
        :return:
        """
        if not self.channel_class or not self.handler_class:
            return
        c = self.handler_class(self, client)
        for claz in self.channel_class[::-1]:
            c = claz(self, client, c)
        return c

    def handle_io_event(self):
        # print 'waiting for next event'
        readable, writable, exceptional = select.select(self.inputs, self.outputs, self.exceptions, self.timeout)
        for r in readable:
            if r is self.accepter:
                # A readable socket is ready to accept  a connection
                connection, addr = r.accept()
                # print 'connection from, ', addr
                connection.setblocking(False)
                self.inputs.append(connection)
                # print 'accept %s' % connection
                self.context[connection] = self.get_channel(connection)
            else:
                # readable from other system
                client_closed = False
                try:
                    data = r.recv(1024)
                except socket.error:
                    # client  close the socket
                    client_closed = True
                else:
                    if data:
                        self.context[r].input(data)
                        self.outputs.append(r)
                    else:
                        client_closed = True
                if client_closed:
                    # Interrupt empty result as closed connection
                    # print 'client closing....', r.getpeername()
                    if r in self.outputs:
                        self.outputs.remove(r)
                    self.inputs.remove(r)
                    r.close()
                    # remove message queue
                    del self.context[r]
        for w in writable:
            response = self.context[w].output()
            if not response:
                # print 'Empty response queue ', w.getpeername()
                # 这里应该删除，因为本机网络输出一般都处于writable状态，如果不删除，那么将一直被激活
                self.outputs.remove(w)
            else:
                w.send(response)
        for e in exceptional:
            # print 'exception condition on ', e.getpeername()
            self.inputs.remove(e)
            if e in self.outputs:
                self.outputs.remove(e)
            e.close()
            del self.context[e]

    def handle_timeout_event(self):
        # print 'handle the timers ...'
        current = time.time()
        reset_timers = {}
        # 计算下次循环的select 超时时间
        self.timeout = None
        for t, events in self.timers.items():
            if t <= current and self.is_running():
                # 说明已经过了或者到时间了，需要处理
                for event in events:
                    event.invoke(t, current)
                    if event.is_cron:
                        next_time = event.time + t
                        if next_time not in reset_timers:
                            reset_timers[next_time] = []
                        reset_timers[next_time].append(event)
                    self.timers[t].remove(event)
                # 处理完了，就删除
                del self.timers[t]
        self.timers.update(reset_timers)
        for t in self.timers:
            if not self.timeout or (t > current and t - current < self.timeout):
                self.timeout = t - current
                # print 'next timeout is ', self.timeout


    def set_timer(self, target_time, is_cron, func, *args, **kwargs):
        """
        设置时间事件
        :param func: 超时事件处理函数 func(except_time, real_time, *args, **kwargs)
        :param target_time: 时间发生的时间
                            如果target_time<current 那么下次执行时间为target_time+current_time 否则为target_time
        :param is_cron: 是否是定时任务,执行多次，否则只执行一次
        :return:
        """
        current_time = time.time()
        if target_time < current_time:
            real_time = current_time + target_time
        else:
            real_time = target_time
        if real_time not in self.timers:
            self.timers[real_time] = []
        self.timers[real_time].append(TimeEvent(func, args, kwargs, target_time, is_cron))

    def rm_timer(self, func):
        for events in self.timers.values():
            for event in events:
                if func is event.func:
                    events.remove(event)

    def stop(self):
        if self.state == 0:
            self.state = 1

    def is_running(self):
        return self.state == 0

    def is_stopping(self):
        return self.state == 1

    def is_stopped(self):
        return self.state == 2

    def realease(self):
        """
        停止服务, 释放资源
        :return:
        """
        if self.state == 0 or self.state == 2:
            # if running or has stopped, do nothing
            return
        self.state = 2
        self.finalize()

    def finalize(self):
        """
        关闭连接
        :return:
        """
        if self.state == 0 or self.state == 1:
            return
        for conn in self.context:
            try:
                conn.close()
            except Exception:
                pass
            else:
                if conn in self.inputs:
                    self.inputs.remove(conn)
                if conn in self.outputs:
                    self.outputs.remove(conn)
                if conn in self.exceptions:
                    self.exceptions.remove(conn)
        if self.accepter:
            try:
                self.accepter.close()
            except Exception:
                pass
            else:
                if self.accepter in self.inputs:
                    self.inputs.remove(self.accepter)

    def initialise(self):
        """
        初始化
        :return:
        """
        self.accepter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.accepter.setblocking(False)
        self.accepter.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.accepter.bind((self.address, self.port))
        self.accepter.listen(10)
        self.inputs.append(self.accepter)
        # 计算超时时间
        self.timeout = None
        current = time.time()
        for t in self.timers:
            timeout = t - current
            if not self.timeout or (timeout > 0 and timeout < self.timeout):
                self.timeout = timeout
        # set state
        self.state = 0

    def server_forever(self):
        # init the server runtime env
        self.initialise()
        # Main Loop
        while self.inputs:
            # handle io
            self.handle_io_event()
            # handle timer
            self.handle_timeout_event()
            if not self.is_running():
                # stoppde or stopping
                break
        # release the resources
        self.realease()
        print 'Server stopped!'

