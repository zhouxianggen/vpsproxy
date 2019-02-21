# coding: utf8 
import os
import socket


def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 53))
        n = s.getsockname()
        ip = n[0] if n else None
        s.close()
        return ip
    except Exception as e:
        return None


def read_file(path):
    return open(path).read().strip() if os.path.isfile(path) else ''


def get_vps_name():
    cwd = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(cwd, '.name')
    return read_file(path)


def get_deploy_version():
    cwd = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(cwd, '.version')
    content = read_file(path)
    return int(content) if content.isdigit() else 0


def is_network_availble():
    hosts = [
            'www.baidu.com', 
            'www.gov.cn']
    for host in hosts:
        try:
            socket.create_connection((host, 80))
            return True
        except Exception as e:
            continue
    return False

