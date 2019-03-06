# coding: utf8 
import os

CWD = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(CWD, '.run')

# 中间件地址
BROKER_URI_OF_GET_REQUEST = 'http://114.55.31.211:8002/vps/get_request'
BROKER_URI_OF_POST_RESPONSE = 'http://114.55.31.211:8002/vps/post_response'
BROKER_URI_OF_POST_STATUS = 'http://114.55.31.211:8002/vps/post_status'

# 拨号命令
DIAL_CMD = '/usr/bin/sh %s/bohao.sh' % CWD

# 运行日志存放路径
LOG_PATH = '%s/log/service.log' % CWD
