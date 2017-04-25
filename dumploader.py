import os

from IOHelper import Naming


class RawFrameInfo:
    def __init__(self):
        self.offset = 0
        self.module = ''
        self.symbol = ''
        self.offset64 = 0
        self.src_file = ''
        self.line_idx = 0


class RawDmpInfo:
    def __init__(self):
        # list of RawFrameInfo
        self.rframes = []
        self.report_id = -1

    def parse(self, tree):
        for f in tree.find('stack').iter('frame'):
            rframe = RawFrameInfo()
            rframe.offset = int(f.get('offset'))
            rframe.module = f.get('module').split('.')[0]   # retain only dll name
            rframe.symbol = f.get('symbol')
            rframe.offset64 = int(f.get('offset64'))
            rframe.src_file = f.get('srcFile')
            rframe.line_idx = int(f.get('lineNum'))

            if rframe.line_idx < 0:
                rframe.line_idx =0
            self.rframes.append(rframe)


class Frame:
    def __init__(self):
        self.module = ''
        self.raw_symbol = ''
        self.line_idx = -1

        #
        self.clas = ''


class DumpInfoLevel1:
    '''
        level 1 dump info
    '''
    def __init__(self):
        self.report_id = -1     # value assigned outside of class
        self.frames = []

    def from_raw_data(self, rdi):
        self.report_id = rdi.report_id

        self.frames = []
        for rf in rdi.rframes:
            frame = Frame()
            frame.module = rf.module
            frame.raw_symbol = rf.symbol
            frame.line_idx = rf.line_idx

            frame.clas, func = Naming.get_clas_func(rf.symbol)
            self.frames.append(frame)


class DumpInfoLevel2:
    '''
        level 2 dump info contains level with key frame info extracted
    '''
    def __init__(self):
        self.di = None          # dump infomation level 1

        self.manager_name = ''
        self.module_name = ''
        self.line_name = ''     # line information as valid file name

        self.clas_name = ''     # distinguish manager of a shared module

        self.key_frame_idx = -1

    def from_level1(self, dil1):
        self.di = dil1

    def find_best_frame(self, md, clas_include, clas_exclude):
        """
        :param swc_modules: valid module's name,
                            module's name related to swc project, loaded from ModuleDefine.json
                            eg: "CommandCenterFactory"
        :param clas_include:  123
        :param clas_exclude: invalid class's name
                             these classes are most likely to be the standard lib
                                or third party lib which do not give useful information
                                for debugging.
                                "std::"
                             eg: What we really want are classes such as
                                "CElementEvent::" or "DataCenter::"
        """

        found_module = False
        module_name = ''    # the first valid module on stack
        idx_include = -1
        idx_exclude = -1
        idx_normal = -1
        idx_none = -1

        num_include = 0
        num_exclude = 0
        num_normal = 0
        num_none = 0

        # scan frames:
        # 1. check if module is valid
        # 2. count number of each kind class
        for j, frame in enumerate(self.di.frames):
            # module
            if module_name != frame.module and found_module:
                break

            module_name = frame.module
            if module_name not in md.module_list:
                continue
            found_module = True

            # class
            clas = frame.clas
            if clas in clas_include:    # include class
                num_include += 1
                idx_include = j if idx_include < 0 else idx_include
            elif clas in clas_exclude:  # exclude class
                num_exclude += 1
                idx_exclude = j if idx_exclude < 0 else idx_exclude
            elif clas == '':        # no class
                num_none += 1
                idx_none = j if idx_none < 0 else idx_none
            else:                   # normal class
                num_normal += 1
                idx_normal = j if idx_normal < 0 else idx_normal

        # no valid module is found
        if not found_module:
            return False

        if num_include > 0:
            self.key_frame_idx = idx_include
        elif num_normal > 0:
            self.key_frame_idx = idx_normal
        elif num_none > 0:
            self.key_frame_idx = idx_none
        elif num_exclude > 0:
            self.key_frame_idx = idx_exclude

        self.module_name = self.di.frames[self.key_frame_idx].module
        self.clas_name = self.di.frames[self.key_frame_idx].clas
        self.line_name = self.di.frames[self.key_frame_idx].raw_symbol

        self.manager_name = md.which_manager(self.module_name, self.clas_name)

        if self.line_name == '':
            self.line_name = "NoFunction"
        else:
            self.line_name += '_'
            self.line_name += str(self.di.frames[self.key_frame_idx].line_idx)

        return True
