#!/usr/bin/python
# -*- coding:utf-8 -*-
import hashlib

class Handler(object):
    def __init__(self, server, client):
        self.server = server
        self.client = client

    def handle(self, request):
        pass


class DefaultHandler(Handler):
    def __init__(self, server, client):
        super(DefaultHandler, self).__init__(server, client)

    def handle(self, request):
        # print 'handle the request\n%s' % (request)
        if request == 'quit':
            self.server.stop()
        return request.upper() + '\n' + hashlib.md5(request.encode('utf-8')).hexdigest()+'\n'