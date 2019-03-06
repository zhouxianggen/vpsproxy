# coding=utf-8
""" 判断是由有版本更新 
"""
import requests
import vps_config
import vps_utils


class LogObject(object):
    def __init__(self, log_path=None, log_level=logging.INFO):
        self.log = logging.getLogger(self.__class__.__name__)
        if not self.log.handlers:
            if log_path:
                handler = RotatingFileHandler(log_path, 
                        maxBytes=1024*1024*500, backupCount=10)
            else:
                handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                    '[%(name)-12s %(threadName)-10s %(levelname)-8s '
                    '%(asctime)s] %(message)s'))
            self.log.addHandler(handler)
        self.log.setLevel(log_level)


class Worker(LogObject, Thread):
    def __init__(self, context=None, check_context_status=True, 
            run_interval=0):
        LogObject.__init__(self, log_path=vps_config.LOG_PATH)
        Thread.__init__(self)
        self.daemon = True
        self._exit = Event()
        self.context = context
        self.check_context_status = check_context_status
        self.run_interval = run_interval
        self.deadline = 0
        self.start()


    def run(self):
        while not self._exit.is_set():
            try:
                if self.context and self.check_context_status:
                    if self.context.get_status() != 'STATUS_OK':
                        time.sleep(0.1)
                        continue
                self._run()
                if self.run_interval:
                    time.sleep(self.run_interval)
            except requests.exceptions.RequestException as e:
                self.log.error('request failed [{}]'.format(e.request.url))
            except Exception as e:
                self.log.exception(e)
            self.deadline = 0


    def _run(self):
        pass


    def exit(self):
        self._exit.set()


class GetRequestWorker(Worker):
    def _run(self):
        if self.context.request_queue.qsize() > len(
                self.context.request_workers):
            self.log.info('request queue is busy')
            return
        if self.context.response_queue.qsize() > len(
                self.context.post_response_workers):
            self.log.info('response queue is busy')
            return
        
        r = requests.get(vps_config.BROKER_URI_OF_GET_REQUEST, timeout=2)
        if r.status_code == 200 and r.content:
            self.log.info('put request to queue')
            self.context.request_queue.put(r.content)
            self.run_interval = 0
            return

        # increase interval when idle 
        self.run_interval = max(1, self.run_interval + 0.1)


class RequestWorker(Worker):
    def _run(self):
        req = json.loads(self.context.request_queue.get())
        context = req['context']
        method = req.get('method', 'GET').upper()
        url = req['url']
        headers = req['headers']
        data = req.get('data', '')
        if not url:
            return

        timeout = float(headers.get('timeout', 5))
        self.deadline = time.time() + timeout
        self.log.info('open url [{}:{}]'.format(method, url))
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            r = requests.post(url, headers=headers, data=data, timeout=timeout)
        self.context.response_queue.put((context, url, r))


class PostResponseWorker(Worker):
    def _run(self):
        context, url, res = self.context.response_queue.get()
        self.log.info('upload result of [{}]'.format(url))
        self.deadline = time.time() + 10 
        #content = zlib.compress(res.content).decode('utf8')
        data = {'context': context, 'url': url, 'status_code': res.status_code, 
                'headers': dict(res.headers), 'content': res.text}
        requests.post(vps_config.BROKER_URI_OF_POST_RESPONSE, 
                data=json.dumps(data), timeout=10)


class PostStatusWorker(Worker):
    def _run(self):
        self.log.info('post status to broker')
        data = {'vps': vps_utils.get_vps_name(),  
                'version': self.context.version, 
                'status':self.context.get_status(), 
                'ip': vps_utils.get_ip(), 
                'request_queue_size': self.context.request_queue.qsize(), 
                'response_queue_size': self.context.response_queue.qsize()}
        requests.post(vps_config.BROKER_URI_OF_POST_STATUS, 
                data=json.dumps(data), timeout=2)


class DialWorker(Worker):
    def _run(self):
        self.context.bohao()


def main():
    r = requests.get(vps_config.REMOTE_VERSION)
    if r.status_code != 200:
        print('get remote version failed')

    v = float(r.content)
               

if __name__ == '__main__':
    main()

