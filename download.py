#!/usr/bin/env python3
# _._ coding: utf-8 _._

"""
该工具适用于本地与目标服务器连接不稳定的情况下下载文件

该工具通过一个单独的下载服务器来下载目标文件并回传至本地
这通常需要你有一个网络速度较快并且稳定的独立服务器

该工具支持密码与秘钥两种权限认证方式

@author Luna <luna@cyl-mail.com>
"""

import argparse
import paramiko
from paramiko import ssh_exception
from paramiko.sftp import SFTPError
import getpass
import logging
import os
import shutil
import random
import datetime
import progressbar
import sys
from urllib import parse


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def connect_ssh(host: str, port: int = 22, username: str = 'root', passwd: str = '', use_key: bool = False, key: str = ''):
    """
    连接远程服务器.

    :param host:
    :param port:
    :param username:
    :param passwd:
    :param use_key:
    :param key:
    :return:
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            if use_key is True:
                ssh.connect(hostname=host, port=port, username=username, key_filename=key)
            else:
                ssh.connect(hostname=host, port=port, username=username, password=passwd)
        except paramiko.AuthenticationException as exception:
            logger.error("身份验证失败：{0}".format(exception))

            return False
        except paramiko.SSHException as exception:
            logger.error("连接远程服务器失败：{0}".format(exception))

            return False
        except ssh_exception.NoValidConnectionsError as exception:
            logger.error("无法连接服务器：{0}".format(exception))

            return False

        return ssh
    except KeyboardInterrupt:
        logger.info('用户手动结束进程，程序退出')

        return False


def remote_download_file(ssh: paramiko.SSHClient, link: str, save_name: str) -> bool:
    """
    开始在远程服务器下载文件.

    :param ssh:
    :param link:
    :param save_name:
    :return:
    """
    try:
        logging.info("开始下载：{0}".format(link))
        try:
            stdin, stdout, stderr = ssh.exec_command("wget -c -q -t 10 -O '/tmp/{0}' '{1}'".format(save_name, link))
            stdout.read()
        except paramiko.SSHException as exception:
            logger.error("执行远程命令失败：{0}".format(exception))

            return False

        logging.info("远程下载完成")

        return True
    except KeyboardInterrupt:
        logger.info('用户手动结束进程，执行清理程序')

        return False


def download_file_to_local(ssh: paramiko.SSHClient, filename: str, target: str, target_filename: str) -> bool:
    """
    将远程服务器上的文件回传至本地.

    :param ssh:
    :param filename:
    :param target:
    :param target_filename:
    :return:
    """
    try:
        logger.info("正在建立SFTP连接")
        try:
            sftp = ssh.open_sftp()
        except paramiko.SSHException as exception:
            logging.error("FTP连接失败：{0}".format(exception))

            return False

        file_path = "/tmp/{0}".format(filename)
        try:
            file_stat = sftp.stat(file_path)
        except FileNotFoundError:
            logger.error("SFTP无法找到指定路径的文件：{0}".format(file_path))

            return False

        target_file_path = os.path.join(target, target_filename)

        shift = '.temp'
        if os.path.isfile(target_file_path) is False:
            try:
                open(target_file_path + shift, 'w').close()
            except PermissionError:
                logger.error('该目录没有写入权限:{0}'.format(target))

                return False
        else:
            prompt = str(input('已存在同名文件，是否覆盖[y/N]:')).lower()
            if 'n' == prompt[0] if prompt else 'n':
                logger.info('下载结束，程序退出')

                return False

        logger.info("开始回传：{0}".format(target_filename))

        bar = progressbar.ProgressBar()
        bar.start(int(file_stat.st_size / 1024))
        try:
            sftp.get(file_path, target_file_path + shift, lambda size, total: bar.update(int(size / 1024)))
        except IOError as exception:
            sftp.close()

            logger.error("回传文件失败：{0}".format(exception))

            return False
        except SFTPError as exception:
            bar.finish()
            logger.error("回传文件失败：{0}".format(exception))

            sftp.close()
            os.remove(target_file_path + shift)

            return False

        bar.finish()
        sftp.close()

        shutil.move(target_file_path + shift, target_file_path)
        logger.info("回传完成")

        return True
    except KeyboardInterrupt:
        logger.info('用户手动结束进程，执行清理程序')

        return False


def remove_remote_download_file(ssh: paramiko.SSHClient, filename: str):
    """
    清理远程服务器文件.

    :param ssh:
    :param filename:
    :return:
    """
    logger.info("清除远程服务器的临时文件")
    try:
        stdin, stdout, stderr = ssh.exec_command("rm -f '/tmp/{0}'".format(filename))
        stdout.read()
    except paramiko.SSHException as exception:
        logger.error("执行远程命令失败：{0}".format(exception))

        return False

    return True


if '__main__' == __name__:
    default_ssh_key = os.path.join(os.environ['HOME'] if sys.platform in ['darwin', 'linux'] else '', '.ssh', 'id_rsa.pub')
    parser = argparse.ArgumentParser(description="通过远程下载服务器进行文件下载，再通过FTP将文件下载到本地，适用于墙外软件的下载")
    parser.add_argument('host', help="远程服务器地址")
    parser.add_argument('file', help='要下载的文件地址')
    parser.add_argument('-t', '--target', help="保存位置，默认为当前目录", default='.')
    parser.add_argument('-p', '--port', help="远程服务器端口", default=22)
    parser.add_argument('-u', '--username', help="登录远程服务器的用户名", default="root")
    parser.add_argument('-k', '--use-key', help="使用密钥登录远程服务器", action="store_true")
    parser.add_argument('-P', '--password', help="登录远程服务器的密码，非交互模式时使用")
    parser.add_argument('-K', '--key', help="如果使用密钥登录，则需要指定密钥文件，默认使用: ~/.ssh/id_rsa.pub", default=default_ssh_key)

    args = parser.parse_args()

    password = args.password

    if not password and args.use_key is False:
        password = getpass.getpass("{0}用户的登录密码：".format(args.username))

    ssh_handle = connect_ssh(args.host, args.port, args.username, password, args.use_key, args.key)
    if ssh_handle is not False:
        parser_args = parse.urlparse(args.file)
        file_name = os.path.split(parser_args.path)[-1]
        suffix = "*###*{0}{1}".format(datetime.datetime.now(), random.random())

        remote_save_name = "{0}{1}".format(file_name, suffix)
        if remote_download_file(ssh_handle, args.file, remote_save_name) is True:
            download_file_to_local(ssh_handle, remote_save_name, args.target, file_name)

        remove_remote_download_file(ssh_handle, remote_save_name)

        ssh_handle.close()
