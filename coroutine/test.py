__author__ = 'Administrator'


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


if __name__ == '__main__':
    g = coroutine()
    print g.next()  # 第一次必须调用next
    print g.send("world")
    g.send('yooooo')


