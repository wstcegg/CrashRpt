import threading
import time
import random
import re


class myThread (threading.Thread):   #继承父类threading.Thread
    def __init__(self, ID):
        threading.Thread.__init__(self)
        self.ID = ID

    def run(self):                   #把要执行的代码写到run函数里面 线程在创建后会直接运行run函数
        print("Starting " + str(self.ID))
        self.go()
        print("Exiting " + str(self.ID))

    def go(self):
        for i in range(1, 10):
            t = random.randint(1, 10)
            time.sleep(t)
            print('%d is working %d' %(self.ID, i))


if __name__ == "__main__":
    # t1 = myThread(1)
    # t2 = myThread(2)
    #
    # t1.start()
    # t2.start()
    #
    # t1.join()
    # t2.join()

    a = 'a_1, b_1, c_1'
    pat = re.compile(r'([\w]_(\d))')
    res = pat.findall(a)
    for r in res:
        print(r[1])