# simple-raft-py
这是一个简单的python实现的raft协议，只是为了学习raft而写的代码。
关于raft的资料可以参考：
http://thesecretlivesofdata.com/raft/

目前进度：
* 完成基本的网络通讯框架，使用python select做多路IO复用
* 可以处理定时器事件
* 单节点可以进行一些基本的操作(get  set  del  commit)
* cluster内节点选举
* Leader挂掉，其余节点从新选举出leader

目标：
* leader follower之间数据同步
