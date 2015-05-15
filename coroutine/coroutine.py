#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'aducode@126.com'


def coroutine(func):
    """
    yield实现的协程首次需要调用next
    :param func:
    :return:
    """
    def start(*args, **kwargs):
        g = func(*args, **kwargs)
        g.next()
        return g
    start.__doc__ = func.__doc__
    return start
