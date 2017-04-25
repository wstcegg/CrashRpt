import sys
import time
import urllib.request
import os

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


class ThreadStatus:
    def __init__(self):
        self.num_of_downloads = 0   # number of download files
        self.exit_thread = False    # whether exit all threads
        self.pause_thread = False   # whether pause all threads
        self.thread_report_status = False  # thread report status after finish one download

    def clear(self):
        self.num_of_downloads = 0   # number of download files
        self.exit_thread = False    # whether exit all threads
        self.pause_thread = False   # whether pause all threads
        self.thread_report_status = False  # thread report status after finish one download


mut = QMutex()          # used by SingleThread
ts = ThreadStatus()     # used by SingleThread & ThreadManager
tm = None   # used by other widget


class SingleThread(QThread):
    '''
    Thread for download and unzip files
    '''

    # thread_id. total number, current finishes, current file
    _single_begin_one = pyqtSignal(int, int)

    def __init__(self, thread_ID):
        super().__init__()
        self.thread_ID = thread_ID

        self.file_index_list = []
        self.url_base = ''
        self.save_dir = ''

        self.download_dlg = None
        self.exit_dlg = None

        #
        self.cur_file = ''

    def set_parameter(self, file_index_list, url_base, save_dir='data\\'):
        self.file_index_list = file_index_list
        self.url_base = url_base
        self.save_dir = save_dir

    def set_dialog(self, download_dlg=None, exit_dlg=None):
        if download_dlg:
            self.download_dlg = download_dlg
            self._single_begin_one.connect(download_dlg.frame_update)
        if exit_dlg:
            self.exit_dlg = exit_dlg
            self._single_begin_one.connect(exit_dlg.frame_update)

    def get_file_name(self, idx):
        self.cur_file = 'error_report_' + str(idx) + '.zip'
        return self.cur_file

    def make_full_url(self, idx):
        url = self.url_base + self.get_file_name(idx)
        return url

    def make_full_path(self, idx):
        url = self.save_dir + self.get_file_name(idx)
        return url

    def run(self):
        print("Starting " + str(self.thread_ID))
        global ts

        for idx, fnumber in enumerate(self.file_index_list):
            # pause:
            # should be put prior to exit,
            # it is likely to see the exit command followed by puse
            while ts.pause_thread and not ts.exit_thread:     #
                time.sleep(1)

            # exit
            if ts.exit_thread:
                break

            url = self.make_full_url(fnumber)
            filename = self.make_full_path(fnumber)

            # emit signal of current progress made
            self._single_begin_one.emit(self.thread_ID, idx + 1)
            if os.path.exists(filename):
                print(filename + ' already exist')

                # lock before writing shared variable
                mut.lock()
                ts.num_of_downloads += 1
                mut.unlock()
            else:
                try:
                    print("downloading file: " + filename + " from: " + url)
                    urllib.request.urlretrieve(url, filename)
                except Exception as e:
                    if os.path.exists(filename):  # 出现异常,删除文件
                        try:
                            os.remove(filename)
                        except Exception as e:
                            print(e)
                    if hasattr(e, 'code') and e.code:  # HTTP Error
                        print(':HTTPError')
                    elif hasattr(e, 'errno') and e.errno:
                        fnumber -= 1  # 重新下载
                        print(':现有连接断开')
                    elif hasattr(e, 'reason') and e.reason:  # 无法建立连接
                        fnumber -= 1  # 重新下载
                        print(':无法建立连接')
                    else:
                        print(':其他下载异常')
                else:
                    ts.num_of_downloads += 1

        print("Exiting thread: " + str(self.thread_ID))


class ThreadManager:
    '''
    To controll the thread set, including start, pause, stop and so on
    '''
    def __init__(self):
        self.threads = []

        self.url = ''
        self.beg = 0
        self.end = 0
        self.num_of_threads = 0

    def set_parameter(self, url, beg=252300, end=252301):
        #
        self.url = url
        self.beg = beg
        self.end = end

    def set_num_threads(self, num):
        # restrict at most four threads on a core i3 computer
        self.num_of_threads = min(max(num, 0), 4)

    def set_dialog(self, download_dlg=None, exit_dlg=None):
        for idx in range(len(self.threads)):
            self.threads[idx].set_dialog(download_dlg, exit_dlg)

    def init_download_thread(self):
        #
        if self.end < self.beg:
            print('begin and end position not valid!')
            return

        self.threads.clear()

        # if number of files less than number of threads, set step to 1
        step = int((self.end - self.beg + 1) / self.num_of_threads)
        step = max(1, step)

        for idx in range(self.num_of_threads):
            thread = SingleThread(idx)

            low = self.beg+step*idx
            high = self.beg+step*(idx+1)
            high = min(high, self.end+1)

            l = [idx for idx in range(low, high)]
            print(l)

            thread.set_parameter(l, self.url)
            self.threads.append(thread)

    def is_downloading(self):
        for thread in self.threads:
            if thread.isRunning():
                return True
        return False

    def start_downloading(self):
        for thread in self.threads:
            thread.start()

    def pause_downloading(self):
        global ts
        ts.pause_thread = True

    def stop_downloading(self):
        global ts
        ts.pause_thread = False
        ts.exit_thread = True

    def who_is_running(self):
        status = []
        for idx, thread in enumerate(self.threads):
            status[idx].append(thread.isRunning())
        return status


class ExitDlg(QDialog):
    '''
    this class will warn user if any thread is running while closing dialogs
    '''
    def __init__(self, threads):
        super().__init__()
        #
        self.threads = threads
        #
        layout_main = QGridLayout()
        self.progress_bars = []
        for idx, thread in enumerate(threads):
            #
            lbl = QLabel('Thread %d: %s' % (idx, thread.cur_file))

            progress_bar = QProgressBar()
            progress_bar.setMaximum(100)
            progress_bar.setValue(0)
            self.progress_bars.append(progress_bar)

            layout_main.addWidget(lbl, idx, 0, 1, 1)
            layout_main.addWidget(progress_bar, idx, 1, 1, 1)

        self.btn_ok = QPushButton("请等待所有下载线程结束")
        layout_main.addWidget(self.btn_ok, len(threads), 0, 1, 1)
        self.setLayout(layout_main)
        self.setGeometry(500, 500, 300, 150)
        self.setWindowTitle('Exit Dialog')

        # check if all threads exits periodically
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress_bar)
        self.timer.start(100)

    def update_progress_bar(self):
        #
        remaining_thread = 0
        for idx, threadi in enumerate(self.threads):
            max_value = self.progress_bars[idx].maximum()
            if threadi.isRunning():
                cur_value = self.progress_bars[idx].value() + 1
                cur_value = min(cur_value, max_value-1)   # for unfinished threads, max pos is max-1
                self.progress_bars[idx].setValue(cur_value)
                remaining_thread += 1
            else:
                self.progress_bars[idx].setValue(max_value)

        if remaining_thread == 0:
            self.close()


class DownLoadProcessDlg(QDialog):
    '''
    Download dialog
    '''
    global tm

    def __init__(self):
        super().__init__()

        tm.set_num_threads(4)
        tm.init_download_thread()
        self.threads = tm.threads
        tm.set_dialog(download_dlg=self)

        # upper ui, process bar and its label
        layout_main = QGridLayout()
        self.pbars = []
        for idx, thread in enumerate(self.threads):
            #
            lbl_title = QLabel('线程 %d: %s' % (idx, '---'))

            pb = QProgressBar()
            pb.setMaximum(len(thread.file_index_list))
            pb.setValue(0)

            process_str = str('%d/%d' % (0, len(thread.file_index_list)))
            lbl_process = QLabel(process_str)

            self.pbars.append(pb)
            layout_main.addWidget(lbl_title, idx, 0, 1, 1)
            layout_main.addWidget(pb, idx, 1, 1, 3)
            layout_main.addWidget(lbl_process, idx, 4, 1, 1)

        # lower ui, control button
        self.btn_ok = QPushButton('开始')
        self.btn_cancel = QPushButton('停止')
        layout_main.addWidget(self.btn_ok, len(self.threads), 1, 1, 1)
        layout_main.addWidget(self.btn_cancel, len(self.threads), 3, 1, 1)

        self.setLayout(layout_main)
        self.setGeometry(500, 500, 300, 200)
        self.show()

        self.btn_ok.clicked.connect(self.switch_download)
        self.btn_cancel.clicked.connect(self.stop_download)

        # a timer
        self.count = 0
        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.print_hello)

        # other variable
        self.started = False
        self.paused = False

    def frame_update(self, thread_id, cur_idx):
        print('download signal')
        self.pbars[thread_id].setValue(cur_idx)

    def print_hello(self):
        global ts
        global tm
        print('time consumption: %d s, num of downloads: %d' % (self.count, ts.num_of_downloads))
        if not tm.is_downloading():
            self.started = False
            self.btn_ok.setText('开始')
            self.timer1.stop()
        self.count += 1

    def stop_download(self):
        global ts
        global tm

        ts.exit_thread = True
        ts.pause_thread = False

        while tm.is_downloading():
            time.sleep(1)

        self.started = False
        self.timer1.stop()

    def switch_download(self):
        global ts
        global tm

        if not self.started:
            self.started = True
            self.timer1.start(1000)

            global ts
            ts.clear()
            tm.set_num_threads(4)
            tm.init_download_thread()
            self.threads = tm.threads
            tm.set_dialog(download_dlg=self)
            tm.start_downloading()

            self.btn_ok.setText('暂停')
            self.paused = False
            return

        if self.paused:
            self.timer1.start(1000)
            tm.start_downloading()
            self.btn_ok.setText('暂停')
            self.paused = False
        else:
            self.timer1.stop()
            # global variable, running thread pause after finishing current task
            ts.pause_thread = False
            while tm.is_downloading():
                time.sleep(1)
            self.btn_ok.setText('继续')
            self.paused = True

    def closeEvent(self, QCloseEvent):
        global ts
        global tm
        ts.exit_thread = True
        exit_dlg = ExitDlg(tm.threads)
        exit_dlg.exec_()


class DownLoadConfigDlg(QDialog):
    '''
    Download dialog
    '''
    def __init__(self):
        super().__init__()
        # first line
        self.lbl_url = QLabel('URL：')
        self.le_url = QLineEdit('')

        # second line
        self.lbl_beg = QLabel('起始：')
        self.le_beg = QLineEdit('')
        self.lbl_end = QLabel('结束：')
        self.le_end = QLineEdit('')
        self.lbl_sum = QLabel('总计：0')

        # third line
        self.lbl_saveto = QLabel('保存至：')
        self.le_saveto = QLineEdit('')
        self.btn_saveto_browse = QPushButton('浏览：')

        # fourth line
        self.lbl_pdb = QLabel('PDB：')
        self.le_pdb = QLineEdit('')
        self.btn_pdb_browse = QPushButton('浏览：')

        # fifth line
        self.btn_ok = QPushButton('确定')
        self.btn_cancel = QPushButton('取消')

        # set layout style
        self.init_ui()

        # set initial value for variable
        self.started = False
        self.paused = False

        self.url = r'http://222.73.55.231/BugTrap/reports/swcSelf8.8.7/'
        self.beg = 252300
        self.end = 252339
        self.save_folder = os.getcwd() + '\\data'
        self.pdb_folder = r''

        self.update_frame()

        # connect signal and slots
        self.le_beg.textChanged.connect(self.update_sum)
        self.le_end.textChanged.connect(self.update_sum)
        self.btn_ok.clicked.connect(self.on_ok)
        self.btn_cancel.clicked.connect(self.on_cancel)

    def update_data(self):
        # update data from frame widget
        self.url = self.le_url.text()
        self.beg = int(self.le_beg)
        self.end = int(self.le_end)
        self.save_folder = self.le_saveto.text()
        self.pdb_folder = self.le_pdb.text()

    def update_frame(self):
        # set initial text for widget
        self.le_url.setText(self.url)
        self.le_beg.setText(str(self.beg))
        self.le_end.setText(str(self.end))
        self.update_sum()
        self.le_saveto.setText(self.save_folder)
        self.le_pdb.setText(self.pdb_folder)

    def on_ok(self):
        global tm
        tm = ThreadManager()
        tm.set_parameter(self.url, self.beg, self.end)
        self.close()

    def on_cancel(self):
        self.close()

    def update_sum(self):
        self.beg = int(self.le_beg.text())
        self.end = int(self.le_end.text())
        total_num = self.end-self.beg + 1
        self.lbl_sum.setText('总计：%d' % total_num)
        if total_num>=0:
            self.lbl_sum.setStyleSheet('color: black')
        else:
            self.lbl_sum.setStyleSheet('color: red')

    def init_ui(self):
        #
        layout_main = QGridLayout()
        layout_main.setSizeConstraint(QLayout.SetFixedSize)

        layout_main.addWidget(self.lbl_url, 0, 0, 1, 1)
        layout_main.addWidget(self.le_url, 0, 1, 1, 3)

        layout_main.addWidget(self.lbl_beg, 1, 0, 1, 1)
        layout_main.addWidget(self.le_beg, 1, 1, 1, 1)
        layout_main.addWidget(self.lbl_end, 1, 2, 1, 1)
        layout_main.addWidget(self.le_end, 1, 3, 1, 1)
        layout_main.addWidget(self.lbl_sum, 1, 4, 1, 1)

        layout_main.addWidget(self.lbl_saveto, 2, 0, 1, 1)
        layout_main.addWidget(self.le_saveto, 2, 1, 1, 3)
        layout_main.addWidget(self.btn_saveto_browse, 2, 4, 1, 1)

        layout_main.addWidget(self.lbl_pdb, 3, 0, 1, 1)
        layout_main.addWidget(self.le_pdb, 3, 1, 1, 3)
        layout_main.addWidget(self.btn_pdb_browse, 3, 4, 1, 1)

        layout_main.addWidget(self.btn_ok, 4, 1, 1, 1)
        layout_main.addWidget(self.btn_cancel, 4, 3, 1, 1)

        self.setLayout(layout_main)
        self.setGeometry(500, 500, 550, 150)
        self.setWindowTitle('QCheckBox')
        self.show()


class MainDlg(QDialog):
    '''
    Main dialog
    '''
    def __init__(self):
        super().__init__()
        btn_download = QPushButton('下载')
        btn_local = QPushButton('读取本地')
        btn_start = QPushButton('开始')

        btn_download.clicked.connect(self.call_download_config_dialog)
        btn_start.clicked.connect(self.call_download_process_dialog)

        main_layout = QGridLayout()
        main_layout.addWidget(btn_download, 0, 0, 1, 1)
        main_layout.addWidget(btn_local, 0, 1, 1, 1)
        main_layout.addWidget(btn_start, 1, 0, 1, 1)

        self.setLayout(main_layout)
        self.setGeometry(500, 500, 550, 150)
        self.setWindowTitle('Main Window')
        self.show()

    def call_download_config_dialog(self):
        print('creating dialog config')
        dlg = DownLoadConfigDlg()
        dlg.exec_()

    def call_download_process_dialog(self):
        print('creating dialog process')
        dlg = DownLoadProcessDlg()
        dlg.exec_()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainDlg()
    sys.exit(app.exec_())
    print('exit success')
