import argparse
import os
import logging
from logging.handlers import RotatingFileHandler

import Initialize
import AutoDownload
import analyze
import IOHelper

# # public
# probe_dll = ctypes.CDLL(r"runtime\CrashRptProbe1401.dll")
# load_dump = probe_dll['load_dump2']
#
# dmp_path = r'E:\Infomation\crashdump.dmp'
# pdb_path = r'D:\code\TOOLS\released_program\swc_free_bin_4378\bin\release'
#
# def test_dll():
#     str_f1 = "E:\\Information\\full_4272\\unzip\\error_report_22010\\crashdump.dmp"
#     str_f2 = "D:\\code\\TOOLS\\released_program\\swc_free_bin_4272\\bin\\release"
#
#     f1 = ctypes.c_char_p(str_f1.encode('gb2312'))
#     f2 = ctypes.c_char_p(str_f2.encode('gb2312'))
#     info_buf = ctypes.create_string_buffer(128000)
#
#     # load dump info through DLL
#     load_dump(f1, f2, info_buf)
#
#     # convert info into python xml format
#     info = info_buf.value.decode('utf-8')
#     print(info)


class MyArgParse:
    def __init__(self):
        self.args = None
        self.item_names = \
            ['崩溃包URL', '起始编号', '结束编号',
             '崩溃包文件目录',
             '符号文件目录',
             '无效记录定义文件',
             '客户端模式运行',
             '解析页面崩溃包列表',
             '离线分析',
             '重复次数']
        self.error_code = 0

    def url_valid(self):
        if self.args.off_line:
            return True

        if not self.args.url:
            self.error_code = -1
            return False
        print()
        print(self.item_names[0] + ':', self.args.url)
        return True

    def idx_beg_valid(self):
        if self.args.off_line:
            return True

        if not self.args.idx_beg:
            self.error_code = -2
            return False

        print(self.item_names[1] + ': ', end='')
        if self.args.idx_beg < 0:
            print('无限制')
        else:
            print(self.args.idx_beg)
        return True

    def idx_end_valid(self):
        if self.args.off_line:
            return True

        if not self.args.idx_beg:
            self.error_code = -3
            return False

        print(self.item_names[2] + ': ', end='')
        if self.args.idx_end < 0:
            print('无限制')
        else:
            print(self.args.idx_end)
        return True

    def report_valid(self):
        if not self.args.report_folder:
            self.error_code = -4
            return False
        print(self.item_names[3] + ':', self.args.report_folder)
        return True

    def symbol_valid(self):
        if not self.args.symbol_folder:
            self.error_code = -5
            return False
        print(self.item_names[4] + ':', self.args.symbol_folder)
        return True

    def invalid_define_valid(self):
        if not self.args.invalid_define:
            self.error_code = -6
            return False
        print(self.item_names[5] + ':', self.args.invalid_define)
        return True

    def is_client_side(self):
        return self.args.client_mode

    def is_valid(self):
        if self.is_client_side():
            return True

        if not self.url_valid():
            return False

        if not self.idx_beg_valid():
            return False

        if not self.idx_end_valid():
            return False

        if not self.report_valid():
            return False

        if not self.symbol_valid():
            return False

        if not self.invalid_define_valid():
            return False

        print("工作模式: ", end='')
        if self.is_client_side():
            print('客户端模式')
        else:
            print('服务端模式')

        print("是否解析页面崩溃包列表: ", end='')
        if self.args.retrieve_webpage:
            print('是')
        else:
            print('否')

        print("执行次数: ", end='')
        if self.args.repeat_num > 0:
            print(self.args.repeat_num)
        else:
            print('重复执行')

        if self.args.confirm_cmd:
            while True:
                user_input = input('本次查询命令是否正确？(Y/N)')
                if user_input == 'Y' or user_input == 'y':
                    return True
                elif user_input == 'N' or user_input == 'n':
                    return False

        return True

    def command_error(self):
        '''
            分析错误代码，返回提示语
            错误代码范围  [-n,-1]
        :return: 错误信息提示语
        '''
        return ("<%d> 请输入该命令参数: [%s]" %
                (self.error_code, self.item_names[abs(self.error_code) - 1]))

    def parse_args(self):
        ap = argparse.ArgumentParser()
        ap.add_argument("-cc", "--confirm_cmd", help="confirm_command_line", action='store_true')
        ap.add_argument("-u", "--url", help=self.item_names[0], type=str)
        ap.add_argument("-ib", "--idx_beg", help=self.item_names[1], type=int)
        ap.add_argument("-ie", "--idx_end", help=self.item_names[2], type=int)
        ap.add_argument("-rf", "--report_folder", help=self.item_names[3], type=str)
        ap.add_argument("-sf", "--symbol_folder", help=self.item_names[4], type=str)
        ap.add_argument("-ide", "--invalid_define", help=self.item_names[5], type=str)
        ap.add_argument("-c", "--client_mode", help=self.item_names[6], action='store_true')
        ap.add_argument("-rwp", "--retrieve_webpage", help=self.item_names[7], action='store_true')
        ap.add_argument("-ol", "--off_line", help=self.item_names[8], action='store_true')
        ap.add_argument("-re", "--repeat_num", help=self.item_names[9], type=int)
        self.args = ap.parse_args()

    def update_config(self, conf):
        if self.is_client_side():
            print("注意！试图在客户端模式下更新配置参数！")
        conf.url = self.args.url
        conf.idx_beg = self.args.idx_beg
        conf.idx_end = self.args.idx_end
        conf.report_folder = self.args.report_folder
        conf.symbol_folder = self.args.symbol_folder
        conf.invalid_define = self.args.invalid_define

        conf.repeat_num = self.args.repeat_num
        conf.client_mode = self.args.client_mode
        conf.retrieve_webpage = self.args.retrieve_webpage
        conf.off_line = self.args.off_line

        # 更新目录结构！
        conf.calc_folder()

        return conf


def client_job(conf, md):
    print('客户端模式启动')

    report_list = AutoDownload.download_analyze(conf, md, repeat_num=1, interval=1)
    analyze.analyze_client(conf, md, report_list)
    # excel_.update_xml(conf, md)


def server_job(conf, md):
    print('服务端模式启动')
    dc = IOHelper.DirCleaner(conf)
    # dc.clean_zip()
    dc.clean_unzip()

    AutoDownload.download_analyze(conf, md, repeat_num=conf.repeat_num,
                                  interval=1,
                                  remove_after_use=True,
                                  ignore_classified=True)
    # analyze.analyze_server(conf, md, report_id, invalid_records)


def prepare_log(conf):
    try:
        # 日志路径
        log_name = conf.report_folder + '\\runtime.log'
        # if os.path.exists(log_name):
        #     os.remove(log_name)

        # 日志格式
        log_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')

        my_handler = RotatingFileHandler(log_name, mode='a', maxBytes=5*1024*1024,
                                         backupCount=1, encoding=None, delay=0)
        my_handler.setFormatter(log_formatter)
        my_handler.setLevel(logging.INFO)

        root_log = logging.getLogger('root')
        root_log.setLevel(logging.INFO)
        root_log.addHandler(my_handler)

    except Exception as e:
        print('prepare log failed!: %s' % e)
        return False
    return True


def main():
    # 读取配置参数
    conf = Initialize.Conf()
    conf.load(r'data\config.json')

    # 读取模块分工文件
    md = Initialize.MD()
    md.load(conf.module_define)

    # 解析命令行参数
    parser = MyArgParse()
    parser.parse_args()

    # 准备日志文件
    if not prepare_log(conf):
        return

    if not parser.is_valid():       # 命令行参数非法
        error_message = parser.command_error()
        print(error_message)
    elif parser.is_client_side():   # 客户端模式
        conf.client_mode = True
        client_job(conf, md)
    else:                           # 服务端模式
        # 读取无效记录文件
        inva = Initialize.Invalid()
        inva.load(conf.invalid_define)
        conf.invalid_records = inva.invalid_list

        # 利用命令行参数，更新配置参数
        conf = parser.update_config(conf)
        conf.client_mode = False
        server_job(conf, md)

if __name__ == "__main__":
    main()