# coding: utf8
import sys
import time
from threading import Thread
import requests
from pyutil import get_logger
from proxy_client import ProxyClient


log = get_logger()
#client = ProxyClient('http://114.55.31.211:8081')

#url = 'http://114.55.31.211:8502/control_panel/watch_status'
url = 'https://h5api.m.taobao.com/h5/mtop.taobao.detail.getdetail/6.0/?jsv=2.4.8&t=1551742011879&api=mtop.taobao.detail.getdetail&v=6.0&dataType=jsonp&ttid=2017%40taobao_h5_6.6.0&AntiCreep=true&type=jsonp&callback=mtopjsonp2&data=%7B%22itemNumId%22%3A%22576026346249%22%7D'


def foo():
    log.info('start')
    client = ProxyClient('http://114.55.31.211:8081')
    start = time.time()
    r = client.get(url=url, headers={'User-Agent': 'xman', 'timeout': '3'})
    log.info('[{}][{}][{}]'.format(r.status_code, r.reason, time.time()-start))
    open('content', 'wb').write(r.content)

foo()
sys.exit()

pool = []
for i in range(1):
    pool.append(Thread(target=foo))

for t in pool:
    t.daemon = True
    t.start()
for t in pool:
    t.join()

log.info('wait..')
