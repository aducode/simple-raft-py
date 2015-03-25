#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server
from channel import LineChannel

if __name__ == '__main__':
    s = Server(channels=LineChannel)
    s.server_forever()