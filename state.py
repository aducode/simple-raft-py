#!/usr/bin/python
# -*- coding:utf-8 -*-
from protocol.message import Message, ClientMessage, ElectRequestMessage, HeartbeatRequestMessage, ElectResponseMessage, HeartbeatResponseMessage
import time


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
        elif isinstance(message, HeartbeatRequestMessage):
            return self.on_heartbeat_request(client, message)
        elif isinstance(message, HeartbeatResponseMessage):
            return self.on_heartbeat_response(client, message)
        elif isinstance(message, ElectRequestMessage):
            return self.on_elect_request(client, message)
        elif isinstance(message, ElectResponseMessage):
            return self.on_elect_response(client, message)
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
        return '@%s:%d@redirect' % self.node.leader if self.node.leader else 'No Leader Elected, please wait until we have a leader...'

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
        if not self.voted:
            self.voted = True
            return '@%s:%d@elect 1' % self.node.node_key
        else:
            if message.candidate not in self.node.neighbors:
                self.node.neighbors.append(message.candidate)
            return '@%s:%d@elect 0' % self.node.node_key

    def on_heartbeat_request(self, client, message):
        """
        Follower处理心跳请求消息
        """
        self.node.leader = message.leader
        self.node.server.rm_timer(self._election_timeout)
        self.node.neighbors = message.alives
        # 处理heartbeat带过来的extra msg
        extra_msg = message.message
        if extra_msg is not None:
            print extra_msg
        # print 'Now do not reset the timeout handler'
        self.node.server.set_timer(self.node.config.elect_timeout, False, self._election_timeout)
        # 响应
        return '@%s:%s@heartbeat 1' % self.node.node_key

    def _election_timeout(self, excepted_time, real_time):
        """
        Follower到Candidate状态超时时间，该方法改变node状态从Follower->Candidate
        """
        if self.node.leader:
            # 之前已经产生了leader，但是还超时了，说明leader挂了
            # 挂了的节点，需要摘除
            print self.node.leader
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
        return '@%s:%d@elect 0' % self.node.node_key

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
                        follower.input('#%s:%d#elect\n' % self.node.node_key, False)
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
        elect_complite = True
        for value in self.node_cache.values():
            if value == -1:
                elect_complite = False
                break
        if len(self.node_cache) == self.node_count and elect_complite:
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
        # TODO 改成从配置文件获取这些参数的值
        self.heartbeat_timeout = self.node.config.heartbeat_timeout  # 心跳超时2秒
        self.heartbeat_request_time = {}  # 由于发出心跳请求与接收心跳响应是异步的，需要一个dict记录请求与响应之间是否超时
        self.node.server.set_timer(self.node.config.heartbeat_rate, True, self._heartbeat)

    def on_elect_request(self, client, message):
        """
        ElectMessage，说明是新接入的节点，加入neighbors列表
        :param message:
        :return:
        """
        # 说明新接入了其他节点
        self.node.neighbors.append(message.candidate)
        return '@%s:%d@elect 0' % self.node.node_key

    def on_update(self, client, message):
        return self.node.config.db.handle(client, message.op, message.key, message.value, message.auto_commit)

    def on_heartbeat_response(self, client, message):
        """
        HeartbeatResponse， 心跳响应，根据响应的值做相应处理
        :param message:
        :return:
        """
        pass

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
                    sock, follower = self.node.server.connect(follower_addr)
                    follower.input('#%s:%d#heartbeat %s\n' % (self.node.node_key[0], self.node.node_key[1], self._get_alives_info(follower_addr), ), False)
                    # 记录心跳发请求发出的时间
                    self.heartbeat_request_time[follower_addr] = time.time()
                except Exception, e:
                    pass
        else:
            # 说明只有一个节点
            pass

    def _get_alives_info(self, source):
        """
        获取活动节点信息
        :param source: 请求来源
        :return:
        """
        ret = []
        for host, port in self.node.neighbors:
            if (host, port) != source:
                ret.append(str(host))
                ret.append(str(port))
        ret.append(str(self.node.node_key[0]))
        ret.append(str(self.node.node_key[1]))
        return ','.join(ret)