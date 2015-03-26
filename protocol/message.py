#!/usr/bin/python
# -*- coding:utf-8 -*-


class Message(object):
    @staticmethod
    def parse(data):
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
                auto_commit=True
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


class InvalidMessage(Message):
    def __init__(self, msg='invalid message'):
        self.message = msg

    def __str__(self):
        return self.message