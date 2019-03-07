# coding: utf8 
from pyobject import PyObject
import requests


class ProxyClient(PyObject):
    def __init__(self, proxy):
        self.proxy = proxy


    def request(self, method, url, **kwargs):
        kwargs.get('headers', {}).update({'target': url})
        return requests.request(method, self.proxy, **kwargs)


    def get(self, url, params=None, **kwargs):
        kwargs.setdefault('allow_redirects', True)
        return self.request('get', url, params=params, **kwargs)


    def post(self, url, data=None, json=None, **kwargs):
        return self.request('post', url, data=data, json=json, **kwargs)

