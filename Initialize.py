import json
import codecs
import os
import copy
import IOHelper


class Conf:
    def __init__(self):
        #
        self.data = None
        
        # download
        self.url = ''
        self.idx_beg = 0
        self.idx_end = 0
        self.url_symbol = ''

        # path
        self.dumpload_dll = ''
        self.module_define = ''
        self.invalid_define = ''
        self.xls = ''
        self.symbol_folder = ''
        self.folder_prefix = ''
        self.dump_name = ''
        self.dump_xml = ''
        self.dump_folder = ''
        self.report_folder = ''
        self.zip_folder = ''
        self.unzip_folder = ''
        self.classified_folder = ''

        # class
        self.clas_include = []
        self.clas_exclude = []

        # zip
        self.num_zip_move = 0
        self.num_zip_extract = 0

        # other
        self.thread_num = 1
        self.repeat_num = 1
        self.client_mode = True
        self.retrieve_webpage = False
        self.off_line = False
        self.write_ini = True

        # additional
        self.invalid_records = []

    def to_str(self):
        str = "配置参数如下:\n\t"
        str += "url: %s" % self.url + "\n\t"
        str += "idx_beg: %d" % self.idx_beg + "\n\t"
        str += "idx_end: %d" % self.idx_end + "\n\t"
        str += "url_symbol: %s" % self.url_symbol + "\n\t"

        str += "dumpload_dll: %s" % self.dumpload_dll + "\n\t"
        str += "module_define: %s" % self.module_define + "\n\t"
        str += "invalid_define: %s" % self.invalid_define + "\n\t"
        str += "xls: %s" % self.xls + "\n\t"
        str += "symbol_folder: %s" % self.symbol_folder + "\n\t"
        str += "folder_prefix: %s" % self.folder_prefix + "\n\t"
        str += "dump_name: %s" % self.dump_name + "\n\t"
        str += "dump_xml: %s" % self.dump_xml + "\n\t"
        str += "dump_folder: %s" % self.dump_folder + "\n\t"
        str += "report_folder: %s" % self.report_folder + "\n\t"
        str += "zip_folder: %s" % self.zip_folder + "\n\t"
        str += "unzip_folder: %s" % self.unzip_folder + "\n\t"
        str += "classified_folder: %s" % self.classified_folder + "\n"

        return str

    def load(self, fpath):
        file = codecs.open(fpath, 'r', 'utf-8')
        self.data = json.load(file)

        #
        self.url = self.data['download']['crash_report']['url']
        self.idx_beg = self.data['download']['crash_report']['idx_beg']
        self.idx_end = self.data['download']['crash_report']['idx_end']
        self.url_symbol = self.data['download']['symbol']['url']

        self.dumpload_dll = self.data["path"]["dumpload_dll"]
        self.module_define = self.data['path']['module_define']
        self.invalid_define = self.data['path']['invalid_define']
        self.xls = self.data['path']['xls']
        self.symbol_folder = self.data['path']['symbol_folder']
        self.folder_prefix = self.data['path']['folder_prefix']
        self.dump_name = self.data['path']['dump_name']
        self.dump_xml = self.data['path']['dump_xml']

        self.report_folder = self.data['path']['relative']['report_folder']
        self.zip_folder = self.data['path']['relative']['zip_folder']
        self.unzip_folder = self.data['path']['relative']['unzip_folder']
        self.classified_folder = self.data['path']['relative']['classified_folder']
        self.calc_folder()

        self.clas_include = self.data['filter']['class']['include']
        self.clas_exclude = self.data['filter']['class']['exclude']

        self.num_zip_move = self.data['zip']['num_move']
        self.num_zip_extract = self.data['zip']['num_extract']

        self.thread_num = self.data['other']['thread_num']
        self.repeat_num = self.data['other']['repeat_num']
        self.client_mode = self.data['other']['client_mode']
        self.retrieve_webpage = self.data['other']['retrieve_webpage']
        self.off_line = self.data['other']['off_line']
        self.write_ini = self.data['other']['write_ini']
        
    def calc_folder(self):
        if not os.path.isabs(self.zip_folder):
            # 如果zip_folder是相对路径, 为其拓展父路径report_folder，否则不作改变
            # report_folder / zip_folder
            self.zip_folder = os.path.join(self.report_folder, self.zip_folder)

        if not os.path.isabs(self.unzip_folder):
            # 如果unzip_folder是相对路径, 为其拓展父路径report_folder，否则不作改变
            # report_folder / unzip_folder
            self.unzip_folder = os.path.join(self.report_folder, self.unzip_folder)

        if not os.path.isabs(self.classified_folder):
            # 如果classified_folder是相对路径, 为其拓展父路径unzip_folder，否则不作改变
            # unzip_folder / classified_folder
            self.classified_folder = os.path.join(self.report_folder, self.classified_folder)


class MD:
    def __init__(self):
        # {module -> manager}
        self.module_map = {}
        self.module_list = []

        # {class -> manager}
        self.clas_map = {}

        # {manager -> module}
        self.manager_map = {}

    def load(self, jpath):
        # print(jpath)
        file = codecs.open(jpath, 'r', 'utf-8')

        total_map = json.load(file)

        self.module_map = total_map['module']
        self.module_list = list(self.module_map.keys())
        self.clas_map = total_map['class']

        for (module_name, module_detail) in self.module_map.items():
            for (class_name, manager_name) in module_detail.items():

                # update manager_map
                if not self.manager_map.get(manager_name):
                    self.manager_map[manager_name] = {}
                self.manager_map[manager_name][module_name] = {}

    def get_manager_dict(self):
        # print(self.manager_map)
        return copy.deepcopy(self.manager_map)

    def which_manager(self, module, clas):
        """
        find out manager of given infomation
        the class has higher priority!
        :param module:  module name, non-empty
        :param clas:    class name, ignored if empty
        :return: manager name
        """
        # [Step 1] search in global class dict
        if self.clas_map.get(clas):
            return self.clas_map[clas]

        # [Step 2] search in module dict
        # if class name is empty, rename it as 'main'
        if clas == '':
            clas = 'main'

        clas_dict = self.module_map[module]
        if clas_dict.get(clas):
            return clas_dict[clas]      # specified class in module
        else:
            return clas_dict['main']    # general class in module


class Invalid:
    def __init__(self):
        self.invalid_list = []

    def load(self, fpath):
        f = codecs.open(fpath, 'r', 'utf-8')
        for line in f.readlines():
            data = line.split()
            if len(data) < 3:
                continue

            record = IOHelper.xls_record()
            record.module = data[0]
            record.manager = data[1]
            record.line = data[2]
            self.invalid_list.append(record)

    def print(self):
        print("无效崩溃信息:")
        for record in self.invalid_list:
            IOHelper.write_information(
                record.module + " " + record.manager + " " + record.line)
