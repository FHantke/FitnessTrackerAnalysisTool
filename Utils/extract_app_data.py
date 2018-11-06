import hashlib
import os
from datetime import datetime


class Extractor:
    """ This class is a helper class. It can be used to extract files from an Android device via ADB"""

    @staticmethod
    def md5(fname):
        """
        The method calculates the md5 hash of a file
        :param fname: name of the file
        :return: md5 hash
        """
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def extract_more_files(self, path, output_path="."):
        """
        The method lists all files from a directory and hands each of them to the one file extract method
        :param path: The path to the directory on the Android device
        :param output_path: The path, where to store the files on the PC
        :return: The paths to the files on the PC
        """
        exit_code = os.system("adb shell 'su -c \"ls {}\"' > glob".format(path))
        if exit_code != 0:
            raise SystemError("The program was not able to find a connected phone")
        glob = open("glob", 'r')
        ret = []
        for line in glob:
            line = line.rstrip()
            print(line)
            r = self.extract_one_file(os.path.join(os.path.dirname(path), line), output_path)
            ret.append(r)
        glob.close()
        os.remove("glob")
        return ret
        
    def extract_one_file(self, path, output_path="."):
        """
        The method extracts single files from a given path on an Android device
        :param path: The path to the file on the Android device.
                     If * is in the path, only the first found file is extracted.
        :param output_path: The path, where to store the file on the PC
        :return: The path of the file on the PC
        """

        if '*' in path:
            if path.startswith("/sdcard"):
                exit_code = os.system("adb shell 'ls {}' > glob".format(path))
            else:
                exit_code = os.system("adb shell 'su -c \"ls {}\"' > glob".format(path))

            if exit_code != 0:
                raise SystemError("The program was not able to find a connected phone")
            glob = open("glob", 'r')
            path = glob.readline().rstrip()
            glob.close()
            os.remove("glob")

        print("Extract {} from the device".format(path))

        basename = os.path.basename(path)
        timestamp = datetime.now().strftime('%Y_%m_%d_%H_%M')
        file_name = "{}_{}".format(timestamp, basename)

        if not path.startswith("/sdcard"):
            flag_device = False
            print("Copy file from root are to user area")
            while not flag_device:
                os.system("adb shell 'su -c \"md5 {}\"' > md5_1".format(path))
                os.system("adb shell 'su -c \"cp {} /sdcard/\"'".format(path))
                os.system("adb shell 'su -c \"md5 /sdcard/{}\"' > md5_2".format(basename))
                md5_1 = open("md5_1", 'r')
                hash_value_1 = md5_1.readline().split(' ')[0]
                md5_2 = open("md5_2", 'r')
                hash_value_2 = md5_2.readline().split(' ')[0]
                print("Compare md5 on device")
                flag_device = (hash_value_1 == hash_value_2)
                if not flag_device:
                    print("md5 was wrong. Try to copy file on device again")
                md5_1.close()
                md5_2.close()
        
        flag_pc = False
        print("Copy file from phone to pc")
        while not flag_pc:
            os.system("adb pull /sdcard/{}  {}/{}".format(basename, output_path, file_name))
            md5_2 = open("md5_2", 'r')
            hash_value_2 = md5_2.readline().split(' ')[0]
            hash_value_3 = self.md5("{}/{}".format(output_path, file_name))
            print("Compare md5 on pc")
            flag_pc = (hash_value_2 == hash_value_3)
            if not flag_pc:
                print("md5 was wrong. Try to download file from device again")
            md5_2.close()

        os.system("adb shell 'rm -rf /sdcard/{}'".format(basename))
        os.remove("md5_1")
        os.remove("md5_2")
        return os.path.join(output_path, file_name)
