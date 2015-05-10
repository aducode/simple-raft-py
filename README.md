# simple-raft-py
这是一个简单的python实现的raft协议，只是为了学习raft而写的代码。
关于raft的资料可以参考：
http://thesecretlivesofdata.com/raft/

目前进度：

1. 完成基本的网络通讯框架，使用python select做多路IO复用
2. 可以处理定时器事件
3. 单节点可以进行一些基本的操作(get  set  del  commit)
4. cluster内节点选举
5. Leader挂掉，其余节点从新选举出leader
6. 单个客户端连接Leader节点进行update操作时实现Leader Follower之间数据同步
7. client关闭后，node内进行资源释放
8. leader关闭后，释放follower资源
目标：
* 多个客户端连接Leader节点，Leader Follower之间数据同步
* 新增节点时同步数据（全量同步、增量同步）
