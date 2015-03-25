#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server, LineChannel, Channel

if __name__ == '__main__':
    s = Server(channels=LineChannel)

    class MyChannel(Channel):
        def __init__(self, server, client, next):
            super(MyChannel, self).__init__(server, client, next)

        def input(self, data):
            print 'my channel input data:', data
            self.next.input(data)

        def output(self):
            data = self.next.output()
            print 'my channel output data:',data
            return data
    s.register_channel(MyChannel)
    s.server_forever()