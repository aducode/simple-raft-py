#!/usr/bin/python
# -*- coding:utf-8 -*-
from node import Node
import sys

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print 'Usage: port'
        exit(1)
    try:
        port = int(sys.argv[1])
    except ValueError, e:
        print 'Usage: port'

    nodes = [('127.0.0.1', 2333), ('127.0.0.1', 2334), ('127.0.0.1', 2335), ]
    n = Node(nodes, addr=('127.0.0.1', port)).run()
