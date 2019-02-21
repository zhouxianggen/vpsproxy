#!/usr/bin/env python
#coding=utf8

try:
    from  setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

setup(
        name = 'vpsproxy',
        version = '1.0',
        install_requires = ['requests', 'tornado'], 
        description = 'vps 代理',
        url = 'https://github.com/zhouxianggen//vpsproxy', 
        author = 'zhouxianggen',
        author_email = 'zhouxianggen@gmail.com',
        classifiers = [ 'Programming Language :: Python :: 3.7',],
        packages = ['vpsproxy'],
        data_files = [ 
                ('/conf/supervisor/program/', ['vpsproxy.ini']),], 
        entry_points = { 'console_scripts': [
                'run_proxy_service = vpsproxy.proxy_service:main',
                'run_broker_service = vpsproxy.broker_service:main']}   
        )

