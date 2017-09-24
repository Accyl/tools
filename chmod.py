#!/usr/bin/env python3
# _._ coding:utf-8 _._


import os


def main():
    path = input('要校正的路径(./):')

    if not path:
        path = os.path.realpath('.')

    recursive = input('是否向下递归(y/N):')
    recursive = True if recursive and 'y' == recursive[0].lower() else False

    file_mode = script_file_mode = 664
    unified_mode = input('是否使用单一文件权限,默认权限为664(Y/n):')
    unified_mode = False if unified_mode and 'n' == unified_mode[0].lower() else True

    if unified_mode is False:
        file_mode = input('普通文件的权限(664):')
        file_mode = file_mode if file_mode else 664

        script_file_mode = input('可执行脚本文件(.sh)的权限(775):')
        script_file_mode = script_file_mode if script_file_mode else 775

    dir_mode = 775
    correction_dir = input('是否校正目录(y/N):')
    correction_dir = True if correction_dir and 'y' == correction_dir[0].lower() else False

    if correction_dir is True:
        dir_mode = input('目录的权限(775):')
        dir_mode = dir_mode if dir_mode else 775

    ignore_hide_file_and_dir = input('忽略隐藏文件和文件夹(Y/n):')
    ignore_hide_file_and_dir = False if ignore_hide_file_and_dir and 'n' == ignore_hide_file_and_dir[0] else True

    print('格式化路径:{0} 递归:{1} 普通文件权限:{2} 可执行脚本(.sh)文件权限:{3} 校正目录:{4} 目录权限:{5} 忽略隐藏文件和文件夹:{6}'.format(path, recursive,
                                                                                                   file_mode,
                                                                                                   script_file_mode,
                                                                                                   correction_dir, dir_mode,
                                                                                                   ignore_hide_file_and_dir))
    confirm = input('即将执行目录格式化,请确认是否执行(Y/n):')
    confirm = False if confirm and 'n' == confirm[0].lower() else True

    if confirm is False:
        print('取消执行权限校正,程序退出')
        exit(0)

    print('开始执行权限校正')
    correction(path=path, recursive=recursive, file_mode=file_mode, script_file_mode=script_file_mode, correction_dir=correction_dir, dir_mode=dir_mode, ignore_hide_file_and_dir=ignore_hide_file_and_dir)
    print('权限校正完成')


def correction(path, recursive=False, file_mode=664, script_file_mode=664, correction_dir=False, dir_mode=775, ignore_hide_file_and_dir=True):
    for DirEntity in os.scandir(path):
        if DirEntity.is_symlink() is True:
            continue

        if '.' == DirEntity.name[0] and ignore_hide_file_and_dir:
            continue

        if DirEntity.is_dir() is True:
            if correction_dir is True:
                print('chmod {0} {1}'.format(dir_mode, DirEntity.path))
                os.system('chmod {0} "{1}"'.format(dir_mode, DirEntity.path))

            if recursive is True:
                correction(DirEntity.path, recursive=recursive, file_mode=file_mode, script_file_mode=script_file_mode, correction_dir=correction_dir, dir_mode=dir_mode, ignore_hide_file_and_dir=ignore_hide_file_and_dir)

        if DirEntity.is_file() is True:
            if '.sh' == DirEntity.name[-3:]:
                print('chmod {0} {1}'.format(script_file_mode, DirEntity.path))
                os.system('chmod {0} "{1}"'.format(script_file_mode, DirEntity.path))
            else:
                print('chmod {0} {1}'.format(file_mode, DirEntity.path))
                os.system('chmod {0} "{1}"'.format(file_mode, DirEntity.path))


if '__main__' == __name__:
    main()



