#!/usr/bin/python
# -*- coding:utf -*-
__author__ = 'aducode@126.com'
import sys
from optparse import OptionParser
from config import Config
from node import Node

usage = '''
    Usage:
        python code.py host port [neighbor list] [-c config] [-v] [-s]
    '''


def init_parser():
    global usage
    _parser = OptionParser(usage)
    _parser.add_option('-l', '--list',
                       help='the cluster node list, default node.list',
                       action='store', type='string',
                       default='node.list',
                       dest='list_file')
    _parser.add_option('-v', '--verbose',
                       help='display more info',
                       action='store_true',
                       dest='verbose')
    _parser.add_option('-s', '--single',
                       help='start as sngle mode',
                       action='store_true',
                       dest='single')
    _parser.add_option('--db',
                       help='the db engine',
                       default='simple',
                       action='store',
                       type='string',
                       dest='db')
    _parser.add_option('--heartbeat_rate',
                       help='heartbeat rate, default 0.1',
                       default=0.1,
                       action='store',
                       type='float',
                       dest='heartbeat_rate')
    _parser.add_option('--heartbeat_timeout',
                       help='heartbeat timeout, default 2',
                       default=2,
                       action='store',
                       type='float',
                       dest='heartbeat_timeout')
    _parser.add_option('--elect_timeout',
                       help='elect timeout range like 1,2, default 0.15,0.3',
                       default='0.15,0.3',
                       action='store',
                       type='string',
                       dest='elect_timeout')
    _parser.add_option('--show_state_rate',
                       help='show state rate when -v effective, default 3',
                       default=3,
                       action='store',
                       type='float',
                       dest='show_state_rate')
    return _parser


def build_config(parser):
    options, args = parser.parse_args()
    if not args:
        try:
            parser.parse_args('-h')
        except TypeError:
            global usage
            print usage
        sys.exit(1)
    # prepare for host port
    host = args[0]
    port = int(args[1])
    # prepare for neighbors list
    neighbors = []
    if not options.single:
        if options.list_file is not None:
            with open(options.list_file) as _list:
                for line in _list:
                    if not line.startswith('#'):
                        host_port = line.split()
                        if len(host_port) >= 2:
                            neighbors.append((host_port[0], int(host_port[1]), ))

        else:
            neighbors_list = args[2:]
            if neighbors_list and len(neighbors_list) % 2 == 0:
                for i in xrange(0, len(neighbors_list), 2):
                    neighbors.append((neighbors_list[i], int(neighbors_list[i + 1])))
    # prepare for elect_timeout
    elect_timeout = tuple([float(x) for x in options.elect_timeout.split(',')])
    # prepare for db
    return Config(host, port,
                  neighbors=neighbors,
                  db=options.db,
                  heartbeat_rate=options.heartbeat_rate,
                  heartbeat_timeout=options.heartbeat_timeout,
                  elect_timeout=elect_timeout,
                  debug=options.verbose,
                  show_state_rate=options.show_state_rate)


if __name__ == '__main__':
    node = Node(build_config(init_parser())).start()
