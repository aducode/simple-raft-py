#!/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'Administrator'
import types

def coroutine():
    # 调用next后，next返回hello
    # 然后这阻塞到 n = yield
    # 然后调用send("world")后得到n的值print n
    n = yield "hello"
    print n
    # 然后send返回"fuck" 阻塞到m=yield
    # send("yooo")后，得到m，并且print m
    m = yield "fuck"
    print m
    # 然后应该执行到yield xxx 但是没有yield 抛出StopIteration异常


def home(title, name):
    head_gen = head(title)
    body_gen = body(name)
    msg = yield '<html>%s%s</html>' % (head_gen.next(), body_gen.next())
    # print 'home msg:', msg
    # ret1 = head_gen.send(msg)
    # ret2 = body_gen.send(msg)
    # yield ' '.join(['success', ret1, ret2])
    while True:
        if isinstance(msg, types.TupleType) and len(msg) == 2:
            msg = yield '<html>%s%s</html>' % (head_gen.send(msg[0]), body_gen.send(msg[1]))
        else:
            msg = yield '<html>%s%s</html>' % (head_gen.next(), body_gen.next())


def head(title):
    msg = title
    msg = yield '<head><title>%s</title></head>' % msg
    # print 'head msg:', msg
    # yield 'head success'
    while True:
        if not msg:
            msg = title
        msg = yield '<head><title>%s</title></head>' % msg


def body(name):
    msg = name
    msg = yield '<body><h1>%s</h1></body>' % msg
    # print 'body msg:', msg
    # yield 'body success'
    while True:
        if not msg:
            msg = name
        msg = yield '<body><h1>%s</h1></body>' % msg


if __name__ == '__main__':
    # g = coroutine()
    # print g.next()  # 第一次必须调用next
    # print g.send("world")
    # g.send('yooooo')
    home_gen =  home('hello world', 'Issac')
    print home_gen.next()
    print home_gen.send(('hehehehe', 'Alion'))
    print home_gen.next()
    print home_gen.send(('fuck', 'FUCKFUCKFUCK'))



