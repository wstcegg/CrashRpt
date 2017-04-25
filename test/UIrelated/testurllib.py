from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
import os
import urllib.request


mut = QMutex()
finished_num = 0
thread_flag = 0   # 0 运行  1 暂停 2终止


class MyThread(QThread):
    _signal = pyqtSignal(str)

    def __init__(self, thread_ID, url, beg, end, name=''):
        super().__init__()
        self.thread_ID = thread_ID
        self.name = name
        self._url = url
        self._beg = beg
        self._end = end

    def run(self):
        print("Starting " + self.name)
        global finished_num
        global thread_flag

        index = self._beg
        while index < self._end:
            # 终止线程
            # print('thread_flag:' + str(thread_flag))
            if thread_flag == 2:
                break

            fname = 'error_report_' + str(index) + '.zip'
            furl = self._url + fname
            if os.path.exists(fname):
                print(fname + ' already exist')
                mut.lock()
                finished_num += 1
                mut.unlock()
            else:
                try:
                    urllib.request.urlretrieve(furl, fname)
                except Exception as e:
                    # print('in the exception')
                    if os.path.exists(fname):  # 出现异常文件都要删除
                        try:
                            os.remove(fname)
                        except Exception as e:
                            print(e)
                    if hasattr(e, 'code') and e.code:  # HTTPError
                        fname += ':HTTPError'
                    elif hasattr(e, 'errno') and e.errno:
                        index -= 1  # 重新下载
                        fname += ':现有连接断开'
                    elif hasattr(e, 'reason') and e.reason:  # 无法建立连接
                        index -= 1  # 重新下载
                        fname += ':无法建立连接'
                    else:
                        fname += ":下载异常"

                else:
                    finished_num += 1
                    print('other failure')
            index += 1
            print('id =' + str(self.thread_ID) + 'i=' + str(index) + ' finishe_num:' + str(finished_num))
        print("Exiting " + self.name)


if __name__=='__main__':

    url_base = r'http://222.73.55.231/BugTrap/reports/swcSelf8.8.8/'
    # dir = r'crash_data\\'
    #
    # filename = 'error_report_' + '147759' + '.zip'
    #
    # url = url_base + filename
    # fpath = dir + filename
    #
    # urllib.request.urlretrieve(url, fpath)

    t1 = MyThread(0, url_base, 147760, 147761)
    t1.start()
    t1.wait()
