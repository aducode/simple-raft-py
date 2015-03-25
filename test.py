#!/usr/bin/python
# -*- coding:utf-8 -*-
# from node import Node
# import config
# import sys

import server

if __name__ == '__main__':
    # if len(sys.argv) <= 1:
    #     print 'Usage: port'
    #     exit(1)
    # try:
    #     port = int(sys.argv[1])
    # except ValueError, e:
    #     print 'Usage: port'
    #
    # n = Node(config.NODE_TABLE, addr=('127.0.0.1', port)).run()
    s = server.Server()
    s.server_forever()
