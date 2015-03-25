#!/usr/bin/python
# -*- coding:utf-8 -*-


class SimpleDB(object):
    """
    Simple Memeory DB
    """

    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, None)