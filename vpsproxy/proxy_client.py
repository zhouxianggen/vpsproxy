# coding: utf8 
from pyobject import PyObject
import requests


class ProxyClient(PyObject):
    def __init__(self, proxy):
        self.proxy = proxy
        self.DEFAULT_HEADERS = {
                'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; WOW64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/71.0.3578.98 Safari/537.36'),
                'Keep-Alive': 'close'
                }


    def request(self, method, url, **kwargs):
        kwargs.setdefault('headers', self.DEFAULT_HEADERS)
        kwargs['headers']['target'] = url
        return requests.request(method, self.proxy, **kwargs)


    def get(self, url, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('get', url, params=params, **kwargs)


    def post(self, url, data=None, json=None, **kwargs):
        return self.request('post', url, data=data, json=json, **kwargs)

