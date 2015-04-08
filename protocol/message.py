#!/usr/bin/python
# -*- coding:utf-8 -*-


class Message(object):
    @staticmethod
    def parse(data, client):
        """
        解析原始字符串信息
        """
        if not data:
            return None
        elif data.startswith('get') and ';' not in data:
            # 客户端发来的get操作
            tokens = data.split()
            if len(tokens) == 2:
                return ClientMessage('get', tokens[1])
            else:
                return InvalidMessage()
        elif data.startswith('del'):
            auto_commit = False
            if data.endswith(';commit'):
                auto_commit = True
                data = data.split(';')[0]
            tokens = data.split()
            if len(tokens) == 2:
                return ClientMessage('delete', tokens[1], None, auto_commit)
            else:
                return InvalidMessage()
        elif data.startswith('set'):
            # 客户端发来的set操作
            auto_comit = False
            if data.endswith(';commit'):
                auto_comit = True
                data = data.split(';')[0]
            tokens = data.split()
            if len(tokens) == 3:
                return ClientMessage('set', tokens[1], tokens[2], auto_comit)
            else:
                return InvalidMessage()
        elif data == 'commit':
            # 客户端发来的提交
            return ClientMessage('commit')
        elif data == 'rollback':
            return ClientMessage('rollback')
        elif data.startswith('#'):
            # 来自其他节点的消息
            # node message格式
            # #ip:port#msgbody
            # node message需要提供消息来源
            # client.getpeername()也能获取消息来源，但是端口号并不是node监听的端口
            # 如果只是用ip作为node的标示，那么都在本地127.0.0.1上的node就会冲突
            # 所以node作为client连接过来的时候，需要加上来源 ip:port
            data = data[1:]  # 去掉最开始的#
            token = data.split('#')
            if not token or len(token) < 2:
                return InvalidMessage('Invalid Node Message Format')
            source = token[0]
            ip_port = source.split(':')
            if not ip_port or len(ip_port) != 2:
                return InvalidMessage('invalid source ip:port format:%s' % ip_port)
            ip = ip_port[0]
            if ip != client.getpeername()[0]:
                return InvalidMessage('IP %s in message source not eq IP  %s in socket' % (ip, client.getpeername()[0]))
            try:
                port = int(ip_port[1])
            except:
                return InvalidMessage('Invalid port:%s' % ip_port[1])
            node_key = (ip, port)
            data = token[1].strip()
            if data == 'elect':
                return ElectMessage(node_key)
            elif data.startswith('heartbeat'):
                return HeartbeatMessage(node_key)
            else:
                return InvalidMessage()
        else:
            # 暂时忽略其他节点发来的信息
            return InvalidMessage()


class ClientMessage(Message):
    """
    客户端发来的消息
    """

    def __init__(self, op, key=None, value=None, auto_commit=False):
        self.op = op
        self.key = key
        self.value = value
        self.auto_commit = auto_commit

    def __str__(self):
        return '[%s]%s:%s' % (self.op, self.key, self.value)


class NodeMessage(Message):
    pass


class ElectMessage(NodeMessage):
    def __init__(self, candidate):
        self.candidate = candidate


class HeartbeatMessage(NodeMessage):
    def __init__(self, leader):
        self.leader = leader


class InvalidMessage(Message):
    def __init__(self, msg='invalid message'):
        self.message = msg

    def __str__(self):
        return self.message