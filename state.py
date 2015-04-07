#!/usr/bin/python
# -*- coding:utf-8 -*-
from protocol.message import NodeMessage, VoteMessage


class State(object):
    def __init__(self, node):
        self.node = node

    def handle(self, message):
        """
        处理其他node的消息
        """
        pass


class Follower(State):
    """
    Follower State
    """

    def __init__(self, node):
        super(Follower, self).__init__(node)
        self.node.server.set_timer((0.15, 0.3), True, self._election_timeout)
        self.voting = False

    def handle(self, message):
        assert isinstance(message, NodeMessage)
        if isinstance(message, VoteMessage) and not self.voting:
            self.voting = True
            return 1
        else:
            return 0


    def _election_timeout(self, excepted_time, real_time):
        print 'excepted time:%.3f\nreal_time:%.3f\n' % (excepted_time, real_time)
        self.node.server.rm_timer(self._election_timeout)
        self.node.state = Candidate(self.node)


class Candidate(State):
    """
    Candidate  State
    """

    def __init__(self, node):
        super(Candidate, self).__init__(node)

    def _request_vote(self):
        pass


class Leader(State):
    """
    Leader State
    """

    def __init__(self, node):
        super(Leader, self).__init__(node)