# coding=utf-8
""" 判断是由有版本更新 
"""
from subprocess import Popen, PIPE
import requests
import vps_config
import vps_utils


def get(url):
    r = requests.get(url)
    if r.status_code != 200:
        print('打开链接[{}]失败'.format(url))
        return False
    return r.content


def main():
    print('获取远端版本')
    content = get(vps_config.REMOTE_VERSION)
    if not content:
        print('获取失败')
        return

    remote_version = float(content)
    local_version = vps_utils.get_deploy_version()
    print('远端版本[{}], 本地版本[{}]'.format(remote_version, 
            local_version))
    
    if remote_version > local_version:
        print('更新版本')
        print('下载部署脚本')
        content = get(vps_config.DEPLOY_SCRIPT)
        if not content:
            print('下载失败')
            return
        deploy_file = '%s/tmp.sh' % vps_config.CWD
        open(deploy_file, 'wb').write(content)
        cmd = "/usr/bin/sh %s" % deploy_file
        process = Popen(cmd, shell=True, stdout=PIPE)
        stdout, stderr = process.communicate()
        print('部署结果：')
        print(stdout)
    print('运行结束')


if __name__ == '__main__':
    main()

