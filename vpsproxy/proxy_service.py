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


class PostRequestWorker(PyObject, Thread):
    def __init__(self):
        PyObject.__init__(self)
        Thread.__init__(self)
        self.queue = Queue()
        self.MAX_QUEUE_SIZE = 200

    def run(self):
        self.log.info('start')
        while True:
            try:
                req = self.queue.get()
                self.log.info('post request to broker')
                requests.post(g_broker_url, data=req)
            except Empty:
                time.sleep(0.001)

    def add_request(self, req):
        if self.queue.qsize() >= self.MAX_QUEUE_SIZE:
            self.log.waring('queue is busy')
            return False
        self.queue.put(req)
        return True


""" global data """
g_sender = PostRequestWorker()
g_sender.start()


class ProxyRequestHandler(PyObject, tornado.web.RequestHandler):
    """ 处理代理请求
    将受到的代理请求放入slots：slots[(url, fut, deadline)]
    """
    def __init__(self, *args, **kwargs):
        PyObject.__init__(self)
        tornado.web.RequestHandler.__init__(self, *args, **kwargs)
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

    async def get(self, url):
        self.log.info('receive request [{}]'.format(url))
        idx = self.get_free_slot()
        if idx < 0:
            return self.set_status(503, "no free slot")

        req = {'url':url, 'headers':dict(self.request.headers), 
                'data':self.request.body.decode('utf8')}
        id = hashlib.md5(json.dumps(req).encode('utf8')).hexdigest()
        req['context'] = {'id': id, 'caller': get_ip()}
        if not g_sender.add_request(json.dumps(req)):
            return self.set_status(503, "service busy")

        timeout = float(self.request.headers.get('timeout', 5))
        deadline = time.time() + timeout
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self.slots[idx] = (id, fut, deadline)
        await fut
        status_code, headers, content = fut.result()
        self.set_status(status_code)
        for k,v in headers.items():
            self.set_header(k, v)
        self.write(content)

    def post(self, url):
        self.log.info('receive result of [{}]'.format(url))
        try:
            d = json.loads(self.request.body)
            id = d['context']['id']
            status_code = d['status_code']
            headers = d['headers']
            content = d['content']
        except Exception as e:
            self.log.exception(e)

        for i in range(self.MAX_SLOTS_SIZE):
            idx = (self.last + i) % self.MAX_SLOTS_SIZE
            if self.slots[idx][0] == id:
                self.log.info('set future result')
                self.slots[idx][1].set_result((status_code, headers, content))
                break


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
            default=8001, type=int)
    parser.add_argument("-b", "--broker", help="specify broker url", 
            default='http://localhost:8002/caller/post_request')
    args = parser.parse_args()
    global g_broker_url
    g_broker_url = args.broker
    service = tornado.httpserver.HTTPServer(ProxyService())
    service.listen(args.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()

