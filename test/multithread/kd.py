# import pykd
import threading

dmp = "E:\\dmp\\data\\flat\\error_report_3010\\crashdump.dmp"
sym = "E:\\dmp\\swc_free_bin_4055\\bin\\release"

# pykd.initialize()
# pykd.setSymbolPath(sym)


class myThread (threading.Thread):   #继承父类threading.Thread
    def __init__(self, ID, dmp):
        threading.Thread.__init__(self)
        self.ID = ID
        self.dmp = dmp

    def run(self):                   #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("Starting " + str(self.ID))
        self.go(self.dmp)
        print("Exiting " + str(self.ID))

    def go(self, dmp):
        # pykd.loadDump(dmp)
        # s = pykd.dbgCommand('!analyze -v')
        # print(s[:300])
        # pykd.deinitialize()
        print(self.ID, 'is working')


if __name__ == "__main__":
    t1 = myThread(1, dmp)
    t1.start()
    t1.join()