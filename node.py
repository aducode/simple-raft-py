#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server, Handler
from server import Channel, LineChannel
from state import Follower
from protocol.message import Message, ClientCloseMessage, InvalidMessage


class MessageChannel(Channel):
    """
    node消息Channel
    """
    def __init__(self, server, client, _next):
        """
        构造方法
        :param server 服务端
        :param client 客户端
        :param _next   channle链的下一个
        :return
        """
        super(MessageChannel, self).__init__(server, client, _next)

    def input(self, data, recv):
        """
        数据流入MessageChannel
        :param data 上个channel来的数据
        :param  recv 为False时表明不是server接收的
        :return
        """
        if recv:
            message = Message.parse(data, self.client)
        else:
            message = data
        if message:
            return self.next.input(message, recv)

    def output(self):
        """
        流出数据到下一个channel
        :return
        """
        response, end = self.next.output()
        return '%s' % (response, ) if response else None, end


class NodeHandler(Handler):
    """
    节点使用的网络事件处理类
    """
    def __init__(self, _node):
        """
        构造方法
        :param _node
        :return
        """
        self.node = _node

    def handle(self, server, client, request):
        """
        事件处理方法
        :param server
        :param client
        :param request
        :return
        """
        return self.node.dispatch(server, client, request)

    def close(self, server, client):
        """
        这里封装一个ClientCloseMessage，同样给handle方法处理
        """
        request = ClientCloseMessage(client)
        self.handle(server, client, request)


class Node(object):
    """
    节点
    """
    def __init__(self, _config):
        """
        构造方法
        :param _config 配置
        """
        self.config = _config
        """
        node中的neighbors是动态的
        config中的neighbors是静态的
        """
        self.neighbors = self.config.neighbors
        self.server = Server(self.config.port)
        self.server.register_channel(LineChannel)
        self.server.register_channel(MessageChannel)
        self.server.register_handler(NodeHandler(self))
        self.state = Follower(self)
        self.leader = None
        if self.config.debug:
            # 每3秒显示下当前节点状态
            self.server.set_timer(self.config.show_state_rate, True, self._show_state)

    def _show_state(self, excepted_time, real_time):
        """
        定时显示当前节点的状态
        :param excepted_time:
        :param real_time:
        :return:
        """
        import random
        print '> current node:\t', self.node_key
        print '> current state:\t', self.state
        print '> leader is:\t', self.leader
        print '> neighbors are:\t', self.neighbors
        print '>>'
        print '> db sessions:\t', self.config.db.session
        print '>> ', random.randint(0, 100)

    def dispatch(self, server, client, message):
        """
        消息路由方法
        :param server:
        :param client:
        :param message:
        :return:
        """
        if isinstance(message, Message):
            if isinstance(message, InvalidMessage):
                return message
            else:
                return self.state.handle(client, message)
        else:
            return message

    @property
    def node_key(self):
        """
        node key属性
        :return:
        """
        return self.config.host, self.config.port

    def start(self):
        self.server.server_forever()
