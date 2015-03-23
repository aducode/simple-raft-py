#!/usr/bin/python
# -*- coding:utf-8 -*-


class Follower(object):
    """
    Follower State
    """
    def __init__(self, node):
        self._node = node


class Candidate(object):
    """
    Candidate  State
    """
    def __init__(self, node):
        self._node = node


class Leader(object):
    """
    Leader State
    """
    def __init__(self, node):
        self._node = node