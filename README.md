vpsproxy
![](https://img.shields.io/badge/python%20-%203.7-brightgreen.svg)
========
> 爬虫 vps 代理 

### 代理请求路径
> request <--> proxy_service <--> broker_service <--> vps_service

### proxy_service (代理服务)
+ 接收到请求后，将请求提交给中间服务
+ 收到中间服务返回的结果后，将结果返回给调用方

> 一般运行多个proxy_service，保证可用性

### broker_service (中间服务)
+ 接收代理服务发来的请求，存放到队列
+ 接收vps服务的请求后，将队列中的请求返回给vps服务
+ 接收到vps服务返回的结果后，将结果提交给代理服务

> 一般运行多个broker_service，通过负载均衡提供统一访问地址

### vps_service (vps服务)
+ 从中间服务获取请求
+ 打开请求后，将结果提交给中间服务

> 在vps机器上运行，间隔一段时间拨号，间隔一定时间重启，支持热更新。

## `Install`
` pip install git+https://github.com/zhouxianggen/vpsproxy.git`

## `Upgrade`
` pip install --upgrade git+https://github.com/zhouxianggen/vpsproxy.git`

## `Uninstall`
` pip uninstall vpsproxy`

## `Run`
+ 部署vps服务
```
```

+ 部署proxy_service，broker_service
```
supervisorctl -c supervisord.conf restart vpsproxy:
```

## `Example`
```
from pyrequests import PyRequests

requests = PyRequests()
proxies = {
        'http': 'http://vpsproxy',
        'https': 'http://vpsproxy'}
url = 'http://www.baidu.com'
r = requests.get(url=url, proxies=proxies)
print(r.status_code)

```
