#!/usr/bin/python
# -*- coding:utf-8 -*-
import hashlib


class Handler(object):
    def handle(self, server, client, request):
        pass

    def close(self, server, client):
        """
        handler处理close
        :return:
        """
        pass


class DefaultHandler(Handler):
    def handle(self, server, client, request):
        if request == 'quit':
            self.server.stop()
        return request.upper() + '\n' + hashlib.md5(request.encode('utf-8')).hexdigest()+'\n'