# coding: utf8 
import os

CWD = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.join(CWD, '.run')

# 中间件地址
BROKER_HOST = 'http://114.55.31.211:8081'
BROKER_URI_OF_GET_REQUEST = '{}/vps_get_request'.format(BROKER_HOST)
BROKER_URI_OF_POST_RESPONSE = '{}/vps_post_response'.format(BROKER_HOST)
BROKER_URI_OF_POST_STATUS = '{}/vps_post_status'.format(BROKER_HOST)

# 拨号命令
DIAL_CMD = '/usr/bin/sh %s/bohao.sh' % CWD

# 运行日志存放路径
LOG_PATH = '%s/log/service.log' % CWD
if LOG_PATH:
    _d = os.path.dirname(LOG_PATH)
    if not os.path.isdir(_d):
        os.makedirs(_d)

# 远端版本
REMOTE_VERSION = 'https://raw.githubusercontent.com/zhouxianggen/vpsproxy/master/vpsproxy/vps/.version'
DEPLOY_SCRIPT = 'https://raw.githubusercontent.com/zhouxianggen/vpsproxy/master/vpsproxy/vps/deploy.sh'

