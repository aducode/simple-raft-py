#!/usr/bin/python
# -*- coding:utf-8 -*-
from db import SimpleDB


class Config(object):
    """
    cluster的config信息
    """

    def __init__(self, host, port, neighbors=[], db=None):
        """
        构造方法
        :param host;        主机名
        :param port;        端口号
        :param neighobrs:   相邻节点
        :param db;          数据存储引擎
        :return:
        """
        self.host = host
        self.port = port
        self.neighbors = neighbors
        self.db = db if db else SimpleDB()