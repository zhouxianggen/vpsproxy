# coding: utf8 
""" vps代理服务
"""
import time
import json
import zlib
import hashlib
import asyncio
import argparse
import socket
import configparser
from threading import Thread
from queue import Queue, Empty, Full
import tornado.ioloop
import tornado.web
import requests
from pyobject import PyObject
from pyredis import PyRedis
from pyutil import get_ip


class Context(PyObject):
    def init(self, config):
        PyObject.__init__(self)
        cfg = configparser.ConfigParser()
        cfg.read(config)
        host = cfg.get('redis', 'host') 
        port = cfg.getint('redis', 'port') 
        pswd = cfg.get('redis', 'pswd') 
        self.request_cache = PyRedis(host=host, port=port, 
                pswd=pswd, db=4, version='broker-')
        self.vps_status_cache = PyRedis(host=host, port=port, 
                pswd=pswd, db=5, version='vps-')
        self.vps_ip_pool = PyRedis(host=host, port=port, 
                pswd=pswd, db=5, version='ips-')

        self.ip = get_ip()
        self.port = cfg.getint('service', 'port')
        self.host = 'http://{}:{}'.format(self.ip, self.port)

        self.MAX_SLOTS_SIZE = 500
        self.slots = [None for i in range(self.MAX_SLOTS_SIZE)]
        self.last = 0

    
    def get_free_slot(self):
        now = time.time()
        for i in range(self.MAX_SLOTS_SIZE):
            idx = (self.last + i) % self.MAX_SLOTS_SIZE
            if not self.slots[idx] or self.slots[idx][-1] < now:
                self.last = idx
                return idx
        return -1


    def find_slot(self, _id):
        for i in range(self.MAX_SLOTS_SIZE):
            idx = (self.last + i) % self.MAX_SLOTS_SIZE
            if self.slots[idx] and self.slots[idx][0] == _id:
                return idx
        return None


class Broker(Thread, PyObject):
    """ 请求中间件：缓存请求，转发结果
    """
    def __init__(self):
        Thread.__init__(self)
        PyObject.__init__(self)
        self.REQUEST_QUEUE = 'BROKER_REQUEST_QUEUE'
        self.MAX_REQ_QUEUE_SIZE = 500
        self.response_queue = Queue()
        self.MAX_RESP_QUEUE_SIZE = 500
        self.daemon = True


    def push_request(self, request):
        self.log.info('push request')
        n = g_ctx.request_cache.llen(self.REQUEST_QUEUE)
        if n > self.MAX_REQ_QUEUE_SIZE:
            self.log.info('request queue is busy')
            return False
        g_ctx.request_cache.lpush(self.REQUEST_QUEUE, request)
        return True


    def get_request(self):
        return g_ctx.request_cache.rpop(self.REQUEST_QUEUE)


    def push_response(self, response):
        if self.response_queue.qsize() > self.MAX_RESP_QUEUE_SIZE:
            self.log.warning('response queue is busy')
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
g_ctx = Context()
g_broker = Broker()
g_broker.start()


class BaseRequestHandler(PyObject, tornado.web.RequestHandler):
    def __init__(self, *args, **kwargs):
        PyObject.__init__(self)
        tornado.web.RequestHandler.__init__(self, *args, **kwargs)

    def echo(self, status, reason='', data=''):
        if status != 200:
            self.log.warning('set status [{}][{}]'.format(status, reason))
        self.set_status(status)
        self.write(data or '')


class ProxyRequestHandler(BaseRequestHandler):
    """ 处理代理请求
    """
    async def get(self, url):
        self.request.headers.pop('Host', '')
        self.request.headers.pop('host', '')

        url = self.request.headers.pop('target', url)
        self.log.info('receive GET request [{}]'.format(url))
        idx = g_ctx.get_free_slot()
        self.log.info('get slot [{}]'.format(idx))
        if idx < 0:
            return self.echo(500, reason='no free slot')

        req = {'url':url, 'headers':dict(self.request.headers), 
                'data':self.request.body.decode('utf8')}
        _id = hashlib.md5(json.dumps(req).encode('utf8')).hexdigest()
        req['context'] = {'url': url, 'id': _id, 'caller': g_ctx.host} 
        if not g_broker.push_request(json.dumps(req)):
            return self.echo(500, reason='broker is busy')

        timeout = float(self.request.headers.get('timeout', 5))
        deadline = time.time() + timeout
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        g_ctx.slots[idx] = (_id, fut, deadline)

        done, pending = await asyncio.wait({fut}, timeout=timeout)
        if pending:
            return self.echo(500, reason='timeout')
        status_code, headers, content = fut.result()
        self.set_status(status_code)
        self.write(content)


    def post(self, url):
        url = self.request.headers.pop('target', url)
        self.log.info('receive POST request [{}]'.format(url))
        try:
            d = json.loads(self.request.body)
            _id = d['context']['id']
            self.log.info('receive result of [{}]'.format(d['context']['url']))
            status_code = d['status_code']
            headers = d['headers']
            content = d['content']
        except Exception as e:
            self.log.exception(e)
        
        idx = g_ctx.find_slot(_id)
        if idx is None:
            self.log.warning('can not find slot idx of [{}]'.format(_id))
            return
        self.log.info('set future result of [{}]'.format(idx))
        try:
            g_ctx.slots[idx][1].set_result((status_code, headers, content))
        except asyncio.base_futures.InvalidStateError as e:
            self.log.exception(e)
            pass
        g_ctx.slots[idx] = None


class VpsGetRequestHandler(BaseRequestHandler):
    """ 处理vps获取request的请求
    vps收到request后，打开其中的url，然后将结果post回来
    """
    def get(self):
        self.log.info('vps GET from [{}]'.format(self.request.remote_ip))
        self.echo(200, data=g_broker.get_request())


class VpsPostResponseHandler(BaseRequestHandler):
    """ 处理vps上传的结果
    为了不阻塞主线程，这里只把结果提交给broker（线程），由后者post给请求方
    """
    def post(self):
        self.log.info('vps POST from [{}]'.format(self.request.remote_ip))
        g_broker.push_response(self.request.body)
        self.echo(200)


class VpsPostStatusHandler(BaseRequestHandler):
    """ 处理vps汇报的状态
    """
    def update(self, vps, status):
        g_ctx.vps_status_cache.delete(vps)
        for k,v in status.items():
            g_ctx.vps_status_cache.hset(vps, k, v)
        g_ctx.vps_status_cache.hset(vps, 'update_time', time.time())
        ip = status.get('ip', '')
        if ip:
            g_ctx.vps_ip_pool.hincrby(vps, ip)


    def post(self):
        try:
            d = json.loads(self.request.body)
            vps = d['vps']
            self.log.info('get status of [{}]'.format(vps))
            self.echo(200)
        except Exception as e:
            self.log.exception(e)    
            self.echo(500, reason=str(e))


class ProxyService(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"/vps_get_request", VpsGetRequestHandler),
                (r"/vps_post_response", VpsPostResponseHandler),
                (r"/vps_post_status", VpsPostStatusHandler),
                (r"(.*)", ProxyRequestHandler)
        ]   
        settings = dict(
            debug=True,
        )   
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="specify config file")
    args = parser.parse_args()
    g_ctx.init(args.config)
    service = tornado.httpserver.HTTPServer(ProxyService())
    service.listen(g_ctx.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

