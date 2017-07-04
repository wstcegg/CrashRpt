import zipfile
import xlwt
import os
import ntpath
import shutil
import configparser
import urllib
import logging
import sys
from time import sleep


def list_to_str(data_list):
    s = ""
    for elem in data_list:
        s += " "
        s += str(elem)
    return s


def write_information(info, thread_id=-1):
    if thread_id >= 0:
        info = str('[thread %d] ' % thread_id) + info

    print(info)
    root_log = logging.getLogger('root')
    root_log.info(info)


class xls_record:
    def __init__(self):
        self.module = ''
        self.manager = ''
        self.line = ''
        self.num = 0
        self.remark = ''

        # error report list
        self.report_list = []

        # manual added info
        self.modify_code = 0
        self.modify_info = ''

        #
        self.update_folder = False

    def __str__(self):
        return self.to_str()

    def to_str(self):
        s = ''
        s += 'module: ' + self.module
        s += '\tmanager: ' + self.manager
        s += '\tline: ' + self.line
        s += '\tnum: ' + str(self.num)
        s += '\t report_list:['
        for report_idx in self.report_list:
            s += str(report_idx)
            s += ' '
        s += ']'
        return s

    def is_empty(self):
        return self.module == '' or self.manager == '' or self.line == ''

    def __lt__(self, other):
        #
        if self.manager != other.manager:
            return self.manager < other.manager
        elif self.module != other.module:
            return self.module < other.module
        else:
            return self.line < other.line

    def __eq__(self, other):
        # records are equal so long as module, manager and line are equal
        # two equal record with different report_lists will be merged!
        return self.module == other.module \
               and self.manager == other.manager\
               and self.line == other.line

    def merge(self, other):
        if self != other:
            print('merge xls record failed! keys not equal!')
            return
        self.update_folder = True
        self.num += other.num
        self.report_list.extend(other.report_list)

    def to_folder(self, base_folder=''):
        # print(self.manager, self.module, self.line)
        relative_path = self.manager + '\\' + self.module + '\\' + Naming.valid_name(self.line)
        return os.path.join(base_folder, relative_path)

    def to_vs_dbgstr(self):
        clas, func, idx = WinDbgNaming.get_clas_func_idx(self.line)
        str = VSDbgNaming.name_from_clas_func_idx(self.module, clas, func, idx)
        return str


class XLS:
    def __init__(self):
        self.ws = None
        self.style = None
        self.line_idx = -1

    def write_module(self,  record, mask, cell_style):
        if mask[0]:
            self.ws.write(self.line_idx, 0, record.module, cell_style)

    def write_manager(self, record, mask, cell_style):
        if mask[2]:
            self.ws.write(self.line_idx, 2, record.manager, cell_style)

    def write_line(self,  record, mask, cell_style):
        if mask[3]:
            self.ws.write(self.line_idx, 3, record.line, cell_style)

    def write_number(self, record, mask, cell_style):
        if mask[4]:
            self.ws.write(self.line_idx, 4, record.num, cell_style)

    def write_remark(self,  record, mask, cell_style):
        if mask[5]:
            self.ws.write(self.line_idx, 5, record.remark, cell_style)

    def write_mod_code(self, record, mask, cell_style):
        if mask[6]:
            self.ws.write(self.line_idx, 6, record.modify_code, cell_style)

    def write_mod_info(self,  record, mask, cell_style):
        if mask[7]:
            self.ws.write(self.line_idx, 7, record.modify_info, cell_style)

    def write_ws(self, ws, records, mask=[1]*8):
        #
        self.ws = ws
        self.ws.write(0, 0, '模块')
        self.ws.write(0, 1, '版本号')
        self.ws.write(0, 2, '负责人')
        self.ws.write(0, 3, '崩溃行')
        self.ws.write(0, 4, '次数')
        self.ws.write(0, 5, '备注')
        self.ws.write(0, 6, '.')
        self.ws.write(0, 7, '.')

        # font
        font = xlwt.Font()
        font.name = '宋体'
        font.height = 11 * 0x14
        font.bold = False

        # xls style
        cell_style = xlwt.XFStyle()
        cell_style.font = font

        self.line_idx = 0
        total_num = 0
        for i, record in enumerate(records):
            if i == 0 or records[i].module != records[i - 1].module:
                # fist record of a module non-empty
                self.line_idx += 1
                self.write_module(record, mask, cell_style)
                self.write_manager(record, mask, cell_style)

            self.write_line(record, mask, cell_style)     # non-empty
            self.write_number(record, mask, cell_style)   # non-empty
            self.write_remark(record, mask, cell_style)   # usually empty

            # this two items might be empty
            self.write_mod_code(record, mask, cell_style)
            self.write_mod_info(record, mask, cell_style)

            self.line_idx += 1
            total_num += record.num

        # write total number
        self.ws.write(self.line_idx + 1, 0, '总计', cell_style)
        self.ws.write(self.line_idx + 1, 4, total_num, cell_style)

        # column 3 has rich info that require broad width
        line_col = self.ws.col(3)
        line_col.width = 256 * 50

    def write(self, xls_name, records=[], modifications=[]):
        """
        write two workbook to Excel file:
            'data' & 'rule'
        """
        wb = xlwt.Workbook()

        print("records: size:", len(modifications))
        print(modifications)

        # write data
        ws = wb.add_sheet('东方财富通')
        #       0  1  2  3  4  5  6  7
        mask = [1, 1, 1, 1, 1, 1, 0, 0]
        self.write_ws(ws, records, mask)

        # write rule
        ws = wb.add_sheet('rule')
        #       0  1  2  3  4  5  6  7
        mask = [1, 0, 1, 1, 0, 0, 1, 1]
        self.write_ws(ws, modifications, mask)

        wb.save(xls_name)

    def with_color(self):

        import xlwt

        clr_idx_visited = 0x08 + 1

        book = xlwt.Workbook()

        # add new colour to palette and set RGB colour value
        xlwt.add_palette_colour("custom_colour", clr_idx_visited)
        xlwt.add_palette_colour("custom_colour2", clr_idx_visited + 1)
        book.set_colour_RGB(clr_idx_visited, 0, 0, 228)
        book.set_colour_RGB(clr_idx_visited + 1, 255, 0, 228)

        # now you can use the colour in styles
        sheet1 = book.add_sheet('Sheet 1')
        style = xlwt.easyxf('pattern: pattern solid, fore_colour custom_colour2')

        for i in range(10):
            for j in range(10):
                sheet1.write(i, j, 'Some text', style)

        book.save('test.xls')


class INI:
    @staticmethod
    def write(fname, report_list):    #
        file = open(fname, 'w')
        file.write('[ErrorCount]\n')
        file.write('nCount=%d\n' % len(report_list))
        file.write('[ErrorPackage]\n')

        for idx, report in enumerate(report_list):
            file.write('%d=error_report_%d.zip\n' % (idx+1, report))

    @staticmethod
    def load_error_package(fname):
        """
            load error packages from ini file
        :param fname: ini file name
        :return: error package list in form of report idx
                        [idx0, idx1,..., idxn]
        """
        # [ErrorCount]
        # nCount=2
        # [ErrorPackage]
        # 1=error_report_149953.zip
        # 2=error_report_149959.zip
        start_pos = len('error_report_')
        end_pos = len('.zip') * (-1)

        config = configparser.ConfigParser()
        config.read(fname)
        nums = int(config['ErrorCount']['nCount'])

        report_list = []
        for idx in range(1, nums + 1):
            report_name = config['ErrorPackage'][str(idx)]
            report_id = int(report_name[start_pos:end_pos])
            report_list.append(report_id)
        return report_list


class Naming:
    @staticmethod
    def remove_invalid_chars(s, invalid_chars):
        """remove invalid chars from string"""
        res = ''
        for c in s:
            if c in invalid_chars:
                res += '_'
            else:
                res += c
        return res

    @staticmethod
    def unique_given_chars(s, given_chars):
        """remove two adjacent same charactor"""
        res = '='
        for c in s:
            if c in given_chars and c == res[-1]:
                continue
            res += c
        return res[1:]

    @staticmethod
    def valid_line_name_helper(fname):
        """construct a valid file name through given name"""
        invalid_chars = r'\/:*？"<>|()'
        fname = Naming.remove_invalid_chars(fname, invalid_chars)

        given_chars = r'_'
        fname = Naming.unique_given_chars(fname, given_chars)

        return fname

    @staticmethod
    def valid_name(s):
        fname = Naming.valid_line_name_helper(s)
        return str(fname[:80]).strip()    # restrain max length less than 80

    @staticmethod
    def get_clas_func(s):
        """
        extract class and function name from given string
        :param s: structure as the symbol field from dump analyze:
                    class :: function
        :return:
        """
        s = s.strip()

        clas = ''
        func = s
        pos = s.find('::')
        if 0 <= pos <= len(s):
            clas = s[:pos]
            func = s[pos+2:]
        return clas, func


class WinDbgNaming(Naming):
    @staticmethod
    def get_clas_func_idx(s):
        """
        :param s:
            using Excel string structure
            class::function_idx
            CGlobalEnvLite::ReleaseObject_200
        :return:
        """
        pos = s.rfind('_')      # pos of last '_'
        clas, func = Naming.get_clas_func(s[:pos])
        idx = int(s[pos+1:].strip())

        return clas, func, idx

    @staticmethod
    def name_from_clas_func_idx(clas, func, idx):
        fname = ""
        if clas:
            fname += clas
            fname += '::'
        if func:
            fname += func
            fname += '_'
        fname += str(idx)

        return fname


class VSDbgNaming(Naming):
    @staticmethod
    def get_mod_clas_func_idx(s):
        """
        :param s:
            using vs string structure
            module.dll ! classname :: funcinfo 行 lineidx + 0x89 字节
            GlobalEnvironment.dll!CGlobalEnvLite::ReleaseObject()  行200 + 0x5 字节
        :return:
        """

        print(s)
        s = s.strip()
        pos1 = s.find('!')      # pos of '!'
        pos2 = s.find('行')      # pos of '行'

        module = VSDbgNaming.get_module(str(s[:pos1]))    # GlobalEnvironment.dll->GlobalEnvironment
        clas, func = Naming.get_clas_func(s[pos1+1:pos2])
        idx = VSDbgNaming.get_idx(s[pos2+1:])

        return module, clas, func, idx

    @staticmethod
    def get_module(s):
        return s.split('.')[0]

    @staticmethod
    def get_idx(s):
        pos = len(s)           # end pos of lineidx
        for i in range(len(s)):
            if s[i] < '0' or s[i] > '9':
                pos = i
                break
        idx = int(s[:pos])
        return idx

    @staticmethod
    def name_from_clas_func_idx(module, clas, func, idx):
        fname = module + '.dll!'

        if clas:
            fname += clas
            fname += '::'
        if func:
            fname += func
            fname += ' 行'
        fname += str(idx)

        return fname


class DumpFileName:
    def __init__(self, conf):
        self.folderprefix = conf.folder_prefix
        self.dumpname = conf.dump_name   #

    def folder_from_id(self, idx):
        return self.folderprefix + str(idx)

    def zip_name_from_id(self, idx):
        return self.folder_from_id(idx) + '.zip'

    def zip_list_from_id(self, beg_idx, end_idx):
        zip_list = []
        for idx in range(beg_idx, end_idx + 1):
            zip_list.append(self.zip_name_from_id(idx))
        return zip_list

    def zip_list_from_id_list(self, idx_list):
        zip_list = []
        for idx in idx_list:
            zip_list.append(self.zip_name_from_id(idx))
        return zip_list

    def dump_name_from_id(self, idx):
        folder = self.folder_from_id(idx)
        return os.path.join(folder, self.dumpname)

    def get_report_id(self, fname):
        # fname: error_report_22307
        # prefix:error_report_
        if len(fname) < len(self.folderprefix):
            return -1
        pos = len(self.folderprefix)
        return int(fname[pos:])


class FileMover:
    def __init__(self, config):
        self.config = config
        self.dfn = DumpFileName(self.config)

    def move(self, src_folder, dst_folder, idx_list):
        move_list = []
        for idx in idx_list:
            src = os.path.join(src_folder, self.dfn.zip_name_from_id(idx))
            dst = os.path.join(dst_folder, self.dfn.zip_name_from_id(idx))

            print("from %s\n to %s\n" % (src, dst))
            move_list.append((src, dst))

        self.move_files(move_list)
        return move_list

    @staticmethod
    def unzip_files(unzip_list):
        print('unziping files')
        for i, fname in enumerate(unzip_list):
            print("unziping: %d \t %s" % (i, fname))

            try:
                zip_file = zipfile.ZipFile(fname)

                unzip_dir = fname[:-4]
                if not os.path.isdir(unzip_dir):
                    os.mkdir(unzip_dir)
                    zip_file.extractall(unzip_dir + '\\')
                    zip_file.close()
            except Exception as e:
                print("unzip error")


    @staticmethod
    def move_files(move_list):
        print('moving files')
        for i, (src, dst) in enumerate(move_list):
            print("moving %d \n\t src: %s \n\t dst: %s" % (i, src, dst))
            shutil.copy2(src, dst)      # 复制文件修改时间等属性

    @staticmethod
    def remove_empty_dir(classified_folder):
        changed = True
        while changed:
            changed = False
            for root, dirs, files in os.walk(classified_folder):
                if not dirs and not files and root != classified_folder:
                    shutil.rmtree(root)
                    changed = True

    @staticmethod
    def remove_unzip_files(classified_folder, folder_prefix):
        for root, dirs, files in os.walk(classified_folder):
            for d in dirs:
                if d.startswith(folder_prefix):
                    shutil.rmtree(os.path.join(root, d))


class DirCleaner:
    def __init__(self, conf):
        self.conf = conf

    def clean_zip(self):
        print('cleaning......')
        for root, dirs, files in os.walk(self.conf.zip_folder):
            for file in files:
                fname = os.path.basename(file)
                if fname.startswith(self.conf.folder_prefix) \
                        and fname.endswith(".zip"):
                    # print(fname, file)
                    DirCleaner.remove_file(os.path.join(root, file))

    def clean_unzip(self):
        for root, dirs, files in os.walk(self.conf.unzip_folder):
            for dir in dirs:
                dir_name = os.path.basename(dir)
                if dir_name.startswith(self.conf.folder_prefix):
                    DirCleaner.remove_file(os.path.join(root, dir))

    @staticmethod
    def remove_file(file_path):
        try:
            if os.path.exists(file_path):
                write_information("removing old files: %s" % file_path)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                else:
                    shutil.rmtree(file_path)
            return True
        except os.error as e:
            write_information("remove failed! %s" % file_path)
            return False


class ProgressBar:
    def __init__(self):
        self.pos = 0
        self.total = 0
        self.prefix = 'Progress'
        self.suffix = 'Complete'
        self.decimals = 1
        self.length = 20
        self.fill = '█'
        self.max_num_flush = 100

        self.thresh_vals = []
        self.idx = 0

    def prepare(self):
        self.idx = 0
        self.thresh_vals = []
        step = 100 / self.max_num_flush

        pos = step
        while pos < 100:
            self.thresh_vals.append(pos)
            pos += step
        self.thresh_vals.append(99.9999999)

    def update(self, pos, total):
        self.pos = pos
        self.total = total

        percent_val = 100 * (self.pos / float(total))
        if percent_val < self.thresh_vals[self.idx]:
            return
        self.idx += 1

        percent = ("{0:." + str(self.decimals) + "f}").format(percent_val)
        filled_length = int(self.length * self.pos // total)
        bar = self.fill * filled_length + '-' * (self.length - filled_length)
        print('\r%s |%s| %s%% %s' % (self.prefix, bar, percent, self.suffix), end='\r')
        # Print New Line on Complete
        if self.pos == total:
            print()


class VisualizeDownload:
    def __init__(self, url, mb_size=4096):
        self.url = url
        self.max_block_size = mb_size
        self.page_info = b''

    def go(self):
        write_information('prepare to retrieve page, please wait...')
        req = urllib.request.urlopen(self.url)
        length = int(float(req.info()['Content-Length']))

        # 计算并设置进度条参数
        block_size = min(self.max_block_size, length//100)
        block_num = length // block_size
        remnant_size = length % block_size

        pb = ProgressBar()
        pb.total = block_num
        pb.prefix = 'Downloading '
        pb.suffix = 'Complete'
        pb.max_num_flush = 500
        pb.prepare()    # 计算进度条刻度等

        for i in range(block_num):
            data = req.read(block_size)
            self.page_info += data
            pb.update(i + 1, block_num)

        data = req.read(remnant_size)
        self.page_info += data

        return self.page_info
