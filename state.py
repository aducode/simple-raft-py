#!/usr/bin/python
# -*- coding:utf-8 -*-
from protocol.message import NodeMessage, ElectMessage, HeartbeatMessage, ElectResponseMessage
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
        # self.voted = True
        # return '@elect 1\n'
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
        self.voted = False
        self.node.server.set_timer((0.15, 0.3), False, self._election_timeout)


    def _election_timeout(self, excepted_time, real_time):
        if not self.voted and not self.node.leader:
            print '[%.3f]election timeout ... turn to Candidate!' % real_time
            # 转变状态之前去掉选举超时
            # self.node.server.rm_timer(self._election_timeout)
            self.node.state = Candidate(self.node)

    def handle(self, message):
        assert isinstance(message, NodeMessage)
        if isinstance(message, ElectMessage):
            if not self.voted:
                self.voted = True
                return '@%s:%d@elect 1' % self.node.node_key
            else:
                return '@%s:%d@elect 0' % self.node.node_key
        elif isinstance(message, HeartbeatMessage):
            self.node.leader = message.leader
            self.node.server.rm_timer(self._election_timeout)
            # print 'Find leader %s so I must reset candidate timeout....' % (self.node.leader, )
            self.node.server.set_timer((0.15, 0.3), False, self._election_timeout)
            # print 'FIND leader:%s' % (self.node.leader, )


class Candidate(State):
    """
    Candidate  State
    """

    def __init__(self, node):
        super(Candidate, self).__init__(node)
        # voting = Ture 因为Candidate状态的node不会再参与选举
        self.node_count = (len(self.node.neighbors) if self.node.neighbors else 0) + 1
        self.elect_count = 1
        self.node_cache = {self.node.node_key: 1}
        self.node.server.set_timer((0.01, 0.1), True, self._elect)

    def handle(self, message):
        # #########################################
        # print 'Candidate handle:', message
        # #########################################
        assert isinstance(message, NodeMessage)
        if isinstance(message, ElectMessage):
            return '@%s:%d@elect 0' % self.node.node_key
        elif isinstance(message, HeartbeatMessage):
            self.node.leader = message.leader
            print 'FIND leader:%s' % (self.node.leader, )
            self.node.server.rm_timer(self._elect)
            self.node.state = Follower(self.node)
        elif isinstance(message, ElectResponseMessage):
            self.elect_count += message.value
            self.node_cache[message.node_key] = message.value
            # if len(self.node_cache) == self.node_count:
            #     # wait for next elect
            #     self.node_cache.clear()
            #     if self.elect_count > self.node_count/2:
            #         print '###############I\'m the leader'
            #     else:
            #         print 'elect fail wait for next elect'
            # return '@elect 0'

    def _elect(self, excepted_time, real_time):
        # count = 1 because it will elect itself
        # count = 1
        if self.node.neighbors:
            for follower_addr in self.node.neighbors:
                try:
                    sock, follower = self.node.server.connect(follower_addr)
                    # follower = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # follower.connect(follower_addr)
                    # 这里一定要加\n，否则LineChannel会一直缓存消息，不会交给MessageChannel处理
                    # follower.send('#%s:%d#elect\n' % self.node.node_key)
                    # if sock in self.node.server.context:
                    if follower_addr not in self.node_cache:
                        follower.input('#%s:%d#elect\n' % self.node.node_key, False)
                        self.node_cache[follower_addr] = -1
                    elif self.node_cache[follower_addr] != -1:
                        self.node.server.close(sock)
                    # 这里会出现死锁
                    # 由于node作为client端，发送消息时，使用的是阻塞socket，那么在recv时就会阻塞，导致timeout event handler阻塞
                    # 从而不能再main loop中进行下一轮IO handler
                    # client也使用多路IO复用，这里只管send，recv在handler里进行
                    # elected = int(follower.recv(1024))
                except IOError, e:
                    print e, 'Connect %s fail...' % (follower_addr,)
        print '===============================\nElect result:'
        for k, v in self.node_cache.items():
            print '\t', k, '\t', v
        print '==============================='
        elect_complite = True
        for value in self.node_cache.values():
            if value == -1:
                elect_complite = False
                break
        if len(self.node_cache) == self.node_count and elect_complite:
            self.node.server.rm_timer(self._elect)
            if self.elect_count > self.node_count / 2:
                print 'I\'m the leader:%s' % (self.node.node_key,)
                self.node.leader = self.node.node_key
                self.node.state = Leader(self.node)
            else:
                print 'Elect fail ,turn to follower'
                self.node.state = Follower(self.node)
                # finally:
                # if not follower:
                # follower.close()
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
                    sock, follower = self.node.server.connect(follower_addr)
                    #follower.send('#%s:%d#heartbeat\n' % self.node.node_key)
                    follower.input('#%s:%d#heartbeat\n' % self.node.node_key, False)
                except:
                    pass
        else:
            # 说明只有一个节点
            pass