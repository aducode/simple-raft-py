#!/usr/bin/python
# -*- coding:utf-8 -*-
import threading, time, random, datetime
from socket import socket, AF_INET, SOCK_STREAM

from db import SimpleDB
from state import Follower, Candidate, Leader


class Node(object):
    """
    The node
    """

    def __init__(self, nodes, db=None, addr=('127.0.0.1', 2333), state_class=Follower):
        """
        Constractor of this class
        :param other_nodes: Multi Nodes
        :param db: DB engine
        :param port: Node Server port
        :return:
        """
        self._addr = addr
        self._nodes = nodes
        if self._addr not in self._nodes:
            self._nodes.append(self._addr)
        # default use the simple db engine
        self._db = db if db is not None else SimpleDB()
        # it can be 3 state:1 Follower 2 Candidate 3 Leader
        # default is follower state
        self._state = state_class(self)
        # the leader of those nodes
        # None means no leader be voted
        self._leader = None
        # node count
        self._node_count = len(self._nodes) if self._nodes else 0
        self._next_time = 0

    def server(self):
        self.accepter = socket(AF_INET, SOCK_STREAM)
        self.accepter.bind(self._addr)
        self.accepter.listen(5)
        while True:
            client, addr = self.accepter.accept()
            print 'connected from ', addr
            data = client.recv(128)
            if data:
                print '[data]:', data
            client.close()


    def boardcast(self, msg):
        """
        boardcast msg
        :return:
        """
        if self._nodes:
            for other_node in self._nodes:
                if other_node != self._addr:
                    try:
                        client = socket(AF_INET, SOCK_STREAM)
                        client.connect(other_node)
                        client.send(msg)
                        client.close()
                    except Exception, e:
                        print e

    def heartbeat(self):
        self.boardcast('alive')

    def run(self):
        server_thread = threading.Thread(target=self.server)
        server_thread.start()
        # Main Loop
        while True:
            if self._leader is None:
                # need select a leader
                # change state to Candidate
                self._state = Candidate(self)
                # print 'Node[%s:%d] state:Candidate' % self._addr
                timeout = float(random.randint(150, 300)) / 1000
                # print 'timeout:%d' % timeout
                if not self._next_time:
                    self._next_time = time.time() + timeout
                if self._next_time > time.time():
                    continue
                print 'timeout %.3f' % time.time()
                self._next_time = 0
            elif self._leader == self._addr:
                # this node is the leader
                print 'Node[%s:%d] state:Leader' % self._addr
                self.heartbeat()
            else:
                # this node is follower
                print 'Node[%s:%d] state:Follower' % self._addr



