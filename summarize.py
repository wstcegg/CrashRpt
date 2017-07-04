import os
from copy import deepcopy

import IOHelper


class SummaryLevel1:
    def __init__(self):
        '''
        manager_dict:   {manager_name:{module_dict}}
        module_dict:    {module_name:{line_dict}}
        line_dict:      {line_name:{line_info}}
        ----->
        {manager_name:{module_name:{line_name:{line_info}}}}
        <-----
        '''
        self.manager_dict = {}

    def create_manager_dict(self, md):
        self.manager_dict = md.get_manager_dict()

    def join_dump(self, dil2):

        module_dict = self.manager_dict[dil2.manager_name]
        # print(dil2.manager_name, dil2.module_name, dil2.clas_name)
        if not module_dict.get(dil2.module_name):
            module_dict[dil2.module_name] = {}
        line_dict = module_dict[dil2.module_name]

        # update line_dict
        if not line_dict.get(dil2.line_name):
            line_dict[dil2.line_name] = []
        report_list = line_dict[dil2.line_name]
        report_list.append(dil2.di.report_id)

    def remove_non_crash_module(self):

        new_manager_dict = {}

        for ma, mo_dict in self.manager_dict.items():
            new_mo_dict = {}
            # check if this module contains good information
            for mo, li_dict in mo_dict.items():
                if li_dict:
                    # print('line_dict:', li_dict)
                    new_mo_dict[mo] = deepcopy(li_dict)
            if new_mo_dict:
                new_manager_dict[ma] = new_mo_dict

        self.manager_dict = new_manager_dict


class LineSimple:
    def __init__(self):
        self.name = ''
        self.report_list = []

    def __lt__(self, other):
        return self.name < other.name


class ModuleSimple:
    def __init__(self):
        self.name = ''
        self.line_list = []

    def __lt__(self, other):
        return self.name < other.name


class ManagerSimple:
    def __init__(self):
        self.name = ''
        self.module_list = []

    def __lt__(self, other):
        return self.name < other.name


class SummaryLevel2:
    def __init__(self):
        self.manager_list = []

    def __str__(self):
        s = ''
        for manager in self.manager_list:
            s += manager.name
            s += '\n'

            for module in manager.module_list:
                s += '\t'
                s += module.name
                s += '\n'

                for line in module.line_list:
                    s += '\t'*2
                    s += line.name
                    s += str(len(line.report_list))
                    s += '\n'
        return s

    def from_level1(self, suml1):
        for ma, mo_dict in suml1.manager_dict.items():
            mas = ManagerSimple()
            mas.name = ma

            for mo, line_dict in mo_dict.items():
                mos = ModuleSimple()
                mos.name = mo

                for li, report_list in line_dict.items():
                    lis = LineSimple()
                    lis.name = li
                    lis.report_list = report_list

                    mos.line_list.append(lis)
                mas.module_list.append(mos)
            self.manager_list.append(mas)

    def to_records(self):
        records = []
        for manager in self.manager_list:
            for module in manager.module_list:
                for line in module.line_list:

                    rec = IOHelper.xls_record()
                    rec.line = line.name
                    rec.module = module.name
                    rec.manager = manager.name
                    rec.num = len(line.report_list)
                    rec.report_list = line.report_list

                    records.append(rec)
        return records

    def sort_data(self):
        #
        for manager in self.manager_list:
            for module in manager.module_list:
                # sort lines
                module.line_list.sort()
            # sort modules
            manager.module_list.sort()
        # sort manager
        self.manager_list.sort()

    def prepare_to_move_files(self, zip_dict, conf):
        #
        if not os.path.exists(conf.classified_folder):
            os.mkdir(conf.classified_folder)

        #
        move_list = []
        unzip_list = []

        # manager
        for manager in self.manager_list:
            ma_path = os.path.join(conf.classified_folder, manager.name)

            # module
            for module in manager.module_list:
                mo_path = os.path.join(ma_path, module.name)

                # line
                for line in module.line_list:
                    line_folder = IOHelper.Naming.valid_name(line.name)     # line num is not specified
                    li_path = os.path.join(mo_path, line_folder)

                    # ini, server side do not need ini
                    if conf.write_ini:
                        ini = IOHelper.INI()
                        line.report_list = sorted(line.report_list)
                        ini.write(li_path+'\\error_package.ini', line.report_list)

                    #
                    for i, report_id in enumerate(line.report_list):
                        # move small portion of zip files to folder
                        if 0 < conf.num_zip_move <= i:
                            continue

                        # src
                        # dict struct: id->(folder, zip)
                        src = zip_dict[report_id][1]

                        # dst
                        dfn = IOHelper.DumpFileName(conf)
                        zip_fname = dfn.zip_name_from_id(report_id)
                        dst = os.path.join(li_path, zip_fname)

                        # print(dst, len(line.report_list))

                        # add to move list
                        move_list.append((src, dst))

                        if 0 <= conf.num_zip_extract <= i:
                            continue

                        # add to unzip list
                        unzip_list.append(dst)

        return move_list, unzip_list

    def create_folders(self, dst_folder):
        #
        if not os.path.exists(dst_folder):
            os.mkdir(dst_folder)

        # manager
        for manager in self.manager_list:
            ma_path = os.path.join(dst_folder, manager.name)
            if not os.path.exists(ma_path):
                print('making folder: ' + ma_path)
                os.mkdir(ma_path)

            # module
            for module in manager.module_list:
                mo_path = os.path.join(ma_path, module.name)
                if not os.path.exists(mo_path):
                    print('making folder: ' + mo_path)
                    os.mkdir(mo_path)

                # line
                for line in module.line_list:
                    line_folder = IOHelper.Naming.valid_name(line.name)
                    li_path = os.path.join(mo_path, line_folder)     # attention, restrict maximum size of line name
                    if not os.path.exists(li_path):
                        print('making folder: ' + li_path)
                        os.mkdir(li_path)
