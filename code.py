#!/usr/bin/python
# -*- coding:utf -*-
__author__ = 'aducode@126.com'
from optparse import OptionParser


def init_parser():
    usage = '''
    Usage:
        python code.py host port [neighbor list] [-c config] [-v]
    '''
    _parser = OptionParser(usage)
    _parser.add_option('-c', '--config', help='the config file', action='store', type='string', dest='config')
    _parser.add_option('-v', '--verbose', help='display more info', action='store_true', dest='verbose')
    _parser.add_option('--db', help='the db engine', action='store', type='string', dest='db')
    _parser.add_option('--heartbeat_rate', help='heartbeat rate', action='store', type='float', dest='heartbeat_rate')
    _parser.add_option('--heartbeat_timeout', help='heatbeat timeout', action='store', type='float', dest='heartbeat_timeout')
    _parser.add_option('--elect_timeout', help='elect timeout range', action='store', type='string', dest='elect_timeout')
    _parser.add_option('--show_state_rate', help='show state rate when -v effective', action='store', type='float', dest='show_state_rate')
    _parser.add_option('--test', help='test')
    return _parser


if __name__ == '__main__':
    parser = init_parser()
    options, args = parser.parse_args()
    print options
    # print options.port
    print args


