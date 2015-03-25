#!/usr/bin/python
# -*- coding:utf-8 -*-
import socket
import threading
import sys
import random
import time

error_no = 0

def connect2server(i):
    global error_no
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(('127.0.0.1', 2333))
        client.send('[%d]' % i)
        client.send("fuck")
        client.send("you!!!")
        client.send("%d\n" % random.randint(1000, 10000))
        print '[%s]recv:%s' % (i, client.recv(1024))
        client.close()
    except:
        (ErrorType, ErrorValue, ErrorTB) = sys.exc_info()
        (errno, err_msg) = ErrorValue
        error_no += 1
        print "Connect server failed: %s, errno=%d" % (err_msg, errno)

if __name__ == '__main__':
    if len(sys.argv)<=1:
        print 'Usage:num of threads'
        sys.exit(1)

    # 压力测试
    error_no = 0
    total_thread = int(sys.argv[1])
    threads=[]
    start = time.time()
    for i in xrange(total_thread):
        t = threading.Thread(target=connect2server, args=(i,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    end = time.time()
    print 'cast %.3f seconds\nerror times:%d\nTPS:%f\nfail percent:%%%f' % (end-start, error_no, total_thread/(end-start), float(error_no)/total_thread*100)

