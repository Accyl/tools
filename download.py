#!/usr/bin/env python3
# _._ coding: utf-8 _._

"""
该工具适用于需要翻墙下载文件并且VPN或ss下载不稳定的情况。
使用该工具需要你先有一个在墙外的服务器

@author Accyl <email@accyl.cn>
"""

import argparse
import paramiko
from paramiko import ssh_exception
import getpass
import logging
import os
import random
import datetime
import progressbar


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()


def connect_ssh(host: str, port: int=22, username: str='root', passwd: str='', use_key: bool=False, key: str=''):
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


def remote_download_file(ssh: paramiko.SSHClient, link: str, save_name: str) -> bool:
    """
    开始在远程服务器下载文件.

    :param ssh:
    :param link:
    :param save_name:
    :return:
    """
    logging.info("开始下载：{0}".format(link))
    try:
        stdin, stdout, stderr = ssh.exec_command("wget -cO '/tmp/{0}' '{1}'".format(save_name, link))
        stdout.read()
    except paramiko.SSHException as exception:
        logger.error("执行远程命令失败：{0}".format(exception))
        return False

    logging.info("下载完成")
    return True


def download_file_to_local(ssh: paramiko.SSHClient, filename: str, target: str, target_filename: str) -> bool:
    """
    将远程服务器上的文件回传至本地.

    :param ssh:
    :param filename:
    :param target:
    :param target_filename:
    :return:
    """
    logger.info("正在建立SFTP连接")
    try:
        sftp = ssh.open_sftp()
    except paramiko.SSHException as exception:
        logging.error("FTP连接失败：{0}".format(exception))
        return False

    file_path = os.path.join('/tmp', filename)
    file_stat = sftp.stat(file_path)

    logger.info("开始回传：{0}".format(target_filename))

    bar = progressbar.ProgressBar()
    bar.start(file_stat.st_size)
    try:
        sftp.get(file_path, os.path.join(target, target_filename),
                 lambda size, total: bar.update(size))
    except IOError as exception:
        logger.error("回传文件失败：{0}".format(exception))
        return False

    bar.finish()
    sftp.close()
    logger.info("回传完成")
    return True


def remove_remote_download_file(ssh: paramiko.SSHClient, filename: str):
    """
    清理远程服务器文件.

    :param ssh:
    :param filename:
    :return:
    """
    logger.info("清除远程服务器的临时文件")
    try:
        stdin, stdout, stderr = ssh.exec_command("rm -f '{0}'".format(os.path.join('/tmp', filename)))
    except paramiko.SSHException as exception:
        logger.error("执行远程命令失败：{0}".format(exception))
        return False

    return True


parser = argparse.ArgumentParser(description="通过远程下载服务器进行文件下载，再通过FTP将文件下载到本地，适用于墙外软件的下载")
parser.add_argument('host', help="远程服务器地址")
parser.add_argument('file', help='下载连接地址')
parser.add_argument('target', help="保存位置，默认为当前目录", default='.', nargs='?')
parser.add_argument('-p', '--port', help="远程服务器端口", default=22)
parser.add_argument('-u', '--username', help="登录远程服务器的用户名", default="root")
parser.add_argument('-k', '--use-key', help="使用密钥登录远程服务器", action="store_true")
parser.add_argument('-P', '--password', help="登录远程服务器的密码，非交互模式时使用")
parser.add_argument('-K', '--key', help="如果使用密钥登录，则需要指定密钥文件")

args = parser.parse_args()

password = args.password

if not password and args.use_key is False:
    password = getpass.getpass("{0}用户的登录密码：".format(args.username))

if '__main__' == __name__:
    ssh_handle = connect_ssh(args.host, args.port, args.username, password, args.use_key, args.key)
    if ssh_handle is not False:
        file_name = os.path.split(args.file)[-1]
        suffix = "*###*{0}{1}".format(datetime.datetime.now(), random.random())

        remote_download_file(ssh_handle, args.file, "{0}{1}".format(file_name, suffix))

        download_file_to_local(ssh_handle, "{0}{1}".format(file_name, suffix), args.target, file_name)

        remove_remote_download_file(ssh_handle, "{0}{1}".format(file_name, suffix))

        ssh_handle.close()
