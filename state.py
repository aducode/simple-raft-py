#!/usr/bin/python
# -*- coding:utf-8 -*-
from protocol.message import \
    Message, ClientMessage, ClientCloseMessage, \
    ElectRequestMessage, HeartbeatRequestMessage, \
    ElectResponseMessage, HeartbeatResponseMessage, \
    SyncRequestMessage, SyncResponseMessage
import time
import sys


class State(object):
    """
    节点状态类
    不同状态有不同的表现
    """

    def __init__(self, node):
        self.node = node

    def handle(self, client, message):
        """
        处理其他node的消息
        """
        assert isinstance(message, Message)
        if isinstance(message, ClientMessage):
            if message.op == 'get':
                return self.on_get(client, message)
            else:
                return self.on_update(client, message)
        elif isinstance(message, ClientCloseMessage):
            return self.on_client_close(client, message)
        elif isinstance(message, HeartbeatRequestMessage):
            return self.on_heartbeat_request(client, message)
        elif isinstance(message, HeartbeatResponseMessage):
            return self.on_heartbeat_response(client, message)
        elif isinstance(message, ElectRequestMessage):
            return self.on_elect_request(client, message)
        elif isinstance(message, ElectResponseMessage):
            return self.on_elect_response(client, message)
        elif isinstance(message, SyncRequestMessage):
            return self.on_sync_request(client, message)
        elif isinstance(message, SyncResponseMessage):
            return self.on_sync_response(client, message)
        else:
            pass

    def on_get(self, client, message):
        """
        处理客户端get请求
        """
        return self.node.config.db.handle(client, message.op, message.key, message.value, message.auto_commit)

    def on_update(self, client, message):
        """
        处理客户端除了get外的请求
        """
        return '@%s:%d@redirect' % self.node.leader if self.node.leader \
            else 'No Leader Elected, please wait until we have a leader...'

    def on_client_close(self, client, message):
        """
        处理客户端关闭
        """
        return self.node.config.db.release(message.client)

    def on_heartbeat_request(self, client, message):
        """
        接收到heartbeat请求的处理方法
        """
        pass

    def on_heartbeat_response(self, client, message):
        """
        接收到heartbeata响应的处理方法
        """
        pass

    def on_elect_request(self, client, message):
        """
        接收到选举请求的处理方法
        """
        pass

    def on_elect_response(self, client, message):
        """
        接收到选举响应的处理方法
        """
        pass

    def on_sync_request(self, client, message):
        """
        接收到同步请求
        """
        pass

    def on_sync_response(self, client, message):
        """
        接收同步响应
        """
        pass

    def __str__(self):
        return self.__class__.__name__.strip().upper()


class Follower(State):
    """
    Follower State
    """

    def __init__(self, node):
        super(Follower, self).__init__(node)
        self.voted = False
        self.node.server.set_timer(self.node.config.elect_timeout, False, self._election_timeout)

    def on_elect_request(self, client, message):
        """
        Follower处理选举请求消息
        """
        if self.node.leader:
            return ElectResponseMessage(self.node.node_key, 0).serialize()
        if not self.voted:
            self.voted = True
            return ElectResponseMessage(self.node.node_key, 1).serialize()
        else:
            if message.candidate not in self.node.neighbors:
                self.node.neighbors.append(message.candidate)
            return ElectResponseMessage(self.node.node_key, 0).serialize()

    def on_heartbeat_request(self, client, message):
        """
        Follower处理心跳请求消息
        """
        self.node.leader = message.leader
        self.node.server.rm_timer(self._election_timeout)
        self.node.neighbors = message.alives
        if self.node.config.db.commit_pos < message.commit_pos:
            # 说明数据没有同步1.删除elect timeout 2.转换状态
            self.node.state = Syncing(self.node)
            return
        # 处理heartbeat带过来的extra msg
        extra_msg = message.message
        ret = 1
        if extra_msg is not None:
            for msg in extra_msg:
                if isinstance(msg, ClientMessage):
                    if msg.op == 'release' and True == self.node.config.db.handle(client, msg.op, msg.key, msg.value, msg.auto_commit):
                        ret = -1
                        break
                    if 'fail' == self.node.config.db.handle(client, msg.op, msg.key, msg.value, msg.auto_commit):
                        ret = 0
                        break
        # print 'Now do not reset the timeout handler'
        self.node.server.set_timer(self.node.config.elect_timeout, False, self._election_timeout)
        # 响应
        return HeartbeatResponseMessage(self.node.node_key, ret, message.vector).serialize()

    def _election_timeout(self, excepted_time, real_time):
        """
        Follower到Candidate状态超时时间，该方法改变node状态从Follower->Candidate
        """
        if self.node.leader:
            # 之前已经产生了leader，但是还超时了，说明leader挂了
            # 挂了的节点，需要摘除
            if self.node.leader in self.node.neighbors:
                self.node.neighbors.remove(self.node.leader)
            # 但是要考虑重连回复neighbors列表，所以这个列表是动态的
            self.node.leader = None
            self.voted = False

        if not self.voted and not self.node.leader:
            # print '[%.3f]election timeout ... turn to Candidate!' % real_time
            # 转变状态之前去掉选举超时
            # self.node.server.rm_timer(self._election_timeout)
            self.node.state = Candidate(self.node)


class Candidate(State):
    """
    Candidate  State
    """

    def __init__(self, node):
        super(Candidate, self).__init__(node)
        self.node_count = (len(self.node.neighbors) if self.node.neighbors else 0) + 1
        self.elect_count = 1
        self.node_cache = {}
        self.node.server.set_timer(self.node.config.start_elect_timeout, True, self._elect_other_node)

    def on_elect_request(self, client, message):
        """
        其他Follower的Elect，返回value: 0
        :param message:
        :return:
        """
        return ElectResponseMessage(self.node.node_key, 0).serialize()

    def on_heartbeat_request(self, client, message):
        """
        如果接收到其他node的heartbeat则放弃candidate， 转为follower状态
        :param message:
        :return:
        """
        self.node.leader = message.leader
        print 'FIND leader:%s' % (self.node.leader, )
        self.node.neighbors = message.alives
        self.node.server.rm_timer(self._elect_other_node)
        self.node.state = Follower(self.node)

    def on_elect_response(self, client, message):
        """
        其他Follower的ElectResponse，如果value：1 ，则票数+1
        :param message:
        :return:
        """
        self.elect_count += message.value
        self.node_cache[message.follower] = message.value

    def _elect_other_node(self, excepted_time, real_time):
        """
        选举其他的节点的超时处理方法
        """
        # count = 1 because it will elect itself
        # count = 1
        if self.node.neighbors:
            for follower_addr in self.node.neighbors:
                try:
                    sock, follower = self.node.server.connect(follower_addr)
                    # follower = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # follower.connect(follower_addr)
                    # 这里一定要加\n，否则LineChannel会一直缓存消息，不会交给MessageChannel处理
                    # follower.send('#%s:%d#elect\n' % self.node.node_key)
                    # if sock in self.node.server.context:
                    if follower_addr not in self.node_cache:
                        follower.input(ElectRequestMessage(self.node.node_key).serialize(True), False)
                        self.node_cache[follower_addr] = -1
                    elif self.node_cache[follower_addr] != -1:
                        self.node.server.close(sock)
                except IOError, e:
                    print e, 'Connect %s fail...' % (follower_addr,)
            # 向全部neighbors node发出elect request之后，也向自己发出elect request
            # 这里就用timeout event代替了
            # 选择自己
            if self.node_cache.get(self.node.node_key, -1) == -1:
                self.node.server.set_timer((0.01, 0.2), False, self._elect_itself)
        else:
            # 单节点，直接选举自己
            self.node_cache[self.node.node_key] = 1
        # print '===============================\nElect result:'
        # for k, v in self.node_cache.items():
        #     print '\t', k, '\t', v
        # print '==============================='
        elect_complete = True
        for value in self.node_cache.values():
            if value == -1:
                elect_complete = False
                break
        if len(self.node_cache) == self.node_count and elect_complete:
            self.node.server.rm_timer(self._elect_other_node)
            if self.elect_count > self.node_count / 2:
                print 'I\'m the leader:%s' % (self.node.node_key,)
                self.node.leader = self.node.node_key
                self.node.state = Leader(self.node)
            else:
                print 'Elect fail ,turn to follower'
                self.node.state = Follower(self.node)

    def _elect_itself(self, excepted_time, real_time):
        """
        选举自己
        """
        self.node_cache[self.node.node_key] = 1


class Leader(State):
    """
    Leader State
    """

    def __init__(self, node):
        super(Leader, self).__init__(node)
        # 时间向量
        self.current_vector = 0
        self.heartbeat_timeout = self.node.config.heartbeat_timeout  # 心跳超时2秒
        self.heartbeat_request_time = {}  # 由于发出心跳请求与接收心跳响应是异步的，需要一个dict记录请求与响应之间是否超时
        # 记录心跳响应结果
        self.heartbeat_result = {}
        self.node.server.set_timer(self.node.config.heartbeat_rate, True, self._heartbeat)
        # 记录连接的client
        self.clients = {}

    def on_elect_request(self, client, message):
        """
        ElectMessage，说明是新接入的节点，加入neighbors列表
        :param message:
        :return:
        """
        # 说明新接入了其他节点
        if message.candidate not in self.node.neighbors:
            self.node.neighbors.append(message.candidate)
        return ElectResponseMessage(self.node.node_key, 0).serialize()

    def on_update(self, client, message):
        # print 'recv client message:', client
        if not self.node.neighbors:
            # 单个节点
            return self.node.config.db.handle(client, message.op, message.key, message.value, message.auto_commit)
        else:
            # 集群模式
            if client not in self.clients:
                self.clients[client] = []
            self.clients[client].append(message)
        # return self.node.config.db.handle(client, message.op, message.key, message.value, message.auto_commit)

    def on_client_close(self, client, message):
        # 目前无法区分client是来自其他node还是真的client
        if not self.node.neighbors:
            # 单个节点
            return self.node.config.db.release(message.client)
        else:
            # 集群
            if self.node.config.db.release(message.client):
                # 说明是client断开
                if client not in self.clients:
                    self.clients[client] = []
                self.clients[client].append(ClientMessage('release'))
                # self.clients[client] = [ClientMessage('rollback')]
            return True

    def on_heartbeat_response(self, client, message):
        """
        HeartbeatResponse， 心跳响应，根据响应的值做相应处理
        :param message:
        :return:
        """
        if message.value == -1:
            # 说明是释放资源的返回
            self.clients = dict()
            self.heartbeat_result = dict()
            return
        if message.follower not in self.heartbeat_result:
            self.heartbeat_result[message.follower] = message.value
        succeed_response = 0
        if len(self.node.neighbors) == len(self.heartbeat_result):
            # 说明收到了全部的响应
            for v in self.heartbeat_result.values():
                if v == 1:
                    succeed_response += 1
            if succeed_response >= len(self.heartbeat_result)/2:
                for client in self.clients:
                    client_message = self.clients[client][-1]
                    self.node.server.get_channel(client).input(self.node.config.db.handle(client, client_message.op, client_message.key, client_message.value, client_message.auto_commit) + '\n', False)
            else:
                for client in self.clients:
                    self.node.server.get_channel(client).input('operate fail in cluster\n', False)
            self.clients = dict()
            self.heartbeat_result = dict()

    def on_sync_request(self, client, message):
        commit_log_pos = message.value
        if commit_log_pos < self.node.config.db.commit_pos:
            return SyncResponseMessage(self.node.node_key, self.node.config.db.log[
                commit_log_pos:commit_log_pos + self.node.config.sync_count]).serialize()
        else:
            return SyncResponseMessage(self.node.node_key, complete=True).serialize()

    def _heartbeat(self, excepted_time, real_time):
        """
        心跳函数，同时判断是否有节点挂掉
        :param excepted_time:
        :param real_time:
        :return:
        """
        if self.node.neighbors:
            for follower_addr in self.node.neighbors:
                # 判断上次heartbeat之后是否收到请求
                if follower_addr in self.heartbeat_request_time and (
                        real_time - self.heartbeat_request_time[follower_addr]) >= self.heartbeat_timeout:
                    # 已经超时了，不再发心跳，并且从neighbors中移除
                    self.node.neighbors.remove(follower_addr)
                    del self.heartbeat_request_time[follower_addr]
                    print 'node:', follower_addr, ' heartbeat timeout ...'
                    continue
                try:
                    client_messages = []
                    for client in self.clients:
                        client_messages.append(self.clients[client][-1])
                    sock, follower = self.node.server.connect(follower_addr)
                    follower.input(HeartbeatRequestMessage(self.node.node_key,
                                                           [n for n in self.node.neighbors if n != follower_addr],
                                                           message=client_messages, vector=self.current_vector,
                                                           commit_pos=self.node.config.db.commit_pos).serialize(True),
                                   False)
                    # 记录心跳发请求发出的时间
                    self.heartbeat_request_time[follower_addr] = time.time()
                except Exception, e:
                    print e
            # vector自增
            self.current_vector += 1
            if self.current_vector == sys.maxint:
                self.current_vector = 0
        else:
            # 说明只有一个节点
            pass


class Syncing(State):
    """
    同步状态，专门同步数据
    """
    def __init__(self, node):
        super(Syncing, self).__init__(node)
        # 3秒后同步一次
        self.node.server.set_timer(self.node.config.sync_rate, False, self._sync)

    def on_get(self, client, message):
        """
        同步状态的节点不响应受任何client请求
        :param client:
        :param message:
        :return:
        """
        return '@%s:%d@redirect' % self.node.leader if self.node.leader \
            else 'No Leader Elected, please wait until we have a leader...'

    def on_sync_response(self, client, message):
        if message.logs and not message.complete:
            self.node.config.db.sync(message.logs)
            self.node.server.set_timer(self.node.config.sync_rate, False, self._sync)
        elif message.complete:
            self.node.state = Follower(self.node)

    def _sync(self, excepted_time, real_time):
        """
        定时同步函数
        :return:
        """
        if self.node.leader:
            _, leader = self.node.server.connect(self.node.leader)
            leader.input(SyncRequestMessage(self.node.node_key, self.node.config.db.commit_pos).serialize(True), False)