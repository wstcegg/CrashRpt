from distutils.core import setup
import os
import shutil
import py2exe

print('123123')

data_files = [('data', ['data\config.json', 'data\ModulesDefine.json', 'data\invalid.txt']),
              ('runtime', ['runtime\dumploader.dll',
                           'runtime\dbghelp.dll']),
              ('.', ['run_server.bat'])]
setup(
    name='crash',
    console=['crash.py'],  # 'windows' means it's a GUI, 'console' It's a console program, 'service' a Windows' service, 'com_server' is for a COM server
    # You can add more and py2exe will compile them separately.
    options={
        # This is the list of options each module has, for example py2exe,
        # but for example, PyQt or django could also contain specific options
        'py2exe': {
            'packages': [],
            'dist_dir': 'release',     # The output folder
            'compressed': True,     # If you want the program to be compressed to be as small as possible
            # All the modules you need to be included,
            # I added packages such as PySide and psutil
            # but also custom ones like modules and utils inside it
            # because py2exe guesses which modules are being used by the file we want to compile,
            # but not the imports, so if you import something inside main.py
            # which also imports something, it might break.
            'includes': [
                'os',
                'analyze',
                'AutoDownload', 
                'dumploader',
                'excel_',
                'Initialize',
                'IOHelper',
                'summarize' 
                ],
        }
    },
    data_files=data_files   # Finally, pass the
)