#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'aducode@126.com'
import select
import socket
from coroutine import coroutine


@coroutine
def handler():
    msg = yield
    while True:
        if msg:
            ret = msg.upper()
        else:
            ret = None
        msg = yield ret


def coroutine_handle(msg):
    yield msg.upper()


class Reactor(object):
    """
    调度协程的类
    """
    def __init__(self, host='', port=7777):
        """
        构造方法
        :return:
        """
        self.port = port
        self.host = host
        self.accepter = None
        self.inputs = []
        self.outputs = []
        self.exceptions = []
        self.stopped = False
        self.context = {}
        # self.handler = handler()

    def _initialise(self):
        """
        初始化相关资源
        :return:
        """
        self.accepter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.accepter.setblocking(False)
        self.accepter.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.accepter.bind((self.host, self.port))
        self.accepter.listen(10)
        self.inputs.append(self.accepter)

    def _close_conn(self, conn):
        print 'Close connection...'
        if conn in self.context:
            del self.context[conn]
        if conn in self.inputs:
            self.inputs.remove(conn)
        if conn in self.outputs:
            self.outputs.remove(conn)
        if conn in self.exceptions:
            self.exceptions.remove(conn)
        conn.close()

    def _handle_io_event(self):
        """
        处理IO事件
        :return:
        """
        if not self.inputs:
            self.stopped = True
            return
        readable, writable, exceptional = select.select(self.inputs, self.outputs, self.exceptions)
        for r in readable:
            if r is self.accepter:
                # 说明accepter接收了一个新的tcp连接
                connection, addr = r.accept()
                print 'Accept a client:', addr
                self.inputs.append(connection)
            else:
                # 说明有数据
                try:
                    data = r.recv(1024)
                except socket.error:
                    self._close_conn(r)
                else:
                    print 'Recv from client:', data
                    # self.context[r]=self.handler.send(data) # 保留 output用
                    self.context[r] = coroutine_handle(data)
                    self.outputs.append(r)
        for w in writable:
            # 处理output
            data = self.context[w].next()
            try:
                w.send(data)
            except socket.error:
                self._close_conn(w)
            else:
                if w in self.outputs:
                    self.outputs.remove(w)
        for e in exceptional:
            # 处理异常
            self._close_conn(e)

    def server_forever(self):
        """
        Reactor Main Loop
        :return:
        """
        self._initialise()
        while not self.stopped:
            self._handle_io_event()