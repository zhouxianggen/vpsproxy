# coding: utf8
#import requests
from pyrequests import PyRequests


requests = PyRequests()
proxies = {
        'http': 'http://127.0.0.1:8001',
        'https': 'http://192.168.9.226:8001'
    }

url = 'http://114.55.31.211:8502/control_panel/watch_status'
r = requests.get(url=url, headers={'User-Agent': 'xman', 'timeout': '4'}, proxies=proxies)
print(r.status_code)
print(r.content)
