# coding: utf8
#import requests
import requests
#from pyrequests import PyRequests
#requests = PyRequests()
import time


proxies = {
        'http': 'http://114.55.31.211:8001',
        'https': 'http://114.55.31.211:8001'
    }
url = 'http://114.55.31.211:8502/control_panel/watch_status'
start = time.time()
r = requests.get(url=url, headers={'User-Agent': 'xman', 'timeout': '2'}, proxies=proxies)
print(r.status_code, r.reason)
print('took: ', time.time()-start)
