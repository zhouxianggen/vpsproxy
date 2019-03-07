vpsproxy
![](https://img.shields.io/badge/python%20-%203.7-brightgreen.svg)
========
> vps 代理 

### 代理请求路径
> caller <--> proxy_service  <--> vps_service

### proxy_service (代理服务)
+ 接收到caller的请求后，将请求放到分布式队列
+ 接收到vps服务的请求后，将队列中的请求返回给vps服务
+ 接收到vps服务返回的结果后，将结果POST给caller

> 一般运行多个proxy_service，保证可用性

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
```
supervisorctl -c supervisord.conf restart vpsproxy:
```

## `Example`
```
from proxy_client import ProxyClient

client = ProxyClient('http://localhost:8081')
r = client.get(url=url, headers={'timeout': '3'})
print(r.status_code)

```
