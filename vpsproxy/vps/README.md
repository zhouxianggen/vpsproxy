vps
========
> VPS 机器 

### 部署流程
1. 下载deploy脚本
```
wget 'https://raw.githubusercontent.com/zhouxianggen/vpsproxy/master/vpsproxy/vps/deploy.sh'
sh deploy.sh
```

2. 对拨号机命名
```
cd vpp
echo 'name' > .name
```

3. 设置crontab
```
*/1 * * * * cd /root/vpp && python vps_dog.py >dog.log 2>&1
*/1 * * * * cd /root/vpp && python vps_service.py >service.log 2>&1
```

4. 拨号配置
```
参考VPS提供商的文档
```

5. 配置VPS自动重启
```
```

6. 配置环境变量
```
```
