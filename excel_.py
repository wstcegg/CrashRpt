import xlrd
import os
import shutil
import copy

import Initialize
import IOHelper

# "xls_modification": {
#     "0": "keep",
#     "-1": "delete",
#     "-2": "rename to non-exist",
#     "-3": "rename to exist"
# }


class Records:
    def __init__(self, config, md):
        self.data = []
        self.total_crash_num = 0

        self.data_old = []
        self.modify_rule = {}

        self.config = config
        self.md = md

        # used when modify record
        # {line idx in XLS ----> record idx in self.data}
        self.row_idx_dict = {}

    def to_str(self):
        s = ''
        for item in self.data:
            s += item.to_str()
            s += '\n'

        if s == '':
            s = 'Records is empty!'
        return s

    def clear(self):
        self.data = []
        self.total_crash_num = 0

        self.data_old = []
        self.modify_rule = None

    def read_error_package(self, root_folder):
        for idx, record in enumerate(self.data):
            # load report_list from ini file
            ini_path = root_folder + '\\' + record.to_folder() + '\\error_package.ini'
            self.data[idx].report_list = IOHelper.INI.load_error_package(ini_path)

            # num is load from excel
            if self.data[idx].num != len(self.data[idx].report_list):
                print("record [%s, %s, %s] and error_package.ini not compatible!!!"
                      % (record.module, record.manager, record.line))

    def read_one(self, xls, sheet_name1='data', sheet_name2='rule'):
        #
        res, data, rule = self.read_excel_helper(xls, sheet_name1, sheet_name2)
        if not res:
            return False

        self.data = data
        self.data_old = []
        self.modify_rule = rule
        return True

    def read_two(self, new_xls, old_xls,
                 new_sheet_name1='data', new_sheet_name2='rule',
                 old_sheet_name1='data', old_sheet_name2='rule'):
        #
        res1, new_data, new_rule = self.read_excel_helper(new_xls, new_sheet_name1, new_sheet_name2)
        res2, old_data, old_rule = self.read_excel_helper(old_xls, old_sheet_name1, old_sheet_name2)

        if not res1 or not res2:
            print("excel load failed!")
            return False

        self.data = new_data
        self.data_old = old_data
        self.modify_rule = self.merge_modify_rule([new_rule, old_rule])
        return True

    def read_excel_helper(self, fname, sheet1_name='data', sheet2_name='rule', load_pre_rule=False):
        #
        data = []
        rule = {}
        try:
            wb = xlrd.open_workbook(fname)
        except Exception as e:
            print("xlrd: open excel worksheet %s failed!" % fname)
            return False, data, rule

        # load data and new rule from sheet1
        ws1 = wb.sheet_by_name(sheet1_name)
        data1, row_idx_dict = self.read_data(ws1)
        rule1 = self.get_modify_rule(data1)
        rule1 = self.update_rule_type3(rule1, row_idx_dict, data1, reserve=True)

        # load previous rule from sheet2
        rule2 = None
        if load_pre_rule:
            ws2 = wb.sheet_by_name(sheet2_name)
            data2 = self.read_data(ws2)
            rule2 = self.get_modify_rule(data2)
            rule2 = self.update_rule_type3(rule2, row_idx_dict, data2, reserve=False)

        data = data1
        rule = self.merge_modify_rule([rule1, rule2])
        return True, data, rule

    def read_data(self, ws):
        # row type 1:
        # 模块	版本号	负责人	崩溃行	次数	备注  | 修正码     修正数据
        #  0      1       2       3      4       5    |   6           7

        # row type 2:
        # 总计                                  XXX
        #  0                                     5

        data = []
        row_idx_dict = {}
        if ws.ncols < 8:    # column number invalid
            return data

        for i in range(1, ws.nrows):
            #
            row = ws.row_values(i)
            if not str(row[3]):     # column 3 must not be empty
                continue

            # data row
            record = IOHelper.xls_record()

            if row[0] == '总计':  # reaching sum row
                break

            # module, might be empty
            if str(row[0]):
                record.module = str(row[0])         # non-empty
            elif data:
                record.module = data[-1].module     # as previous one
            else:                                   # first record with blank field is invalid!
                print('xls file content broken!')
                return

            # manager, might be empty
            if str(row[2]):                         # non-empty
                record.manager = str(row[2])
            elif data:
                record.manager = data[-1].manager   # as previous one
            else:                                   # first record with blank field is invalid!
                print('xls file content broken!')
                return

            # line
            record.line = str(row[3])
            # num
            record.num = int(row[4])
            # remark
            record.remark = str(row[5])

            # modify code
            if len(row) == 8 and row[6]:
                record.modify_code = int(row[6])

            # modify info
            if len(row) == 8 and row[7]:
                record.modify_info = str(row[7])

            data.append(record)
            row_idx_dict[i + 1] = len(data) - 1    # actual row index -> record idx
            self.total_crash_num += record.num

        return data, row_idx_dict

    def update_rule_type3(self, rule=None, idx_dict=None, data=None, reserve=False):
        # print(rule)
        for k, v in rule.items():
            code, info = v
            if code == -3:    # only rule of type 3 is modified
                if reserve:
                    xls_idx = idx_dict[int(float(info))]
                    v[1] = data[xls_idx].to_vs_dbgstr()
                    # now this rule converted to type 2
                    v[0] = -2
                    # print(v)
        return rule

    def get_modify_rule(self, data_rule):
        #
        rule = {}
        if not data_rule:
            return rule

        for record in data_rule:
            if record.modify_code >= 0:
                continue

            k = (record.module, record.manager, record.line)
            v = [record.modify_code, record.modify_info]
            rule[k] = v

        return rule

    def merge_modify_rule(self, rule_list):
        #
        new_rule = {}
        if not rule_list:
            return new_rule

        for rule in rule_list:

            if not rule:
                continue

            for (k, v) in rule.items():
                if not new_rule.get(k):
                    new_rule[k] = v
        return new_rule

    def record_from_str(self, s):
        # vs string structure
        # module.dll ! classname :: otherinfo 行 lineidx + 0x89 字节
        # GlobalEnvironment.dll!CGlobalEnvLite::ReleaseObject()  行200 + 0x5 字节

        record = IOHelper.xls_record()
        record.module, clas, func, idx = IOHelper.VSDbgNaming.get_mod_clas_func_idx(s)
        record.manager = self.md.which_manager(record.module, clas)

        fname = IOHelper.WinDbgNaming.name_from_clas_func_idx(clas, func, idx)
        record.line = fname[:80]

        # print("new record:")
        # print(record)

        return record

    # update data related
    def get_update_detail(self):
        #
        changes = {}
        for idx, record in enumerate(self.data):
            new_record = copy.deepcopy(record)

            k = (record.module, record.manager, record.line)
            if not self.modify_rule.get(k):     # good record, no need to update
                continue

            code, info = self.modify_rule[k]
            # the modify code by modify rule must be negative!
            if code == -1:
                # delete
                # make the new record an empty one
                new_record = IOHelper.xls_record()
            elif code == -2:
                # rename
                # load new information from dump symbol
                new_record = self.record_from_str(info)
                new_record.num = record.num
                new_record.report_list = record.report_list
            changes[idx] = new_record
        return changes

    def update(self, changes, file_folder, mod_disk):
        #
        new_data = []
        del_list = []

        # iterate all records, check if it requires modification
        # if no:  ----->[old record]
        # if yes: ----->[modified record]
        for idx, record in enumerate(self.data):
            if not changes.get(idx):    # good record
                new_data.append(record)

        for rec in new_data:
            print(rec.to_str())

        for idx, record in enumerate(self.data):
            if changes.get(idx):  # good record
                # record to be updated, src folder should be deleted
                folder = file_folder + '\\' + record.to_folder()
                del_list.append(folder)

                # modified record
                new_record = changes[idx]

                # if modified record is empty, ignore and continue
                if new_record.is_empty():
                    continue

                # new record not empty
                if new_record not in new_data:          # non-duplicated
                    new_data.append(new_record)
                    new_idx = len(new_data) - 1
                else:                                   # duplicated
                    new_idx = new_data.index(new_record)
                    new_data[new_idx].merge(new_record)

                # this is a new record, currently no corresponding folder
                # to be constructed later
                new_data[new_idx].update_folder = True

        self.data = sorted(new_data)

        if mod_disk:
            self.delete_folders(del_list)
            self.create_folders()

    def create_folders(self):
        """create folders for new record"""
        for record in self.data:
            if record.update_folder:    # no corresponding folder for this record, create it
                folder = record.to_folder(self.config.classified_folder)
                if not os.path.exists(folder):
                    os.mkdirs(folder)

                # write ini file for current folder
                ini = IOHelper.INI()
                ini.write(os.path.join(folder, 'error_package.ini'), record.report_list)

                # move zip files to current folder
                report_list = record.report_list[0:conf.num_zip_move]
                fm = IOHelper.FileMover(self.config)
                move_list = fm.move(conf.zip_folder, folder, report_list)

                zip_list = [pair[1] for pair in move_list]
                fm.unzip_files(zip_list)

                record.update_folder = False

    def delete_folders(self, del_list):
        """delete folders correspond to old record"""
        for folder in del_list:
            if os.path.isdir(folder) and os.path.exists(folder):
                shutil.rmtree(folder)

    def get_raw_rules(self):
        raw_rules = []
        for k, v in self.modify_rule.items():
            raw_rule = IOHelper.xls_record()

            raw_rule.module = k[0]  # module
            # raw_rule.version        version ignored
            raw_rule.manager = k[1]  # manager
            raw_rule.line = k[2]  # line
            # raw_rule.num       num ignored
            # raw_rule.remark       remark ignored
            raw_rule.modify_code = v[0]  # modify code
            raw_rule.modify_info = v[1]  # modify info

            raw_rules.append(raw_rule)
        return raw_rules

    def write_excel(self, fname):

        print("modifications: ")
        print(self.modify_rule)

        rules = self.get_raw_rules()

        ex = IOHelper.XLS()
        ex.write(fname, self.data, rules)


def update_xml(conf, md):
    r = Records(conf, md)
    # r.read_one(conf.xls, '东方财富通', 'rule')
    r.read_two(conf.xls, r'C:\Users\Administrator\Desktop\new.xls',
               '东方财富通', 'rule', '东方财富通', 'rule')
    r.read_error_package(conf.classified_folder)

    # print("Init records:")
    # print(r.to_str())
    #
    # print("modifications: ")
    # print(r.modify_rule)

    changes = r.get_update_detail()
    # print('Changes: ')
    # for k, v in changes.items():
    #     print(k, '->[', v, ']')

    # print(r.to_str())

    r.update(changes, conf.classified_folder, mod_disk=True)
    IOHelper.FileMover.remove_empty_dir(conf.classified_folder)
    # IOHelper.FileMover.remove_unzip_files(conf.classified_folder, conf.folder_prefix)

    # r.write_excel(conf.xls)
    r.write_excel(r'data\new.xls')


if __name__ == '__main__':

    # configuration
    conf = Initialize.Conf()
    conf.load(r'data\config.json')

    # module define
    md = Initialize.MD()
    md.load(conf.module_define)

    update_xml(conf, md)