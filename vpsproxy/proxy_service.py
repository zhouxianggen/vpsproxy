# coding: utf8 
""" vps代理服务
"""
import time
import json
import zlib
import hashlib
import argparse
import asyncio
from threading import Thread
from queue import Queue, Empty, Full
import tornado.ioloop
import tornado.web
import requests
from pyobject import PyObject
from pyutil import get_ip


class Context(PyObject):
    def __init__(self):
        PyObject.__init__(self)
        self.ip = get_ip()
        self.port = 0
        self.BROKER_HOST = ''
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
                return self.slots[idx]
        return None


class PostRequestWorker(PyObject, Thread):
    def __init__(self):
        PyObject.__init__(self)
        Thread.__init__(self)
        self.daemon = True
        self.queue = Queue()
        self.MAX_QUEUE_SIZE = 200

    def run(self):
        self.log.info('start')
        while True:
            try:
                req = self.queue.get()
                self.log.info('post request to broker')
                requests.post(g_ctx.BROKER_HOST, data=req)
            except Empty:
                time.sleep(0.001)

    def add_request(self, req):
        self.log.info('add request')
        if self.queue.qsize() >= self.MAX_QUEUE_SIZE:
            self.log.warning('queue is busy')
            return False
        self.queue.put(req)
        return True


""" global data """
g_ctx = Context()
g_sender = PostRequestWorker()
g_sender.start()


class ProxyRequestHandler(PyObject, tornado.web.RequestHandler):
    """ 处理代理请求
    将受到的代理请求放入slots：slots[(url, fut, deadline)]
    """
    def __init__(self, *args, **kwargs):
        PyObject.__init__(self)
        tornado.web.RequestHandler.__init__(self, *args, **kwargs)


    async def get(self, url):
        self.log.info('receive request [{}]'.format(url))
        idx = g_ctx.get_free_slot()
        if idx < 0:
            self.log.warning('no free slot')
            return self.set_status(503, "no free slot")

        req = {'url':url, 'headers':dict(self.request.headers), 
                'data':self.request.body.decode('utf8')}
        id = hashlib.md5(json.dumps(req).encode('utf8')).hexdigest()
        req['context'] = {'url': url, 'id': id, 
                'caller': 'http://{}:{}'.format(g_ctx.ip, g_ctx.port)}
        if not g_sender.add_request(json.dumps(req)):
            self.log.warning('service busy')
            return self.set_status(503, "service busy")

        timeout = float(self.request.headers.get('timeout', 5))
        deadline = time.time() + timeout
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        #await fut
        g_ctx.slots[idx] = (id, fut, deadline)
        done, pending = await asyncio.wait({fut}, timeout=timeout)
        if pending:
            self.log.warning('timeout')
            return self.set_status(500, "timeout")
        status_code, headers, content = fut.result()
        self.set_status(status_code)
        for k,v in headers.items():
            self.set_header(k, v)
        self.write(content)

    def post(self, url):
        self.log.info('receive result of [{}]'.format(url))
        try:
            d = json.loads(self.request.body)
            _id = d['context']['id']
            status_code = d['status_code']
            headers = d['headers']
            content = d['content']
        except Exception as e:
            self.log.exception(e)
        
        slot = g_ctx.find_slot(_id)
        if slot:
            self.log.info('set future result')
            slot[1].set_result((status_code, headers, content))


class ProxyService(tornado.web.Application):
    def __init__(self):
        handlers = [
                (r"(.*)", ProxyRequestHandler)
        ]   
        settings = dict(
            debug=True,
        )   
        tornado.web.Application.__init__(self, handlers, **settings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="specify port", 
            default=8081, type=int)
    parser.add_argument("-b", "--broker", help="specify broker url", 
            default='http://localhost:8082/caller/post_request')
    args = parser.parse_args()
    g_ctx.BROKER_HOST = args.broker
    g_ctx.port = args.port
    service = tornado.httpserver.HTTPServer(ProxyService())
    service.listen(args.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

