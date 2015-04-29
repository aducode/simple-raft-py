#!/usr/bin/python
# -*- coding:utf-8 -*-
from server import Server, Handler
from server import Channel, LineChannel
from state import Follower, Leader
from protocol.message import Message, ClientMessage, NodeMessage
from config import Config


class MessageChannel(Channel):
    """
    node消息Channel
    """
    def __init__(self, server, client, next):
        """
        构造方法
        :param server 服务端
        :param client 客户端
        :param next   channle链的下一个
        :return
        """
        super(MessageChannel, self).__init__(server, client, next)

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
        print '> current node:\t', self.node_key
        print '> current state:\t', self.state
        print '> leader is:\t', self.leader
        print '> neighbors are:\t', self.neighbors
        print '>>'

    def dispatch(self, server, client, message):
        """
        消息路由方法
        :param server:
        :param client:
        :param message:
        :return:
        """
        if isinstance(message, ClientMessage):
            if message.op == 'get' or isinstance(self.state, Leader):
                return self.config.db.handle(client, message.op, message.key, message.value, message.auto_commit)
            else:
                #set del commit 操作需要重定位到leader操作
                return '@%s:%d@redirect' % self.leader if self.leader else 'No Leader Elected, please wait until we have a leader...'
        elif isinstance(message, NodeMessage):
            return self.state.handle(message)
        else:
            return message

    @property
    def node_key(self):
        """
        node key属性
        :return:
        """
        # 这里不能用getsockname 会返回0.0.0.0
        # return self.server.accepter.getsockname()
        return self.config.host, self.config.port

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
    except Exception, e:
        pass
    try:
        port = int(sys.argv[2])
    except Exception, e:
        pass
    try:
        nei = sys.argv[3:]
        if nei and len(nei) % 2 == 0:
            neighbors = []
            for i in xrange(0, len(nei), 2):
                neighbors.append((nei[i], int(nei[i+1])))
    except:
        sys.exit(1)
    # node = Node(Config(host, port, neighbors=neighbors, debug=True, heartbeat_timeout=1, heartbeat_response_timeout=10, elect_timeout=(1.5, 3), start_elect_timeout=(0.1, 0.5)))
    node = Node(Config(host, port, neighbors=neighbors, debug=True))
    node.start()
