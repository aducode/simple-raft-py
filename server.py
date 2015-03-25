#!/usr/bin/python
# -*- coding:utf-8 -*-
import socket
import select
import Queue
import time


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
    """
    保存客户端连接
    """

    def __init__(self, client):
        self.client = client


class Input(object):
    def input(self):
        pass


class Output(object):
    def output(self):
        pass


class Buffer(Input, Output):
    pass


class BaseBuffer(Buffer):
    def __init__(self, channel):
        self.channel = channel
        self.input_buf = Queue.Queue()
        self.output_buf = Queue.Queue()

    def input(self, data):
        self.input_buf.put(data)

    def output(self):
        try:
            data = self.output_buf.get_nowait()
        except Queue.Empty:
            return None
        else:
            return data


class Server(object):
    def __init__(self, address='', port=2333):
        self.address = address
        self.port = port
        self.inputs = []
        self.outputs = []
        self.exceptions = []
        self.input_buffer = {}
        self.request_queue = {}
        self.response_queue = {}
        self.timers = {}
        self.running = False

        def echo_timer(except_time, real_time, value):
            print '[%s]happen:except_time:%.3f, real:%.3f' % (value, except_time, real_time, )

        # def stop_the_server(except_time, real_time, server):
        # print 'stop the server'
        # server.running = False

        self.set_timer(0.3, True, echo_timer, 1)
        #self.set_timer(3, False, stop_the_server, self)

    def handle(self, request):
        """
        处理IO
        :param request: 接收到数据
        :return: 返回的response
        """
        print 'handle the request:\n', request
        return request

    def do_io(self):
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
                self.request_queue[connection] = Queue.Queue()
                self.input_buffer[connection] = ''
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
                        if '\n' not in data:
                            self.input_buffer[r] += data
                        else:
                            msgs = data.split('\n')
                            self.input_buffer[r] += msgs[0]
                            self.request_queue[r].put(self.input_buffer[r])
                            for i in xrange(1, len(msgs) - 1):
                                self.request_queue.put(msgs[i])
                            self.input_buffer[r] = msgs[len(msgs) - 1]
                        # print 'receive data: ', request, ' from ', r.getpeername()
                        # TODO check request type
                        # if has a high priority
                        # we can fast handle it like this:
                        # if r not in self.reponse_queue:
                        # self.response_queue[r]=Queue.Queue()
                        # self.response_queue[r] = self.handle(request)
                        # self.request_queue[r].put(request)
                        if r not in self.outputs:
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
                    del self.request_queue[r]
                    del self.response_queue[r]
                    del self.input_buffer[r]
        for w in writable:
            try:
                response = self.response_queue[w].get_nowait()
            except Queue.Empty:
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
            del self.request_queue[e]
            del self.response_queue[e]
            del self.input_buffer[e]

    def handle_requests(self):
        # print 'handle the request ...'
        for client, requests in self.request_queue.items():
            if client not in self.response_queue:
                self.response_queue[client] = Queue.Queue()
            try:
                request = requests.get_nowait()
            except Queue.Empty:
                pass
            else:
                # send response to the response_queue, it will be sent in next loop
                self.response_queue[client].put(self.handle(request))

    def handle_timers(self):
        # print 'handle the timers ...'
        current = time.time()
        for t, events in self.timers.items():
            if t <= current and self.running:
                # 说明已经过了或者到时间了，需要处理
                for event in events:
                    event.invoke(t, current)
                    if event.is_cron:
                        next_time = event.time + t
                        if next_time not in self.timers:
                            self.timers[next_time] = []
                        self.timers[next_time].append(event)
                    self.timers[t].remove(event)
                # 处理完了，就删除
                del self.timers[t]

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
        """
        停止服务, 释放资源
        :return:
        """
        if self.running:
            return
        for conn in self.request_queue:
            try:
                conn.close()
            except Exception:
                pass
            self.request_queue.remove(conn)
        for conn in self.response_queue:
            try:
                conn.close()
            except Exception:
                pass
            self.response_queue.remove(conn)
        if self.accepter:
            try:
                self.accepter.close()
            except Exception:
                pass

    def server_forever(self):
        self.running = True
        self.accepter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.accepter.setblocking(False)
        self.accepter.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.accepter.bind((self.address, self.port))
        self.accepter.listen(10)
        self.inputs.append(self.accepter)
        # Main Loop
        # timeout 5ms
        self.timeout = 0.05
        while self.inputs:
            # handle io
            self.do_io()
            # handle message
            self.handle_requests()
            # handle timer
            self.handle_timers()
            if not self.running:
                self.stop()
                break

        print 'Server stopped!'

