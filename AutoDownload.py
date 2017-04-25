import time
import urllib.request
import os
from os.path import basename
import shutil
import re
import zipfile
import logging
import xml.etree.ElementTree as ET
import ctypes
import threading

import Initialize
import IOHelper
from IOHelper import write_information
import analyze

# public
probe_dll = None    # dll
load_dump = None    # function
pdb_path = None


class Fetcher:
    '''
    Duty: handle the task include but not limit to: download, unzip and analyze.
    Notice: Analysis result are saved to the same directory of .dmp file.
            Summarize the data and making final report will be done by another class
    '''
    def __init__(self, thread_id, conf, md):
        super().__init__()
        self.thread_id = thread_id
        self.url_base = conf.url
        self.zip_folder = conf.zip_folder       # reports/zip/
        self.unzip_folder = conf.unzip_folder   # reports/unzip/
        self.dump_name = conf.dump_name         # crashdump.dmp
        self.dump_xml = conf.dump_xml           # dmp.xml

        self.zip_path = ''      # reports/zip/error_report_xxx.zip
        self.unzip_dir = ''     # reports/unzip/error_report_xxx

        self.status_valid = True  # status is invalid when there exist file that can not be removed
        self.num_succeed = 0

        self.conf = conf
        self.md = md

    def process(self, report_id):
        #
        dfn = IOHelper.DumpFileName(self.conf)
        filename = dfn.zip_name_from_id(report_id)

        self.zip_path = os.path.join(self.zip_folder, filename)
        self.unzip_dir = os.path.join(self.unzip_folder, filename.split('.')[0])
        dmp_path = os.path.join(self.unzip_dir, self.dump_name)
        xml_path = os.path.join(self.unzip_dir, self.dump_xml)

        self.remove_overdue(self.zip_path, self.unzip_dir, xml_path)

        self.status_valid = True    # will be modified in self.remove_file

        # try to download
        res = self.try_download(filename, self.zip_path)
        if not self.status_valid:
            self.status_valid = True
            return False
        if not res:
            return False

        # try to unzip
        res = self.try_unzip(filename, self.zip_path, self.unzip_dir)
        if not self.status_valid:
            self.status_valid = True
            return False
        if not res:
            return False

        # try to analyze
        res = self.try_analyze(filename, self.zip_path, self.unzip_dir, dmp_path, xml_path)
        if not self.status_valid:
            self.status_valid = True
            return False
        if not res:
            return False

        return True

    def remove_overdue(self, zip_path, unzip_path, dmp_path):
        '''
        文件依赖关系,->表示依赖于
            unzip   --> zip
            dmp     ->  unzip
        如果文件（文件夹）的依赖项不存在，则移除当前文件（文件夹）
        '''
        if not os.path.exists(self.zip_path) and os.path.exists(unzip_path):
            self.remove_file(unzip_path)
        if not os.path.exists(unzip_path) and os.path.exists(dmp_path):
            self.remove_file(dmp_path)

    def remove_file(self, file_path):
        """
        带有日志和异常处理的文件删除辅助函数
        :param file_path: 
        :return: 
        """
        try:
            if os.path.exists(file_path):
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    shutil.rmtree(file_path)
            return True
        except os.error as e:
            self.status_valid = False
            write_information("remove failed! %s" % file_path, self.thread_id)
            return False

    def remove_temps(self):
        """
        解压分析过后，删除原始zip文件。dmp文件也是临时文件，
        不过会等到分析阶段结束和xml文件及其所在文件夹一起删除
        :return: 
        """
        self.remove_file(self.unzip_dir)
        self.remove_file(self.zip_path)

    def try_download(self, filename, zip_path):
        #
        ret = True
        if not os.path.exists(zip_path):
            url = self.url_base + filename
            write_information('[downloading]:\t%s' % filename, self.thread_id)
            try:
                req = urllib.request.urlopen(url)
                data = req.read()
                with open(zip_path, 'wb') as f:
                    f.write(data)
            except Exception as e:
                # download exception, delete files
                write_information('[download error]:\t%s ' % filename, self.thread_id)
                if os.path.exists(zip_path):
                    self.remove_file(zip_path)  # if no dirty file is stored, status is acceptable
                ret = False
        return ret

    def try_unzip(self, filename, zip_path, unzip_path):
        #
        ret = True
        if os.path.exists(zip_path) and not os.path.exists(unzip_path):
            try:
                z = zipfile.ZipFile(zip_path, 'r')
                if self.dump_name in z.namelist():
                    write_information("[unziping]\t%s " % filename, self.thread_id)
                    z.extract(self.dump_name, unzip_path)
            except Exception as e:
                # unzip exception, delete files
                write_information('[unzip error]:\t%s ' % zip_path, self.thread_id)
                if os.path.exists(zip_path):
                    self.remove_file(unzip_path)
                if os.path.exists(unzip_path):
                    self.remove_file(unzip_path)
                ret = False
        return ret

    def try_analyze(self, filename, zip_path, unzip_path, dmp_path, xml_path):
        #
        if os.path.exists(xml_path):
            return True
        if not os.path.exists(unzip_path):
            return True

        write_information("[trying analyze] %s" % dmp_path, self.thread_id)

        f1 = ctypes.c_char_p(dmp_path.encode('gb2312'))
        f2 = ctypes.c_char_p(pdb_path.encode('gb2312'))
        info_buf = ctypes.create_string_buffer(128000)

        # load dump info through DLL
        ret = load_dump(f1, f2, info_buf)
        if 0 == ret:
            write_information("[load dump]: succeed!", self.thread_id)

            # convert info into python xml format
            info = info_buf.value.decode('utf-8')
            # print(info)
            dumpXML = ET.ElementTree(ET.fromstring(info))
            dumpXML.write(xml_path, 'utf-8')
            return True

        write_information("[load dump]: failed!", self.thread_id)
        return False


class Analyzer:
    def __init__(self, thread_id, conf, md):
        self.thread_id = thread_id
        self.conf = conf
        self.md = md

    def process_server(self, report_id):
        ao = analyze.AnalyzeOne(self.thread_id, self.conf, self.md)
        ao.prepare(report_id)
        ao.process(self.conf.invalid_records)

        return True


class JobHandler(threading.Thread):
    def __init__(self):
        super().__init__()
        self.thread_id = -1
        self.report_list = []

        self.repeat = 0
        self.num_succeed = 0

        # 全局配置参数
        self.conf = None
        self.md = None

        self.remove_after_use = False

    def set_param(self, thread_id, report_list, conf, md, remove_after_use=False):
        self.thread_id = thread_id
        self.report_list = report_list

        self.repeat = 0
        self.num_succeed = 0

        self.conf = conf
        self.md = md

        self.remove_after_use = remove_after_use

    def run(self):
        write_information('is running', self.thread_id)
        fe = Fetcher(self.thread_id, self.conf, self.md)
        an = Analyzer(self.thread_id, self.conf, self.md)

        #
        idx = 0
        nums = len(self.report_list)
        while idx < nums:
            report_id = self.report_list[idx]   # 当前报告编号
            idx += 1

            # 下载、解压、获取崩溃堆栈
            fe_ret = fe.process(report_id)
            # if not fe_ret:                     # 然后判断执行是否成功
            #     continue

            # 分析、归类(仅服务器模式)
            if not self.conf.client_mode:
                an_ret = an.process_server(report_id)

                # if not an_ret:                 # 然后判断执行是否成功
                #     continue

            if self.remove_after_use:   # 先清理当前步骤的临时文件
                fe.remove_temps()

            if fe_ret:  # 第一步骤成功
                if self.conf.client_mode or \
                        (not self.conf.client_mode and an_ret):     # 第二步骤不需要或者不成功
                    self.num_succeed += 1


class JobAssigner:
    def __init__(self, conf, md):
        self.url_base = conf.url
        self.zip_dir = conf.zip_folder

        self.beg_idx = conf.idx_beg
        self.end_idx = conf.idx_end

        self.thread_num = conf.thread_num

        self.report_list = []
        self.conf = conf
        self.md = md

    def get_classified_file(self):
        report_list = []
        dfn = IOHelper.DumpFileName(self.conf)
        for root, dirs, files in os.walk(self.conf.classified_folder):
            for file in files:
                if file.startswith(self.conf.folder_prefix) and file.endswith(".zip"):
                    report_list.append(dfn.get_report_id(file.split('.')[0]))

        print('totally %d classified files' % len(report_list))
        return sorted(report_list)

    def get_file_list(self, thread_num, beg_idx, end_idx, enquire_webpage=False, ignore_classified=False):
        #
        self.thread_num = thread_num
        self.beg_idx = beg_idx
        self.end_idx = end_idx

        if not enquire_webpage:
            self.report_list = [id for id in range(self.beg_idx, self.end_idx)]
        else:
            self.report_list = self.parse_webpage(self.url_base, self.beg_idx, self.end_idx)

        # 服务端模式下，忽略已归类文件夹
        if ignore_classified:
            exclude_list = self.get_classified_file()

            # info = IOHelper.list_to_str(exclude_list)
            # write_information("--exclude-------------------------------------------------------")
            # write_information(info)

            # info = IOHelper.list_to_str(self.report_list)
            # write_information("--report list 1-------------------------------------------------------")
            # write_information(info)

            self.report_list = list(set(self.report_list) - set(exclude_list))

        self.report_list.sort()

        # info = IOHelper.list_to_str(self.report_list)
        # write_information("--report list 2-------------------------------------------------------")
        # write_information(info)

    def go(self, thread_num, beg_idx, end_idx, enquire_webpage=False, ignore_classified=False, remove_after_use=False):
        #
        self.get_file_list(thread_num, beg_idx, end_idx, enquire_webpage, ignore_classified)
        # JobAssigner.delete_files(self.zip_dir, self.report_list, self.conf)

        write_information('totally [%d] files to proceed, thread number %d'
                          % (len(self.report_list), self.thread_num))

        #
        thread_file_list = [[] for i in range(self.thread_num)]
        for idx in range(len(self.report_list)):
            thread_file_list[idx % self.thread_num].append(self.report_list[idx])
            idx += 1

        threads = []
        for i in range(self.thread_num):
            jh = JobHandler()
            jh.set_param(i, thread_file_list[i], self.conf, self.md, remove_after_use=remove_after_use)
            threads.append(jh)

            # print(thread_file_list[i])

        for i in range(self.thread_num):
            threads[i].start()

        for i in range(self.thread_num):
            threads[i].join()

    @staticmethod
    def parse_webpage(url_base, start_idx, end_idx):
        # download webpages
        try:
            vd = IOHelper.VisualizeDownload(url_base)
            page_info = vd.go()
        except Exception as e:
            write_information("failed to get web page!")
            return []

        # decode to utf-8
        page_info = page_info.decode('utf-8')
        # print(page_info)

        # find all report names
        p_name = re.compile(r'>(error_report_([\d]*).zip)<')
        id_list = p_name.findall(page_info)  # currently unsorted
        # print(id_list)
        id_list = sorted(id_list, key=lambda x: x[1])
        write_information('totally <%d> files found on server, ranging from %s to %s'
                          % (len(id_list), id_list[0][1], id_list[-1][1]))

        # create file list
        new_id_list = []
        for report in id_list:
            idx = int(report[1])
            if start_idx >= 0 and idx < start_idx:
                continue
            if end_idx >= 0 and idx > end_idx:
                continue
            new_id_list.append(idx)
        return new_id_list

    # @staticmethod
    # def delete_files(zip_dir, id_list, conf):
    #     #
    #     dfn = IOHelper.DumpFileName(conf)
    #     file_list = dfn.zip_list_from_id_list(id_list)
    #
    #     for file_path in os.listdir(zip_dir):
    #         filename = basename(file_path)
    #         if os.path.exists(file_path) and filename not in file_list:
    #             write_information('[removing]:\t%s' % (zip_dir + "\\" + file_path))
    #             os.remove(zip_dir + "\\" + file_path)


def prepare_symbol(conf):
    return os.path.exists(conf.symbol_folder)


def prepare_dll(conf):
    global probe_dll
    global load_dump
    global pdb_path
    probe_dll = ctypes.CDLL(conf.dumpload_dll)
    if not probe_dll:
        return False

    load_dump = probe_dll['load_dump']
    load_dump.restype = ctypes.c_int
    if not load_dump:
        return False

    pdb_path = conf.symbol_folder
    return True


def download_analyze(conf, md, repeat_num=-1, interval=5, ignore_classified=False, remove_after_use=False):
    # if not prepare_log(conf):
    #     write_information('prepare log failed!')
    #     return

    if not prepare_dll(conf):
        write_information('prepare dll failed!')
        write_information('dll path: %s' % conf.dumpload_dll)
        return

    if not prepare_symbol(conf):
        write_information('prepare symbol failed!')
        write_information('symbol path: %s' % conf.symbol_folder)
        return

    js = JobAssigner(conf, md)

    write_information('system started...')
    count = 0
    while True:
        if 0 < repeat_num and repeat_num <= count:
            break
        if count > 99990:
            count = 0
        write_information("<The %s time>" % count)
        count += 1
        js.go(conf.thread_num, conf.idx_beg, conf.idx_end,
              enquire_webpage=conf.retrieve_webpage,
              ignore_classified=ignore_classified,
              remove_after_use=remove_after_use)
        time.sleep(interval)

    return js.report_list


def main():
    # configuration
    conf = Initialize.Conf()
    conf.load(r'data\config.json')

    # module define
    md = Initialize.MD()
    md.load(conf.module_define)

    download_analyze(conf, md)


if __name__ == '__main__':
    main()