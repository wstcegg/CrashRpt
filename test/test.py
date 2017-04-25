from PyQt5.QtCore import *
import argparse


class JobHandler1(QThread):
    _signal = pyqtSignal(str)

    def __init__(self, thread_ID):
        super().__init__()
        self.thread_id = thread_ID

    def run(self):
        print("Starting ", self.thread_id)


def main():
    thread_num = 10
    threads = []
    for i in range(thread_num):
        t1 = JobHandler1(i)
        threads.append(t1)

    for i in range(thread_num):
        threads[i].start()
        threads[i].wait()


class MyArgParse:
    def __init__(self):
        self.args = None
        self.item_names = \
            ['崩溃包URL', '起始编号', '结束编号',
             '崩溃包文件夹',
             '符号文件路径',
             '客户端运行',
             '分析本地崩溃包']
        self.error_code = 0

    def url_valid(self):
        if self.args.local:
            return True

        if not self.args.url:
            self.error_code = -1
            return False
        print(self.item_names[0] + ':', self.args.url)
        return True

    def idx_beg_valid(self):
        if self.args.local:
            return True

        if not self.args.idx_beg:
            self.error_code = -2
            return False
        print(self.item_names[1] + ':', self.args.idx_beg)
        return True

    def idx_end_valid(self):
        if self.args.local:
            return True

        if not self.args.idx_beg:
            self.error_code = -3
            return False
        print(self.item_names[2] + ':', self.args.idx_end)
        return True

    def zip_valid(self):
        if not self.args.zip:
            self.error_code = -4
            return False
        print(self.item_names[3] + ':', self.args.zip)
        return True

    def symbol_valid(self):
        if not self.args.symbol:
            self.error_code = -5
            return False
        print(self.item_names[4] + ':', self.args.symbol)
        return True

    def is_valid(self):
        if self.args.client:
            print(self.item_names[5])
            return True

        if not self.url_valid():
            return False

        if not self.idx_beg_valid():
            return False

        if not self.idx_end_valid():
            return False

        if not self.zip_valid():
            return False

        if not self.symbol_valid():
            return False

        return True

    def command_error(self):
        print("请输入有效的命令参数:%d [%s]" %
              (self.error_code, self.item_names[-1 * self.error_code - 1]))

    def parse_args(self):
        ap = argparse.ArgumentParser()
        ap.add_argument("-url", "--url", help=self.item_names[0], type=str)
        ap.add_argument("-b", "--idx_beg", help=self.item_names[1], type=int)
        ap.add_argument("-e", "--idx_end", help=self.item_names[2], type=int)
        ap.add_argument("-z", "--zip_folder", help=self.item_names[3], type=str)
        ap.add_argument("-s", "--symbol_folder", help=self.item_names[4], type=str)
        ap.add_argument("-c", "--client", help=self.item_names[5], action='store_true')
        ap.add_argument("-l", "--local", help=self.item_names[6], action='store_true')
        self.args = ap.parse_args()


if __name__ == '__main__':
    parser = MyArgParse()
    parser.parse_args()

    if parser.is_valid():
        pass
    else:
        parser.command_error()