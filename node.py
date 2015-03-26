#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server, Handler
from server import Channel, LineChannel
from state import Follower
from protocol.message import Message, ClientMessage
from db import SimpleDB


class MessageChannel(Channel):
    def __init__(self, server, client, next):
        super(MessageChannel, self).__init__(server, client, next)

    def input(self, data):
        message = Message.parse(data)
        if message:
            return self.next.input(message)

    def output(self):
        response, end = self.next.output()
        return '%s' % response, end


class NodeHandler(Handler):
    def __init__(self, node):
        self.node = node

    def handle(self, server, client, request):
        return self.node.dispatch(server, client, request)


class Node(object):
    def __init__(self, port, neighbors=None, db=None):
        self.port = port
        self.neighbors = neighbors
        self.state = Follower(self)
        self.db = db if db else SimpleDB()
        self.server = Server(self.port)
        self.server.register_channel(LineChannel)
        self.server.register_channel(MessageChannel)
        self.server.register_handler(NodeHandler(self))

    def dispatch(self, server, client, message):
        # print message
        if isinstance(message, ClientMessage):
            return self.db.handle(client, message.op, message.key, message.value, message.auto_commit)
        return message

    def start(self):
        self.server.server_forever()


if __name__ == '__main__':
    node = Node(2333)
    node.start()