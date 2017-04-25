import os


def modify_bat(src, dst):
    f = open(src)
    lines = f.readlines()

    # lines[0]: python XXX.py ^
    exe_name = lines[0].split()[1].split('.')[0]
    lines[0] = exe_name + " ^\n"

    f2 = open(dst, 'w+')
    f2.writelines(lines)


def mk_folder(folder):
    if not os.path.exists(folder):
        os.mkdir(folder)

    zip = folder + "\\zip"
    unzip = folder + "\\unzip"
    classified = folder + "\\classified"
    if not os.path.exists(zip):
        os.mkdir(zip)
    if not os.path.exists(unzip):
        os.mkdir(unzip)
    if not os.path.exists(classified):
        os.mkdir(classified)


if __name__ == '__main__':
    modify_bat(src='release\\run_server.bat', dst='release\\run_server.bat')
    mk_folder("release\\reports")