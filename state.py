#!/usr/bin/python
# -*- coding:utf-8 -*-
import time, random

class State(object):
    def __init__(self, node):
        self._node = node


class Follower(State):
    """
    Follower State
    """

    def __init__(self, node):
        super(Follower, self).__init__(node)


class Candidate(State):
    """
    Candidate  State
    """

    def __init__(self, node):
        super(Candidate, self).__init__(node)



class Leader(State):
    """
    Leader State
    """

    def __init__(self, node):
        super(Leader, self).__init__(node)