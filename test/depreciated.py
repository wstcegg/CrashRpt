def check_zip_file_status(self, zip_path):
    '''
    :param zip_path: you know what is mean
    :return: file status.
            So long as invalid file is removed, the return status is True, otherwise is False
            file: exist && valid -> True
            file not exist -> True
            file exist && invalid -> False;
    '''
    if os.path.exists(zip_path):
        # zip file already exist
        try:
            zf = zipfile.ZipFile(zip_path, 'r')
            ret = zf.testzip()
            if ret is not None:
                # zip file not valid, ret is the first bad file
                self.write_infomation("first bad file in zip %s" % ret)
                self.remove_file(zip_path)  # try to remove it
            else:
                # zip file is good
                self.write_infomation("zip file already exist %s" % zip_path)
        except zipfile.BadZipFile as e:
            self.remove_file(zip_path)


def check_unzip_file_status(self, unzip_path):
    '''
    :param unzip_path: you know what is mean
    :return: file status.
            So long as invalid file is removed, the return status is True, otherwise is False
            file exist && valid -> True
            file not exist -> True
            file exist && invalid -> False;
    '''
    pass


def check_dmp_file_status(self, dmp_path):
    #
    pass