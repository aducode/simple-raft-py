#!/usr/bin/python
# -*- coding:utf-8 -*-
import types
import Queue
from handler import Handler


class Channel(object):
    def __init__(self, server, client, next):
        self.server = server
        self.client = client
        self.next = next

    def input(self, data, recv):
        """
        :param data 数据
        :param recv 是否从socket接受来的消息
                    当为False时，说明数据是发送到其他server的，不是server接受来的
        """
        pass

    def output(self):
        pass


class LineChannel(Channel):
    """
    保存客户端连接
    """

    def __init__(self, server, client, next):
        super(LineChannel, self).__init__(server, client, next)
        self.input_buffer = ''

    def input(self, request, recv):
        if '\n' not in request:
            self.input_buffer += request
        else:
            msgs = request.split('\n')
            msg = (self.input_buffer + msgs[0]).strip()
            if msg:
                self.input_buffer = ''
                self.next.input(msg, recv)
            for msg in msgs[1:-1]:
                msg = msg.strip()
                if msg:
                    self.next.input(msg, recv)
            msg = msgs[-1]
            if msg:
                self.input_buffer = msg.strip()

    def output(self):
        data, end = self.next.output()
        return data+'\r\n', end