from Devices.device import Device
from datetime import datetime
from Utils import extract_app_data
import glob
import os
import re


class App(Device):
    """ This class receives data from the Huawei Health application, interprets it and stores it in the database """
    def __init__(self):
        super().__init__()
        self.support_heartrate = False
        self.support_custom_attributes = False
        self.support_steps = True
        self.support_sleep = False
        self.support_user = False
        self.support_position = False

    def action(self):
        """
        First, the function extracts the databases from the device, or uses a existing Android image.
        Thereafter, it parses the log files to store the counted steps in the database.
        """
        print("Android image path (leave empty if live downloading):")
        path_to_image = input()

        path_to_image = path_to_image.rstrip()
        if path_to_image == "":
            print("Extract Huawei Health data from Android phone")
            extractor = extract_app_data.Extractor()
            path = "/data/data/com.huawei.health/files/com.huawei.health/com.huawei.health/log.*"
            logs = extractor.extract_more_files(path, "tmp")
        else:
            print("Extract Huawei Health data from " + path_to_image)
            path_n = os.path.join(path_to_image,
                    "data/data/com.huawei.health/files/com.huawei.health/com.huawei.health/log.*")
            logs = glob.glob(path_n)

        for log in logs:
            print("Process log file " + log)
            log_file = open(log, 'r')

            content = ''
            contents = []
            for line in log_file:  # collects all lines, where SCUI_FitnessDetailInteractor appears
                if 'SCUI_FitnessDetailInteractor' in line and 'null' not in line:
                    line = line.rstrip()
                    if 'datas' in line:
                        content += line.split('|')[3]
                    else:
                        content += line.split('|')[2]
                    if ']' in line:
                        contents.append(content)
                        content = ''

            days = []
            pattern = re.compile(r'{.*?}')
            for cont in contents:  # interprets the lines: content type 3 or 4 to get steps
                for match in re.findall(pattern, cont):
                    content_type = re.search('type=(\d*)', match).group(1)
                    if content_type in ['4', '3']:
                        content_day = re.search('day.=.(.*?),', match).group(1)
                        if content_day in days:
                            continue
                        else:
                            days.append(content_day)
                        steps = re.search('step=(\d*)', match).group(1)
                        time = datetime.strptime(content_day, '%Y-%m-%d %H:%M:%S')
                        self.steps.addData(steps, time)
            log_file.close()
