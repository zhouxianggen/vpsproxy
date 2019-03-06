#!/bin/bash

GITHOME='https://raw.githubusercontent.com/zhouxianggen/vpsproxy/master/vpsproxy'
WDIR="$HOME/vpp"

if [ ! -d $WDIR ];then
    echo "创建工作目录" 
    mkdir $WDIR
fi

cd $WDIR
echo "下载服务脚本" 
wget "${GITHOME}/vps/vps_dog.py" -O vps_dog.py
wget "${GITHOME}/vps/vps_service.py" -O vps_service.py
wget "${GITHOME}/vps/vps_utils.py" -O vps_utils.py
wget "${GITHOME}/vps/vps_config.py" -O vps_config.py
wget "${GITHOME}/vps/bohao.sh" -O bohao.sh
wget "${GITHOME}/vps/.version" -O .version

echo "部署成功"
