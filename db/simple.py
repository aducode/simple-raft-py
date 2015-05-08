# !/usr/bin/python
# -*- coding:utf-8 -*-
__author__ = 'Administrator'


class DB(object):
    """
    Simple Memeory DB
    """

    def __init__(self):
        """
        构造方法
        :return:
        """
        self.data = {}
        self.session = {}
        # 提交日志
        self.log = []

    @property
    def commit_pos(self):
        return len(self.log)

    def handle(self, session_id, op, key, value, auto_commit):
        """
        处理client请求
        :param session_id:  本次请求的session
        :param op:          请求具体操作
        :param key:         请求的key
        :param value:       请求的value
        :param auto_commit: 是否自动提交
        :return:
        """
        if session_id not in self.session:
            self.session[session_id] = {'local': {}, 'logs': []}
        try:
            return getattr(self, op)(session_id, key, value, auto_commit)
        except Exception, e:
            print e
            return 'fail'

    def release(self, session_id, key=None, value=None, auto_commit=False):
        """
        释放session相关资源
        :param session_id:
        :return Boolean:
        """
        if session_id in self.session:
            del self.session[session_id]
            return True
        return False

    def get(self, session_id, key, value=None, auto_commit=False):
        """
        get请求
        :param session_id:
        :param key:
        :param value:
        :param auto_commit:
        :return:
        """
        local = self.session[session_id]['local']
        if key not in local:
            return self.data.get(key, '%s' % value)
        else:
            return '%s' % local[key]

    def set(self, session_id, key, value, auto_commit):
        """
        set请求
        :param session_id:
        :param key:
        :param value:
        :param auto_commit:
        :return:
        """
        if auto_commit:
            # self.commit_set(key, value)
            self.data[key] = value
        else:
            logs = self.session[session_id]['logs']
            local = self.session[session_id]['local']
            logs.append('%s:%s:%s' % ('set', key, value))
            local[key] = value
        return 'success'

    def delete(self, session_id, key, value=None, auto_commit=False):
        """
        删除请求
        :param session_id:
        :param key:
        :param value:
        :param auto_commit:
        :return:
        """
        if auto_commit:
            if key in self.data:
                del self.data[key]
        else:
            logs = self.session[session_id]['logs']
            local = self.session[session_id]['local']
            logs.append('%s:%s:%s' % ('delete', key, value))
            local[key] = None
        return 'success'

    def commit_set(self, key, value):
        """
        提交修改
        :param key:
        :param value:
        :return:
        """
        self.data[key] = value

    def commit_delete(self, key, value=None):
        """
        提交删除
        :param key:
        :param value:
        :return:
        """
        if key in self.data:
            del self.data[key]

    def commit(self, session_id, key=None, value=None, auto_commit=False):
        """
        提交操作
        :param session_id:
        :param key:
        :param value:
        :param auto_commit:
        :return:
        """
        logs = self.session[session_id]['logs']
        if logs:
            for log in logs:
                tokens = log.split(':')
                getattr(self, 'commit_' + tokens[0])(tokens[1], tokens[2])
                self.log.append(log)
            if session_id in self.session:
                del self.session[session_id]
        return 'success'

    def rollback(self, session_id, key=None, value=None, auto_commit=False):
        """
        回滚操作
        :param session_id:
        :param key:
        :param value:
        :param auto_commit:
        :return:
        """
        if session_id in self.session:
            del self.session[session_id]
        return 'success'