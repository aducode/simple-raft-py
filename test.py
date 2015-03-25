#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server, LineChannel, Channel

if __name__ == '__main__':
    s = Server(channels=LineChannel)

    def my_time_handler(target_time, real_time, value):
        print '%.3f-----%.3f:%d' %(target_time, real_time, value)

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
    s.set_timer(3, True, my_time_handler, 1)
    s.server_forever()