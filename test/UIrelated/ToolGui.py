from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import urllib.request
import sys
import os


finished_num = 0
thread_flag = 0   # 0 运行  1 暂停 2终止


class DownLoadDlg(QDialog):

    _signal = pyqtSignal(int, name='set_total')

    def __init__(self, parent=None):
        super(DownLoadDlg, self).__init__(parent)
        self.threads = []
        self.beg = 0
        self.end = 0
        self.threadnum = 2
        Label_URL = QLabel("URL: ")
        Label_Beg = QLabel("起始: ")
        Label_End = QLabel("结束: ")
        Label_Total = QLabel("总计: ")
        self.Label_TotalNum = QLabel("0")
        Label_Save= QLabel("保存到: ")
        Label_PDB = QLabel("PDB目录: ")
        self.Edit_URL = QLineEdit()
        self.Edit_Beg = QLineEdit()
        self.Edit_End = QLineEdit()
        self.Edit_Save = QLineEdit()
        self.Edit_PDB = QLineEdit()
        self.Button_Skim1 = QPushButton("浏览")
        self.Button_Skim2 = QPushButton("浏览")
        self.Button_Ensure = QPushButton("确定")

        Label_URL.setFixedSize(40, 20)
        Label_Beg.setFixedSize(40, 20)
        Label_End.setFixedSize(40, 20)
        Label_Total.setFixedSize(40, 20)
        self.Label_TotalNum.setFixedSize(70, 20)
        self.Edit_Beg.setFixedSize(70, 20)
        self.Edit_End.setFixedSize(70, 20)

        Label_Save.setFixedSize(40, 20)
        Label_PDB.setFixedSize(40, 20)

        self.Button_Skim1.clicked.connect(self.Skim1)
        self.Button_Skim2.clicked.connect(self.Skim2)
        self.Button_Ensure.clicked.connect(self.Ensure)

        self.Edit_Beg.textChanged.connect(self.NumChanged)
        self.Edit_End.textChanged.connect(self.NumChanged)

        self._signal.connect(self.parentWidget().ProgressDlg.setTotalNum)
        Hlayout1 = QHBoxLayout()
        Hlayout1.addWidget(Label_URL)
        Hlayout1.addWidget(self.Edit_URL)
        Hlayout2 = QHBoxLayout()
        Hlayout2.addWidget(Label_Beg)
        Hlayout2.addWidget(self.Edit_Beg)
        Hlayout2.addWidget(Label_End)
        Hlayout2.addWidget(self.Edit_End)
        Hlayout2.addWidget(Label_Total)
        Hlayout2.addWidget(self.Label_TotalNum)

        Vlayout1 = QVBoxLayout()
        Vlayout1.addLayout(Hlayout1)
        Vlayout1.addLayout(Hlayout2)

        Hlayout3 = QHBoxLayout()
        Hlayout3.addWidget(Label_Save)
        Hlayout3.addWidget(self.Edit_Save)
        Hlayout3.addWidget(self.Button_Skim1)
        Hlayout4 = QHBoxLayout()
        Hlayout4.addWidget(Label_PDB)
        Hlayout4.addWidget(self.Edit_PDB)
        Hlayout4.addWidget(self.Button_Skim2)

        Vlayout2 = QVBoxLayout()
        Vlayout2.addLayout(Hlayout3)
        Vlayout2.addLayout(Hlayout4)

        Hlayout4 = QHBoxLayout()
        Hlayout4.addStretch()
        Hlayout4.addWidget(self.Button_Ensure)
        Hlayout4.addStretch()

        Vlayout = QVBoxLayout()
        Vlayout.addLayout(Vlayout1)
        Vlayout.addLayout(Vlayout2)
        Vlayout.addLayout(Hlayout4)
        Vlayout.addStretch()
        Vlayout.setSpacing(20)

        self.setLayout(Vlayout)
        # okBtn.clicked.connect(self.accept)
        self.setWindowTitle("下载")
        self.resize(200, 400)

        global finished_num
        finished_num = 0

    def Skim1(self):
        url = QFileDialog.getExistingDirectory(self, "选择文件夹",
                                                  "/home",
                                               QFileDialog.ShowDirsOnly
                                                  | QFileDialog.DontResolveSymlinks)
        self.Edit_Save.setText(url)

    def Skim2(self):
        url = QFileDialog.getExistingDirectory(self, "选择文件夹",
                                                  "/home",
                                               QFileDialog.ShowDirsOnly
                                                  | QFileDialog.DontResolveSymlinks)
        self.Edit_PDB.setText(url)

    def NumChanged(self):
        beg = self.Edit_Beg.text()
        end = self.Edit_End.text()
        try:
            if beg == "":
                self.beg = 0
            else:
                self.beg = int(beg)
            if end == "":
                self.end = 0
            else:
                self.end = int(end)
            #print(beg)
            #print(end)
            self.Label_TotalNum.setText(str(self.end+1 - self.beg))
        except ValueError:
            self.Label_TotalNum.setText("字符不合法")

    def Ensure(self):
        if self.Edit_URL.text() == '':
            QMessageBox.critical(self, "错误",
                                 self.tr("URL不能为空!"))
        elif self.beg < 0 or self.end < 0 or self.end < self.beg:
            QMessageBox.critical(self, "错误",
                                 self.tr("文件索引号错误!"))
        elif self.Edit_Save.text() == '':
            QMessageBox.critical(self, "错误",
                                 self.tr("保存路径不能为空!"))
        elif self.Edit_PDB.text() == '':
            QMessageBox.critical(self, "错误",
                                 self.tr("PDB目录不能为空!"))
        else:
            if self.parentWidget().ProgressDlg:
                self._signal.emit(self.end+1 - self.beg)

            if not os.path.isabs(self.Edit_Save.text()): #不是绝对路径不合法
                QMessageBox.critical(self, "错误",
                                     self.tr("保存路径不合法!"))
                return
            elif not os.path.exists(self.Edit_Save.text()):
                try:
                    os.mkdir(self.Edit_Save.text())
                except Exception as e:
                    QMessageBox.critical(self, "错误",
                                         self.tr("保存路径不合法!"))
                    return

            if not os.path.isabs(self.Edit_PDB.text()): #不是绝对路径不合法
                QMessageBox.critical(self, "错误",
                                     self.tr("PDB路径不合法!"))
                return
            elif not os.path.exists(self.Edit_PDB.text()):
                try:
                    os.mkdir(self.Edit_PDB.text())
                except Exception as e:
                    QMessageBox.critical(self, "错误",
                                         self.tr("PDB路径不合法!"))
                    return

            self.threads.clear() #每次更新参数杀死所有线程
            self.close()

    def Run(self):

        print("Download dialog is running!")

        if self.beg < 0 or self.end < 0 or self.end < self.beg:
            return False
        if self.Edit_URL.text() == '' or self.Edit_Save == '':
            return False
        os.chdir(self.Edit_Save.text())

        global finished_num
        finished_num = 0

        num_each = int((self.end+1 - self.beg)/self.threadnum)
        parent = self.parentWidget()
        if len(self.threads) == 0:
            for i in range(1, 1+self.threadnum):
                #print('i:'+str(i)+' beg')
                beg = self.beg + (i-1)*num_each
                end = self.beg + i*num_each
                if i == self.threadnum:
                    end = self.end+1

                mythread = MyThread(i, self.Edit_URL.text(), beg, end, parent.ProgressDlg, 'thread'+str(i))
                #print('i:'+str(i)+' end')
                self.threads.append(mythread)
                print("creating new thread")
        else:
            flag = True
            for thread in self.threads:
                if thread.isRunning():
                    flag = False
                    break
            if flag == False:
                message = ''
                for thread in self.threads:
                    name = thread.name
                    #print(name)
                    status = None
                    if thread.isRunning():
                        status = 'Running'
                    else:
                        status = 'Stopped'
                    #print(status)
                    message += name+':'+status+'\n'
                message +='请等待所有线程终止'
                print(message)
                QMessageBox.information(None, "警告", message, QMessageBox.Yes);
                return False

        # 开启线程
        global thread_flag
        thread_flag = 0
        for thread in self.threads:
            thread.start()
        return True

class AnalyzeDlg(QDialog):
    _signal = pyqtSignal(int, name='set_total')
    def __init__(self, parent=None):
        super(AnalyzeDlg, self).__init__(parent)
        self.threads = []
        self.beg = 0
        self.end = 0
        self.threadnum = 4
        Label_URL = QLabel("URL: ")
        Label_Beg = QLabel("起始: ")
        Label_End = QLabel("结束: ")
        Label_Total = QLabel("总计: ")
        self.Label_TotalNum = QLabel("0")
        Label_Save= QLabel("保存到: ")
        Label_PDB = QLabel("PDB目录: ")
        self.Edit_URL = QLineEdit()
        self.Edit_Beg = QLineEdit()
        self.Edit_End = QLineEdit()
        self.Edit_Save = QLineEdit()
        self.Edit_PDB = QLineEdit()
        self.Button_Skim1 = QPushButton("浏览")
        self.Button_Skim2 = QPushButton("浏览")
        self.Button_Ensure = QPushButton("确定")

        Label_URL.setFixedSize(40, 20)
        Label_Beg.setFixedSize(40, 20)
        Label_End.setFixedSize(40, 20)
        Label_Total.setFixedSize(40, 20)
        self.Label_TotalNum.setFixedSize(70, 20)
        self.Edit_Beg.setFixedSize(70, 20)
        self.Edit_End.setFixedSize(70, 20)

        Label_Save.setFixedSize(40, 20)
        Label_PDB.setFixedSize(40, 20)



        self.Button_Skim1.clicked.connect(self.Skim1)
        self.Button_Skim2.clicked.connect(self.Skim2)
        self.Button_Ensure.clicked.connect(self.Ensure)

        self.Edit_Beg.textChanged.connect(self.NumChanged)
        self.Edit_End.textChanged.connect(self.NumChanged)

        self._signal.connect(self.parentWidget().ProgressDlg.setTotalNum)
        Hlayout1 = QHBoxLayout()
        Hlayout1.addWidget(Label_URL)
        Hlayout1.addWidget(self.Edit_URL)
        Hlayout2 = QHBoxLayout()
        Hlayout2.addWidget(Label_Beg)
        Hlayout2.addWidget(self.Edit_Beg)
        Hlayout2.addWidget(Label_End)
        Hlayout2.addWidget(self.Edit_End)
        Hlayout2.addWidget(Label_Total)
        Hlayout2.addWidget(self.Label_TotalNum)

        Vlayout1 = QVBoxLayout()
        Vlayout1.addLayout(Hlayout1)
        Vlayout1.addLayout(Hlayout2)

        Hlayout3 = QHBoxLayout()
        Hlayout3.addWidget(Label_Save)
        Hlayout3.addWidget(self.Edit_Save)
        Hlayout3.addWidget(self.Button_Skim1)
        Hlayout4 = QHBoxLayout()
        Hlayout4.addWidget(Label_PDB)
        Hlayout4.addWidget(self.Edit_PDB)
        Hlayout4.addWidget(self.Button_Skim2)

        Vlayout2 = QVBoxLayout()
        Vlayout2.addLayout(Hlayout3)
        Vlayout2.addLayout(Hlayout4)

        Hlayout4 = QHBoxLayout()
        Hlayout4.addStretch()
        Hlayout4.addWidget(self.Button_Ensure)
        Hlayout4.addStretch()

        Vlayout = QVBoxLayout()
        Vlayout.addLayout(Vlayout1)
        Vlayout.addLayout(Vlayout2)
        Vlayout.addLayout(Hlayout4)
        Vlayout.addStretch()
        Vlayout.setSpacing(20)

        self.setLayout(Vlayout)
        # okBtn.clicked.connect(self.accept)
        self.setWindowTitle("下载")
        self.resize(200, 400)

        global finished_num
        finished_num = 0

    def Skim1(self):
        url = QFileDialog.getExistingDirectory(self, "选择文件夹",
                                                  "/home",
                                               QFileDialog.ShowDirsOnly
                                                  | QFileDialog.DontResolveSymlinks)
        self.Edit_Save.setText(url)

    def Skim2(self):
        url = QFileDialog.getExistingDirectory(self, "选择文件夹",
                                                  "/home",
                                               QFileDialog.ShowDirsOnly
                                                  | QFileDialog.DontResolveSymlinks)
        self.Edit_PDB.setText(url)


    def NumChanged(self):
        beg = self.Edit_Beg.text()
        end = self.Edit_End.text()
        try:
            if beg == "":
                self.beg = 0
            else:
                self.beg = int(beg)
            if end == "":
                self.end = 0
            else:
                self.end = int(end)
            #print(beg)
            #print(end)
            self.Label_TotalNum.setText(str(self.end+1 - self.beg))
        except ValueError:
            self.Label_TotalNum.setText("字符不合法")

    def Ensure(self):
        if self.Edit_URL.text() == '':
            QMessageBox.critical(self, "错误",
                                 self.tr("URL不能为空!"))
        elif self.beg < 0 or self.end < 0 or self.end < self.beg:
            QMessageBox.critical(self, "错误",
                                 self.tr("文件索引号错误!"))
        elif self.Edit_Save.text() == '':
            QMessageBox.critical(self, "错误",
                                 self.tr("保存路径不能为空!"))
        elif self.Edit_PDB.text() == '':
            QMessageBox.critical(self, "错误",
                                 self.tr("PDB目录不能为空!"))
        else:
            if self.parentWidget().ProgressDlg:
                self._signal.emit(self.end+1 - self.beg)

            if not os.path.isabs(self.Edit_Save.text()): #不是绝对路径不合法
                QMessageBox.critical(self, "错误",
                                     self.tr("保存路径不合法!"))
                return
            elif not os.path.exists(self.Edit_Save.text()):
                try:
                    os.mkdir(self.Edit_Save.text())
                except Exception as e:
                    QMessageBox.critical(self, "错误",
                                         self.tr("保存路径不合法!"))
                    return

            if not os.path.isabs(self.Edit_PDB.text()): #不是绝对路径不合法
                QMessageBox.critical(self, "错误",
                                     self.tr("PDB路径不合法!"))
                return
            elif not os.path.exists(self.Edit_PDB.text()):
                try:
                    os.mkdir(self.Edit_PDB.text())
                except Exception as e:
                    QMessageBox.critical(self, "错误",
                                         self.tr("PDB路径不合法!"))
                    return

            self.threads.clear() #每次更新参数杀死所有线程
            self.close()

    def Run(self):

        if self.beg < 0 or self.end < 0 or self.end < self.beg:
            return False
        if self.Edit_URL.text() == '' or self.Edit_Save == '':
            return False
        os.chdir(self.Edit_Save.text())


        global finished_num
        finished_num = 0


        num_each = int((self.end+1 - self.beg)/self.threadnum)
        parent = self.parentWidget()
        if len(self.threads) == 0:
            for i in range(1, 1+self.threadnum):
                #print('i:'+str(i)+' beg')
                beg = self.beg + (i-1)*num_each
                end = self.beg + i*num_each
                if i == self.threadnum:
                    end = self.end+1

                mythread = MyThread(i, self.Edit_URL.text(), beg, end, parent.ProgressDlg, 'thread'+str(i))
                #print('i:'+str(i)+' end')
                self.threads.append(mythread)
        else:
            flag = True
            for thread in self.threads:
                if thread.isRunning():
                    flag = False
                    break
            if flag == False:
                message = ''
                for thread in self.threads:
                    name = thread.name
                    #print(name)
                    status = None
                    if thread.isRunning():
                        status = 'Running'
                    else:
                        status = 'Stopped'
                    #print(status)
                    message += name+':'+status+'\n'
                message +='请等待所有线程终止'
                print(message)
                QMessageBox.information(None, "警告", message, QMessageBox.Yes);
                return False

        # 开启线程
        global thread_flag
        thread_flag = 0
        for thread in self.threads:
            thread.start()
        return True


class ExitDlg(QDialog):
    #d
    def __init__(self, threads=None, parent=None):
        super(ExitDlg, self).__init__(parent)
        self.Label_Message = QLabel('正在等待线程退出')
        self.Bar_Progress = QProgressBar()
        self.Bar_Progress.setFixedSize(250, 20)
        self.Bar_Progress.setMaximum(len(threads))
        self.Bar_Progress.setValue(0)
        self.Timer = QTimer()
        self.Timer.timeout.connect(self.checkThread)
        self.Timer.start(1000)
        self.RunningThreads = threads

        Hlayout1 = QHBoxLayout()
        Hlayout1.addStretch()
        Hlayout1.addWidget(self.Label_Message)
        Hlayout1.addStretch()

        Hlayout2 = QHBoxLayout()
        Hlayout2.addStretch()
        Hlayout2.addWidget(self.Bar_Progress)
        Hlayout2.addStretch()

        Vlayout = QVBoxLayout()
        Vlayout.addStretch()
        Vlayout.addLayout(Hlayout1)
        Vlayout.addLayout(Hlayout2)
        Vlayout.addStretch()

        self.setWindowTitle('等待')
        self.setLayout(Vlayout)
        self.resize(400, 80)

    def checkThread(self):
        parent = self.parentWidget()
        flag = True
        for thread in self.RunningThreads:
            if thread.isRunning():
                print("a thread is running")
                flag = False
            else:
                self.Bar_Progress.setValue(self.Bar_Progress.value()+1)
                self.RunningThreads.remove(thread)

        if flag == True:
            print('killing timer')
            self.Timer.killTimer()
            # self.Timer.
            self.close()

    def closeEvent(self, QCloseEvent):  #忽略强制退出消息，必须线程结束才退出
        QCloseEvent.ignore()


class ProgressDlg(QDialog):
    def __init__(self, parent=None):
        super(ProgressDlg, self).__init__(parent)
        self.TotalNum = 0
        Label_Download = QLabel('正在下载')
        self.Label_FileName = QLabel('')
        self.Bar_Progress = QProgressBar()
        global finished_num
        self.Label_FinishedNum = QLabel(str(finished_num)+'/'+ str(self.TotalNum))
        self.Button_Cancel = QPushButton('取消')
        self.Bar_Progress.setMinimum(0)
        self.Bar_Progress.setMaximum(self.TotalNum)

        self.Button_Cancel.clicked.connect(self.cancel)

        Hlayout1 = QHBoxLayout()
        Hlayout1.addWidget(Label_Download)
        Hlayout1.addWidget(self.Label_FileName)

        Hlayout2 = QHBoxLayout()
        Hlayout2.addWidget(self.Bar_Progress)
        Hlayout2.addWidget(self.Label_FinishedNum)

        Vlayout = QVBoxLayout()
        Vlayout.addStretch()
        Vlayout.addLayout(Hlayout1)
        Vlayout.addLayout(Hlayout2)
        Vlayout.addWidget(self.Button_Cancel)
        Vlayout.addStretch()
        Vlayout.setSpacing(20)

        self.setWindowTitle('下载')
        self.setLayout(Vlayout)
        self.resize(500, 200)

    def refresh(self, filename):
        parent = self.parentWidget()
        totalnum = parent.DownLoadDlg.end+1 - parent.DownLoadDlg.beg
        global finished_num
        self.Label_FinishedNum.setText(str(finished_num)+'/'+str(self.TotalNum))
        self.Bar_Progress.setValue(finished_num)
        self.Label_FileName.setText(filename)
        if finished_num == self.TotalNum:
            print(1)
            self.close()

    def setTotalNum(self, num):
        num = int(num)
        self.TotalNum = num
        self.Bar_Progress.setMaximum(self.TotalNum)

    def cancel(self):
        global thread_flag
        thread_flag = 2
        self.close()

    def closeEvent(self, QCloseEvent):
        global thread_flag
        thread_flag = 2
        if finished_num == self.TotalNum:
            QMessageBox.information(None,'提示','下载完毕',QMessageBox.Yes)
        QCloseEvent.accept() #关闭窗口之前设置标志位结束线程


class MainDlg(QDialog):
    def __init__(self, parent=None):
        super(MainDlg, self).__init__(parent)

        self.ProgressDlg = ProgressDlg(self)
        self.DownLoadDlg = DownLoadDlg(self)
        self.AnalyzeDlg = AnalyzeDlg(self)
        # self.ProgressDlg = None
        # self.DownLoadDlg = None
        # self.AnalyzeDlg = None

        Button_Download = QPushButton("使用Http下载文件并分析")
        Button_Analyze  = QPushButton("导入本地文件分析")
        Button_Progress = QPushButton("显示任务进度")
        Button_Start = QPushButton("开始")
        Button_Pause = QPushButton("暂停")
        Button_Close = QPushButton("关闭")

        Button_Download.setFixedSize(150, 30)
        Button_Analyze.setFixedSize(150, 30)
        Button_Progress.setFixedSize(150, 30)
        Button_Start.setFixedSize(150, 30)
        Button_Pause.setFixedSize(150, 30)
        Button_Close.setFixedSize(150, 30)

        Button_Download.clicked.connect(self.download)
        Button_Start.clicked.connect(self.start)
        Button_Analyze.clicked.connect(self.analyze)

        TableWidget_Data = QTableWidget()
        TableWidget_Data.setColumnCount(2)
        #TableWidget_Data.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) #设置列等宽
        TableWidget_Data.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch);
        TableWidget_Data.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents);
        TableWidget_Data.resizeColumnToContents(0)
        TableWidget_Data.setHorizontalHeaderLabels(['dll', '次数'])

        for i in range(0, 20):
            TableWidget_Data.insertRow(i)
        for i in range(0, 20):
            item0 = QTableWidgetItem("123456789")
            item1 = QTableWidgetItem("1")
            TableWidget_Data.setItem(i, 0, item0)
            TableWidget_Data.setItem(i, 1, item1)

        TableWidget_Data1 = QTableWidget()
        TableWidget_Data1.setColumnCount(2)
        # TableWidget_Data.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) #设置列等宽
        TableWidget_Data1.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch);
        TableWidget_Data1.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents);
        TableWidget_Data1.resizeColumnToContents(0)
        TableWidget_Data1.setHorizontalHeaderLabels(['dll', '次数'])

        for i in range(0, 20):
            TableWidget_Data1.insertRow(i)
        for i in range(0, 20):
            item0 = QTableWidgetItem("123456789")
            item1 = QTableWidgetItem("1")
            TableWidget_Data1.setItem(i, 0, item0)
            TableWidget_Data1.setItem(i, 1, item1)

        TableWidget_Data2 = QTableWidget()
        TableWidget_Data2.setColumnCount(2)
        # TableWidget_Data.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) #设置列等宽
        TableWidget_Data2.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch);
        TableWidget_Data2.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents);
        TableWidget_Data2.resizeColumnToContents(0)
        TableWidget_Data2.setHorizontalHeaderLabels(['dll', '次数'])

        for i in range(0, 20):
            TableWidget_Data2.insertRow(i)
        for i in range(0, 20):
            item0 = QTableWidgetItem("123456789")
            item1 = QTableWidgetItem("1")
            TableWidget_Data2.setItem(i, 0, item0)
            TableWidget_Data2.setItem(i, 1, item1)

        Hlayout1 = QHBoxLayout()
        Hlayout1.addWidget(Button_Download)
        Hlayout1.addWidget(Button_Analyze)

        Hlayout2 = QHBoxLayout()
        Hlayout2.addWidget(Button_Start)

        Hlayout3 = QHBoxLayout()
        Hlayout3.addWidget(TableWidget_Data)
        Hlayout3.addWidget(TableWidget_Data1)
        Hlayout3.addWidget(TableWidget_Data2)
        Hlayout3.setSpacing(10)

        Vlayout = QVBoxLayout()
        Vlayout.addLayout(Hlayout1)
        Vlayout.addLayout(Hlayout2)
        Vlayout.addLayout(Hlayout3)
        Vlayout.setSpacing(60)

        self.setLayout(Vlayout)
        self.setWindowTitle("登录")
        self.resize(800, 400)

    def download(self):
        self.DownLoadDlg.exec_()

    def analyze(self):
        self.AnalyzeDlg.exec_()

    def start(self):

        if self.DownLoadDlg.Run():
            self.ProgressDlg.show()
        else:
            QMessageBox.critical(self, "错误",
                                 self.tr("请先设置各项参数!"))

    def closeEvent(self, QCloseEvent):
        exitdlg = ExitDlg(threads=self.DownLoadDlg.threads, parent=self)
        exitdlg.exec_()


class MyThread(QThread):
    _signal = pyqtSignal(str)

    def __init__(self, threadID, url, beg, end, targetdlg=None, name=''):
        super(MyThread, self).__init__()
        self.threadID = threadID
        self.name = name
        self._url = url
        self._beg = beg
        self._end = end
        self._targetdlg = targetdlg
        self._signal.connect(self._targetdlg.refresh)

    def run(self):
        print("Starting " + self.name)
        global finished_num
        index = self._beg
        while index < self._end:
            # 终止线程
            global thread_flag
            #print('thread_flag:' + str(thread_flag))
            if thread_flag == 2:
                break
            url = self._url + 'error_report_' + str(index) + '.zip'
            filename = 'error_report_' + str(index) + '.zip'
            if os.path.exists(filename):
                #print(filename + ' is exsit')
                finished_num += 1
            else:
                self._signal.emit(filename)
                try:
                    urllib.request.urlretrieve(url, filename)
                except Exception as e:
                    #print('in the exception')
                    if os.path.exists(filename):  #出现异常文件都要删除
                        try:
                            os.remove(filename)
                        except Exception as e:
                            print(e)
                    if hasattr(e, 'code') and e.code != None:  #HTTPError
                        filename += ':HTTPError'
                    elif hasattr(e, 'errno') and e.errno != None:
                            index -= 1  # 重新下载
                            filename += ':现有连接断开'
                    elif hasattr(e, 'reason') and e.reason != None: #无法建立连接
                        index -= 1  # 重新下载
                        filename += ':无法建立连接'
                    else:
                        filename += ":下载异常"

                    self._signal.emit(filename)
                else:
                    finished_num += 1
                    self._signal.emit(filename)
            index += 1
            # print('id =' + str(self.threadID)+ 'i='+str(i) + ' finishe_num:'+ str(finished_num))
        print("Exiting " + self.name)


app = QApplication(sys.argv)
dlg = MainDlg()
# dlg.show()
dlg.exec_()
app.exit()

# dlg = ExitDlg()
# dlg.exec_()
# app.exit()

#http://222.73.55.231/BugTrap/reports/swcSelf8.8.7/