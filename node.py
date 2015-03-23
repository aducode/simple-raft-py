#!/usr/bin/python
# -*- coding:utf-8 -*-
import threading, time
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
        #default use the simple db engine
        self._db = db if db is not None else SimpleDB()
        #it can be 3 state:1 Follower 2 Candidate 3 Leader
        # default is follower state
        self._state = state_class(self)
        # the leader of those nodes
        # None means no leader be voted
        self._leader = None
        # node count
        self._node_count = len(self._nodes) if self._nodes else 0

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

    def heartbeat(self, msg='alive'):
        """
        boardcast heartbeat
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

    def run(self):
        server_thread = threading.Thread(target=self.server)
        server_thread.start()
        #Main Loop
        if self._leader is None:
            #need select a leader
            
            pass
        elif self._leader == self._addr:
            #this node is the leader
            while True:
                self.heartbeat()
        else:
            # this node is follower
            pass



