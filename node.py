#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server, Handler
from server import LineChannel
from state import Follower


class NodeHandler(Handler):
    def __init__(self, node):
        self.node = node

    def handle(self, server, client, request):
        print request
        return request


class Node(object):

    def __init__(self, port, neighbors=None):
        self.port = port
        self.neighbors = neighbors
        self.state = Follower(self)
        self.server = Server(self.port)
        self.server.register_channel(LineChannel)
        self.server.register_handler(NodeHandler(self))

    def start(self):
        self.server.server_forever()


if __name__ == '__main__':
    node = Node(2333)
    node.start()