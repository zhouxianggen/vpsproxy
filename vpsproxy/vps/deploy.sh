#!/bin/bash

WDIR="$HOME/vpp"

if [ ! -d $WDIR ];then
    echo "创建工作目录" 
    mkdir $WDIR
fi

cd $WDIR
echo "下载服务脚本" 

#wget 'https://github.com/zhouxianggen/vpsproxy/blob/master/vpsproxy/vps_service.py' -O vps_service.py
#wget 'https://github.com/zhouxianggen/vpsproxy/blob/master/vpsproxy/vps_config.py' -O vps_config.py
#wget 'https://github.com/zhouxianggen/vpsproxy/blob/master/vpsproxy/vps_utils.py' -O vps_utils.py
#wget 'https://github.com/zhouxianggen/vpsproxy/blob/master/vpsproxy/bohao.sh' -O bohao.sh
