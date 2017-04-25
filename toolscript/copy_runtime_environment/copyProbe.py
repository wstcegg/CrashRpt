import os
import shutil


def copy_helper_common(src, dst, fname):
    # copy implementation
    src += fname
    dst += fname
    if os.path.exists(src):
        shutil.copy(src, dst)
    else:
        print("non-existing path: " + src)


def copy_probe_helper1(src, dst, dst_project_name, fname, version, debug_flag):

    folder = r'\Debug' if debug_flag else r'\Release'
    last = 'd' if debug_flag else ''    #   Release & Debug make no difference for filename

    # inc
    # src/include/CrashRptProbe.h
    # -----> dst/XXXX/CrashRptProbe.h
    name = "\\" + fname + ".h"
    _src = src + r"\include"
    _dst = dst + dst_project_name
    copy_helper_common(_src, _dst, name)

    # lib
    # src/lib/CrashRptProbe_1401_d_.lib
    # -----> dst/XXXX/CrashRptProbe_1401_d_.lib
    name = "\\" + fname + version + last + ".lib"
    _src = src + r'\lib'
    _dst = dst + dst_project_name
    copy_helper_common(_src, _dst, name)

    # dll
    # src/bin/CrashRptProbe_1401_d_.dll
    # -----> dst/Debug/CrashRptProbe_1401_d_.dll
    name = "\\" + fname + version + last + ".dll"
    _src = src + r'\bin'
    _dst = dst + folder
    copy_helper_common(_src, _dst, name)


def copyProbe(src, dst, dst_project_name, fname, version):
    # debug
    copy_probe_helper1(src, dst, dst_project_name, fname, version, True)
    # release
    copy_probe_helper1(src, dst, dst_project_name, fname, version, False)


def copy_helper_common(src, dst, fname):
    # copy implementation
    src += fname
    dst += fname

    print("copy from %s to %s" % (src, dst))

    if os.path.exists(src):
        shutil.copy(src, dst)
    else:
        print("non-existing path: " + src)


def copy_dbg_helper1(src, dst, dst_project_name, fname, debug_flag):

    folder = r'\Debug' if debug_flag else r'\Release'
    last = ''
    # last = 'd' if debug_flag else ''    #   Release & Debug make no difference for filename

    # inc
    # src/include/dbghelp.h
    # -----> dst/XXXX/dbghelp.h
    name = "\\" + fname + ".h"
    _src = src + r"\include"
    _dst = dst + dst_project_name
    copy_helper_common(_src, _dst, name)

    # lib
    # src/lib/dbghelp.lib
    # -----> dst/XXXX/dbghelp.lib
    name = "\\" + fname + ".lib"
    _src = src + r'\lib'
    _dst = dst + dst_project_name
    copy_helper_common(_src, _dst, name)

    # dll
    # src/bin/dbghelp.dll
    # -----> dst/Debug/dbghelp.dll
    name = "\\" + fname + ".dll"
    _src = src + r'\bin'
    _dst = dst + folder
    copy_helper_common(_src, _dst, name)


def copydbg(src, dst, dst_project_name, fname):
    # debug
    copy_dbg_helper1(src, dst, dst_project_name, fname, True)
    # release
    copy_dbg_helper1(src, dst, dst_project_name, fname, False)


if __name__ == "__main__":

    src_folder = r"E:\debug_\INP\Release_1.4.1_3"
    dst_folder = r"E:\debug_\INP\testcbd"
    dst_project_name = r'\testcbd'
    version = '1401'

    #
    fname = 'CrashRptProbe'
    copyProbe(src_folder, dst_folder, dst_project_name, fname, version)

    #
    fname = 'dbghelp'
    copydbg(src_folder, dst_folder, dst_project_name, fname)

    # for python file
    dst_folder = r"E:\pycharm\CrashAnalyze\runtime"
    fname = 'CrashRptProbe'
    name = '\\' + fname + version + '.dll'
    copy_helper_common(src_folder + r'\bin', dst_folder, name)

    fname = 'dbghelp'
    name = '\\' + fname + '.dll'
    copy_helper_common(src_folder + r'\bin', dst_folder, name)


