def modify_bat(src, dst):
    f = open(src)
    lines = f.readlines()

    # lines[0]: python XXX.py ^
    exe_name = lines[0].split()[1].split('.')[0]
    lines[0] = exe_name + " ^\n"

    f2 = open(dst, 'w+')
    f2.writelines(lines)


if __name__=='__main__':
    modify_bat(src='run_server.bat', dst='run_server2.bat')