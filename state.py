#!/usr/bin/python
# -*- coding:utf-8 -*-
from protocol.message import NodeMessage, ElectMessage, HeartbeatMessage
import socket


class State(object):
    def __init__(self, node):
        self.node = node
        self.voting = False

    def handle(self, message):
        """
        处理其他node的消息
        """
        assert isinstance(message, NodeMessage)
        if isinstance(message, ElectMessage) and not self.voting:
            self.voting = True
            return 1
        elif isinstance(message, HeartbeatMessage):
            self.node.leader = HeartbeatMessage.leader
            return 1
        return 0


class Follower(State):
    """
    Follower State
    """

    def __init__(self, node):
        super(Follower, self).__init__(node)
        self.node.server.set_timer((0.15, 0.3), False, self._election_timeout)


    def _election_timeout(self, excepted_time, real_time):
        # print 'excepted time:%.3f\nreal_time:%.3f\n' % (excepted_time, real_time)
        # self.node.server.rm_timer(self._election_timeout)
        self.node.state = Candidate(self.node)


class Candidate(State):
    """
    Candidate  State
    """

    def __init__(self, node):
        super(Candidate, self).__init__(node)
        # voting = Ture 因为Candidate状态的node不会再参与选举
        self.voting = True
        self.node.server.set_timer(0.01, False, self._elect)

    def _elect(self, excepted_time, real_time):
        # count = 1 because it will elect itself
        count = 1
        node_count = (len(self.node.neighbors) if self.node.neighbors else 0) + 1
        if self.node.neighbors:
            for follower_addr in self.node.neighbors:
                elected = 0
                try:
                    follower = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    follower.connect(follower_addr)
                    follower.send('#elect')
                    elected = int(follower.recv(1024))
                    follower.close()
                except:
                    pass
                count += elected
        if count >= node_count / 2 + 1:
            self.node.state = Leader(self.node)
        else:
            self.node.state = Follower(self.node)
        # else:
        #     self.node.state = Follower(self.node)
        # self.node.server.rm_timer(self._elect)


class Leader(State):
    """
    Leader State
    """
    def __init__(self, node):
        super(Leader, self).__init__(node)
        self.buffer = []
        self.alive = []
        self.node.server.set_timer(0.15, True, self._heartbeat)

    def _heartbeat(self, excepted_time, real_time):
        # print '%.3f\n%.3f\n' % (excepted_time, real_time)
        del self.alive[:]
        if self.node.neighbors:
            for follower_addr in self.node.neighbors:
                try:
                    follower = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    follower.connect(follower_addr)
                    follower.send('#heartbeat')
                    if int(follower.recv(1024)) == 1:
                        self.alive.append(follower_addr)
                    follower.close()
                except:
                    pass
        else:
            # 说明只有一个节点
            pass