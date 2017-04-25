import os
import shutil


def copy_helper_common(src, dst, fname):
    # copy implementation
    src += fname
    dst += fname

    print("copy from %s to %s" % (src, dst))

    if os.path.exists(src):
        if os.path.exists(dst):
            os.remove(dst)
        shutil.copy(src, dst)
    else:
        print("non-existing path: " + src)


def main():
    # for python file
    src_folder = r"E:/debug_/INP/totallynew/release/"
    dst_folder = r"../../runtime/"

    fname = 'dumploader.dll'
    copy_helper_common(src_folder, dst_folder, fname)

    fname = 'dbghelp.dll'
    copy_helper_common(src_folder, dst_folder, fname)


if __name__ == '__main__':
    main()