#!/usr/bin/python
# -*- coding:utf-8 -*-
from protocol.message import NodeMessage, ElectMessage, HeartbeatMessage
import socket


class State(object):
    def __init__(self, node):
        self.node = node
        self.voted = False

    def handle(self, message):
        """
        处理其他node的消息
        """
        pass
        # assert isinstance(message, NodeMessage)
        # if isinstance(message, ElectMessage) and not self.voted:
        #     self.voted = True
        #     return '@elect 1\n'
        # elif isinstance(message, HeartbeatMessage):
        #     self.node.leader = HeartbeatMessage.leader
        #     return '@elect 1\n'
        # return '@elect 0\n'


class Follower(State):
    """
    Follower State
    """

    def __init__(self, node):
        super(Follower, self).__init__(node)
        self.node.server.set_timer((0.15, 0.3), False, self._election_timeout)


    def _election_timeout(self, excepted_time, real_time):
        #print 'election timeout...'
        self.node.state = Candidate(self.node)

    def handle(self, message):
        assert isinstance(message, NodeMessage)
        if isinstance(message, ElectMessage) and not self.voted:
            self.voted = True
            return '@elect 1\n'
        elif isinstance(message, HeartbeatMessage):
            self.node.leader = HeartbeatMessage.leader
            return '@elect 1\n'
        return '@elect 0\n'


class Candidate(State):
    """
    Candidate  State
    """

    def __init__(self, node):
        super(Candidate, self).__init__(node)
        # voting = Ture 因为Candidate状态的node不会再参与选举
        self.node_count = (len(self.node.neighbors) if self.node.neighbors else 0) + 1
        self.elect_count = 0
        self.voted = True
        self.node.server.set_timer((0.01, 0.1), False, self._elect)

    def handle(self, message):
        assert isinstance(message, NodeMessage)
        if isinstance(message, ElectMessage) and not self.voted:
            self.voted = True
            return '@elect 1\n'
        elif isinstance(message, HeartbeatMessage):
            self.node.leader = HeartbeatMessage.leader
            return '@elect 1\n'
        return '@elect 0\n'

    def _elect(self, excepted_time, real_time):
        # count = 1 because it will elect itself
        # count = 1
        if self.node.neighbors:
            for follower_addr in self.node.neighbors:
                elected = 0
                try:
                    follower = self.node.server.connect(follower_addr)
                    # follower = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # follower.connect(follower_addr)
                    # 这里一定要加\n，否则LineChannel会一直缓存消息，不会交给MessageChannel处理
                    # follower.send('#%s:%d#elect\n' % self.node.node_key)
                    follower.input('#%s:%d#elect\n' % self.node.node_key, False)
                    # 这里会出现死锁
                    # 由于node作为client端，发送消息时，使用的是阻塞socket，那么在recv时就会阻塞，导致timeout event handler阻塞
                    # 从而不能再main loop中进行下一轮IO handler
                    # client也使用多路IO复用，这里只管send，recv在handler里进行
                    # elected = int(follower.recv(1024))
                except IOError, e:
                    #print e, 'Connect %s fail...' % (follower_addr,)
                    pass
                # finally:
                #     if not follower:
                #         follower.close()
                # count += elected
        # if count >= self.node_count / 2 + 1:
        #     print 'elect success! turn to leader!'
        #     self.node.state = Leader(self.node)
        # else:
        #     print 'elect failed! turn to follower wait next elect'
        #     self.node.state = Follower(self.node)


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