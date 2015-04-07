#!/usr/bin/python
# -*- coding:utf-8 -*-


class SimpleDB(object):
    """
    Simple Memeory DB
    """

    def __init__(self):
        self.data = {}
        self.session = {}
        # self.commit_pos = 0

    def handle(self, session_id, op, key, value, auto_commit):
        if session_id not in self.session:
            self.session[session_id] = {'local': {}, 'logs': []}
        try:
            return getattr(self, op)(session_id, key, value, auto_commit)
        except Exception, e:
            print e
            return 'fail'

    def get(self, session_id, key, value=None, auto_commit=False):
        local = self.session[session_id]['local']
        if key not in local:
            return self.data.get(key, '%s' % value)
        else:
            return '%s' % local[key]

    def set(self, session_id, key, value, auto_commit):
        if auto_commit:
            #self.commit_set(key, value)
            self.data[key] = value
        else:
            logs = self.session[session_id]['logs']
            local = self.session[session_id]['local']
            logs.append('%s:%s:%s' % ('set', key, value))
            local[key] = value
        return 'success'

    def delete(self, session_id, key, value=None, auto_commit=False):
        if auto_commit:
            if key in self.data:
                del self.data[key]
        else:
            logs = self.session[session_id]['logs']
            local = self.session[session_id]['local']
            logs.append('%s:%s:%s' % ('delete', key, value))
            local[key]=None
        return 'success'

    def commit_set(self, key, value):
        self.data[key] = value

    def commit_delete(self, key, value=None):
        if key in self.data:
            del self.data[key]

    def commit(self, session_id, key=None, value=None, auto_commit=False):
        logs = self.session[session_id]['logs']
        if logs:
            for log in logs:
                tokens = log.split(':')
                getattr(self, 'commit_' + tokens[0])(tokens[1], tokens[2])
            if session_id in self.session:
                del self.session[session_id]
        return 'success'

    def rollback(self, session_id, key=None, value=None, auto_commit=False):
        if session_id in self.session:
            del self.session[session_id]
        return 'success'