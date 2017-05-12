import os
import os.path
import shutil

import xml.etree.cElementTree
import xml.etree.ElementTree as Et

import dumploader
import summarize
import IOHelper
from IOHelper import write_information


class AnalyzeOne:
    def __init__(self, thread_id, conf, md):
        self.report_id = -1

        self.zip_name = ''
        self.zip_path = ''
        self.folder_name = ''
        self.folder_path = ''

        self.conf = conf
        self.md = md
        #
        self.thread_id = thread_id

    def prepare(self, report_id):
        self.report_id = report_id

        dfn = IOHelper.DumpFileName(self.conf)
        self.zip_name = dfn.zip_name_from_id(self.report_id)
        self.zip_path = self.conf.zip_folder + '\\' + self.zip_name

        self.folder_name = dfn.folder_from_id(self.report_id)
        self.folder_path = self.conf.unzip_folder + '\\' + self.folder_name

    def process(self, invalid_records):

        ret = self.process_helper(invalid_records)
        if ret == 0:
            folder = self.conf.classified_folder + '\\valid\\'
            if not os.path.exists(folder):
                os.mkdir(folder)
            dst = folder + self.zip_name
        elif ret == -1:
            folder = self.conf.classified_folder + '\\invalid\\'
            if not os.path.exists(folder):
                os.mkdir(folder)
            dst = folder + self.zip_name
        elif ret == -2:
            folder = self.conf.classified_folder + '\\broken\\'
            if not os.path.exists(folder):
                os.mkdir(folder)
            dst = folder + self.zip_name

        # move files
        src = self.zip_path
        try:
            if os.path.exists(src) and not os.path.exists(dst):
                shutil.copy(src, dst)
        except Exception as e:
            print('move file %s failed' % self.zip_name)

    def process_helper(self, invalid_records):
        """
        
        :param invalid_records: 
        :return:    valid: 0, invalid: -1, broken: -2

        """
        fpath = os.path.join(self.folder_path, self.conf.dump_xml)

        if not os.path.exists(fpath):
            write_information("dump xml %s not exist!" % fpath, self.thread_id)
            return -2

        write_information('[classifying]: %s' % fpath, self.thread_id)

        dumpXML = Et.parse(fpath)

        # convert XML string to raw struct
        rdi = dumploader.RawDmpInfo()
        rdi.parse(dumpXML)
        rdi.report_id = self.report_id

        # to info level 1
        dil1 = dumploader.DumpInfoLevel1()
        dil1.from_raw_data(rdi)

        # to info level 2
        dil2 = dumploader.DumpInfoLevel2()
        dil2.from_level1(dil1)
        frame_is_good = dil2.find_best_frame(self.md,
                                             self.conf.clas_include,
                                             self.conf.clas_exclude)
        if not frame_is_good:
            return -2

        # classify file
        for invalid_rec in invalid_records:
            if dil2.module_name == invalid_rec.module \
                    and dil2.manager_name == invalid_rec.manager \
                    and dil2.line_name.startswith(invalid_rec.line):
                return -1
        return 0


        # record = IOHelper.xls_record()
        # record.module = dil2.module_name
        # record.manager = dil2.manager_name
        # record.line = dil2.line_name
        # if record not in invalid_records:
        #     return 0
        # else:
        #     return -1
        ###############
        # if record not in invalid_records:
        #     folder = self.conf.classified_folder + '\\valid\\'
        #     if not os.path.exists(folder):
        #         os.mkdir(folder)
        #     dst = folder + self.zip_name
        # else:
        #     folder = self.conf.classified_folder + '\\invalid\\'
        #     if not os.path.exists(folder):
        #         os.mkdir(folder)
        #     dst = folder + self.zip_name
        #
        # try:
        #     if os.path.exists(src) and not os.path.exists(dst):
        #         shutil.copy(src, dst)
        # except Exception as e:
        #     print('move file %s failed' % self.zip_name)


class AnalyzeAll:
    def __init__(self, conf, md):
        self.file_dict = {}
        self.file_list = []

        self.conf = conf
        self.md = md

    def prepare_scan(self, zip_folder, unzip_folder):
        # find all files to be processed
        # and create file_dict for later removing files
        for root, dirs, files in os.walk(unzip_folder):
            if root == unzip_folder:  # only iterate direct sub folder
                count = 0
                for dir in dirs:
                    # ./ error_report_22307 / crashdump.dmp
                    #    0123456789...13

                    if not dir.startswith(self.conf.folder_prefix):  # escape invalid folder
                        print('invalid path 1: ' + dir)
                        continue

                    if 0 <= dir.find('.') < len(dir):
                        print('invalid path 2: ' + dir)
                        continue

                    # folder
                    folder_path = root + '\\' + dir

                    # zip
                    dfn = IOHelper.DumpFileName(self.conf)
                    report_id = dfn.get_report_id(dir)

                    zip_path = zip_folder + '\\' + dir + '.zip'
                    self.file_dict[report_id] = (folder_path, zip_path)  # construct id-dump map
                    self.file_list.append((report_id, folder_path, zip_path))

                    # print(count, report_id, folder_path, zip_path)
                    count += 1

    def prepare_list(self, zip_folder, unzip_folder, id_list):
        # find all files to be processed
        # and create file_dict for later removing files
        dfn = IOHelper.DumpFileName(self.conf)
        count = 0
        for report_id in id_list:
            # folder
            folder_path = unzip_folder + '\\' + dfn.folder_from_id(report_id)
            zip_path = zip_folder + '\\' + dfn.zip_name_from_id(report_id)

            self.file_dict[report_id] = (folder_path, zip_path)  # construct id-dump map
            self.file_list.append((report_id, folder_path, zip_path))

            # print(count, report_id, folder_path, zip_path)
            count += 1

    def process(self, dump_xml, md):
        #
        sml1 = summarize.SummaryLevel1()
        sml1.create_manager_dict(md)

        count = 0
        for report_id, folder_path, zip_path in self.file_list:
            # print(report_id, folder_path, zip_path)
            fpath = os.path.join(folder_path, dump_xml)

            if not os.path.exists(fpath):
                print("file %s not exist!!!!!!!!!!!!!!!!!!" % fpath)
                continue

            print('___processing %d___' % count)
            print(fpath)
            count += 1

            dumpXML = Et.parse(fpath)

            # convert XML string to raw struct
            rdi = dumploader.RawDmpInfo()
            rdi.parse(dumpXML)
            rdi.report_id = report_id

            # to info level 1
            dil1 = dumploader.DumpInfoLevel1()
            dil1.from_raw_data(rdi)

            # to info level 2
            dil2 = dumploader.DumpInfoLevel2()
            dil2.from_level1(dil1)
            frame_is_good = dil2.find_best_frame(md,
                                                 self.conf.clas_include,
                                                 self.conf.clas_exclude)

            # add into summary level 1
            if frame_is_good:
                sml1.join_dump(dil2)

        # remove module with no crash
        sml1.remove_non_crash_module()

        return sml1


def analyze_client(conf, md, report_list=[]):
    print('begin to analyze!')

    # summary level 1
    al = AnalyzeAll(conf, md)
    if report_list:
        al.prepare_list(conf.zip_folder, conf.unzip_folder, report_list)
    else:
        al.prepare_scan(conf.zip_folder, conf.unzip_folder)

    print(al.conf)
    sml1 = al.process(conf.dump_xml, md)

    # summary level 2
    sml2 = summarize.SummaryLevel2()
    sml2.from_level1(sml1)
    sml2.sort_data()

    # write excel document
    ex = IOHelper.XLS()
    ex.write(conf.xls, sml2.to_records())

    # move files
    sml2.create_folders(conf.classified_folder)
    move_list, unzip_list = sml2.prepare_to_move_files(al.file_dict, conf)

    print(len(move_list))

    IOHelper.FileMover.move_files(move_list)
    IOHelper.FileMover.unzip_files(unzip_list)
