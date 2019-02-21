# coding: utf8 
""" vps代理的中间服务器，完成下列工作：
1. 将调用方发过来的请求放入请求队列
2. 分发请求队列中的请求给vps机群（被动）
3. 获取vps机群的请求结果（被动），然后将请求结果转发给调用方
4. 获取vps机群的状态信息（被动），提供状态监控界面
"""
import time
import json
import argparse
import asyncio
from datetime import datetime
from threading import Thread
from queue import Queue, Empty, Full
import requests
import tornado.ioloop
import tornado.web
from pyobject import PyObject
from pyresource import REDIS_CRAWLER as REDIS 
from pyredis import PyRedis


class RequestBroker(Thread, PyObject):
    """ 请求中间件：缓存请求，转发结果
    """
    def __init__(self):
        Thread.__init__(self)
        PyObject.__init__(self)
        self.daemon = True
        self.cache = PyRedis(host=REDIS.host, port=REDIS.port, 
                pswd=REDIS.pswd, db=5, version='broker-')
        self.REQUEST_QUEUE = 'BROKER_REQUEST_QUEUE'
        self.MAX_REQ_QUEUE_SIZE = 500
        self.response_queue = Queue()
        self.MAX_RESP_QUEUE_SIZE = 100

    def push_request(self, request):
        self.cache.lpush(self.REQUEST_QUEUE, request)
        if self.cache.llen(self.REQUEST_QUEUE) > self.MAX_REQ_QUEUE_SIZE:
            self.log.warning('request queue is busy')
            self.cache.rpop(self.REQUEST_QUEUE)

    def get_request(self):
        return self.cache.rpop(self.REQUEST_QUEUE)

    def push_response(self, response):
        if self.response_queue.qsize() > self.MAX_RESP_QUEUE_SIZE:
            self.log.warning('response queue if busy')
            return
        self.response_queue.put(response)

    def run(self):
        self.log.info('start')
        while True:
            try:
                response = self.response_queue.get()
                d = json.loads(response)
                caller = d['context']['caller']
                self.log.info('post response to [{}]'.format(caller))
                requests.post(caller, data=response)
            except Empty:
                time.sleep(0.001)


""" global data """
g_broker = RequestBroker()
g_broker.start()


class BaseRequestHandler(PyObject, tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        PyObject.__init__(self)
        tornado.web.RequestHandler.__init__(self, *args, **kwargs)

    def echo(self, status, data=None):
        self.set_status(status)
        self.write(data or '')


class CallerPostRequestHandler(BaseRequestHandler):
    """ 处理调用方发送过来的请求
    """
    def post(self):
        req = json.loads(self.request.body)
        self.log.info('request from [{}]'.format(req['context']))
        g_broker.push_request(json.dumps(req))
        self.echo(200)


class VpsGetRequestHandler(BaseRequestHandler):
    """ 处理vps获取request的请求
    vps收到request后，打开其中的url，然后将结果post回来
    """
    def get(self):
        self.log.info('ip=[{}]'.format(self.request.remote_ip))
        self.echo(200, g_broker.get_request())


class VpsPostResponseHandler(BaseRequestHandler):
    """ 处理vps上传的结果
    为了不阻塞主线程，这里只把结果提交给broker（线程），由后者post给请求方
    """
    def post(self):
        self.log.info('ip=[{}]'.format(self.request.remote_ip))
        g_broker.push_response(self.request.body)
        self.echo(200)


class VpsPostStatusHandler(BaseRequestHandler):
    """ 处理vps汇报的状态
    """
    def __init__(self, *args, **kwargs):
        BaseRequestHandler.__init__(self, *args, **kwargs)
        self.vps_status_cache = PyRedis(host=REDIS.host, port=REDIS.port, 
                pswd=REDIS.pswd, db=5, version='vps-')
        self.vps_ip_pool = PyRedis(host=REDIS.host, port=REDIS.port, 
                pswd=REDIS.pswd, db=5, version='ips-')


    def update(self, vps, status):
        self.vps_status_cache.delete(vps)
        for k,v in status.items():
            self.vps_status_cache.hset(vps, k, v)
        self.vps_status_cache.hset(vps, 'update_time', time.time())
        ip = status.get('ip', '')
        if ip:
            self.vps_ip_pool.hincrby(vps, ip)


    def post(self):
        try:
            d = json.loads(self.request.body)
            vps = d['vps']
            self.log.info('get status of [{}]'.format(vps))
            self.echo(200)
        except Exception as e:
            self.log.exception(e)    
            self.echo(500)


class AdminSuperviseHandler(BaseRequestHandler):
    """ 提供服务状态监控页面
    """
    def get(self):
        self.write('foo')


class BrokerService(tornado.web.Application):
    def __init__(self):
        handlers = [ 
            (r"/caller/post_request", CallerPostRequestHandler),
            (r"/vps/get_request", VpsGetRequestHandler),
            (r"/vps/post_response", VpsPostResponseHandler),
            (r"/vps/post_status", VpsPostStatusHandler),
            (r"/admin/supervise", AdminSuperviseHandler),
        ]   
        settings = dict(
            debug=True,
        )   
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="specify port", default=8002,
            type=int)
    args = parser.parse_args()
    service = tornado.httpserver.HTTPServer(BrokerService())
    service.listen(args.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

