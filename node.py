#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server, Handler
from server import Channel, LineChannel
from state import Follower, Leader
from protocol.message import Message, ClientMessage, NodeMessage
from db import SimpleDB


class MessageChannel(Channel):
    def __init__(self, server, client, next):
        super(MessageChannel, self).__init__(server, client, next)

    def input(self, data, recv):
        if recv:
            message = Message.parse(data, self.client)
        else:
            message = data
        if message:
            return self.next.input(message, recv)

    def output(self):
        response, end = self.next.output()
        return '%s' % response, end


class NodeHandler(Handler):
    def __init__(self, node):
        self.node = node

    def handle(self, server, client, request):
        return self.node.dispatch(server, client, request)


class Node(object):
    def __init__(self, host, port, neighbors=None, db=None):
        self.host = host
        self.port = port
        self.neighbors = neighbors
        self.db = db if db else SimpleDB()
        self.server = Server(self.port)
        self.server.register_channel(LineChannel)
        self.server.register_channel(MessageChannel)
        self.server.register_handler(NodeHandler(self))
        self.state = Follower(self)
        self.leader = None

    def dispatch(self, server, client, message):
        if isinstance(message, ClientMessage):
            if message.op == 'get' or isinstance(self.state, Leader):
                return self.db.handle(client, message.op, message.key, message.value, message.auto_commit)
            else:
                #set del commit 操作需要重定位到leader操作
                return self.leader if self.leader else 'None'
        elif isinstance(message, NodeMessage):
            return self.state.handle(message)
        else:
            return message

    @property
    def node_key(self):
        # 这里不能用getsockname 会返回0.0.0.0
        # return self.server.accepter.getsockname()
        return (self.host, self.port)

    def start(self):
        self.server.server_forever()


if __name__ == '__main__':
    import sys
    host = '127.0.0.1'
    port = 2333
    nei = None
    neighbors = None
    try:
        host = sys.argv[1]
    except:
        sys.exit(1)
    try:
        port = int(sys.argv[2])
    except:
        sys.exit(1)
    try:
        nei = sys.argv[3:]
        if nei and len(nei) % 2 == 0:
            neighbors = []
            for i in xrange(0, len(nei), 2):
                neighbors.append((nei[i], int(nei[i+1])))
    except:
        sys.exit(1)
    node = Node(host, port, neighbors)
    node.start()