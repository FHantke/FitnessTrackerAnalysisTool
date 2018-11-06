import base64
import sqlite3
import json
import os
import sys
import glob
import math
import urllib.request as url_req
from urllib.error import URLError
from datetime import timedelta, datetime
from Utils import geohash, extract_app_data
from Devices.device import Device


class App(Device):
    """ This class receives data from the Mi Fit application, interprets it and stores it in the database """
    def __init__(self):
        super().__init__()
        self.support_heartrate = True
        self.support_steps = True
        self.support_acceleration = True
        self.support_sleep = True
        self.support_user = True
        self.support_position = True

    def action(self):
        """
        First, the function extracts the databases from the device, or uses a existing Android image.
        Thereafter, it obtains data from various databases and hands it to the interpreting functions.
        """
        print("Android image path (leave empty if live downloading):")
        path_to_image = input()
        if path_to_image == "":
            print("Extract Mi Fit data from Android phone")
            extractor = extract_app_data.Extractor()
            path_to_db = extractor.extract_one_file(
                    "/data/data/com.xiaomi.hm.health/databases/origin_db_*",
                    output_path="tmp")
        else:
            print("Extract Mit Fit data from " + path_to_image)
            path_to_db = os.path.join(path_to_image,
                    "data/data/com.xiaomi.hm.health/databases/origin_db_*")
            path_to_db = glob.glob(path_to_db)
            print(path_to_db)
            path_to_db = path_to_db[0]

        conn = sqlite3.connect(path_to_db)
        c = conn.cursor()   
        res = c.execute("SELECT NAME,           \
                                BIRTHDAY,       \
                                AVATAR_URL,     \
                                GENDER,         \
                                HEIGHT,         \
                                WEIGHT,         \
                                CITY,           \
                                CREAT_TIME,     \
                                LAST_LOGIN_TIME \
                                FROM USER_INFOS")
        self.decode_user(res)
        res = c.execute("SELECT DATE, DATA, DATA_HR, SUMMARY FROM DATE_DATA")
        self.decode_data(res)    
        res = c.execute("SELECT TIME, HR FROM HEART_RATE")
        self.decode_hr_table(res)   
        res = c.execute("SELECT DATE,           \
                                COSTTIME,       \
                                ENDTIME,        \
                                LOCATION,       \
                                STATISTICS,     \
                                BULKLL,         \
                                BULKTIME,       \
                                BULKHR,         \
                                BULKPAUSE,      \
                                d.TRACKID       \
                                FROM TRACKDATA d\
                                JOIN TRACKRECORD r ON d.TRACKID = r.TRACKID")
        self.decode_track(res)

    def decode_track(self, data):
        """
        This method decodes information from the track tables.
        It stores longitude and latitude with data like heart rate
        """
        print("Process GPS and track data")
        for row in data:
            date = row[0]
            costtime = timedelta(seconds=row[1])
            endtime = datetime.fromtimestamp(row[2])
            location = row[3]
            bulkll = row[5]
            bulktime = row[6]
            bulkhr = row[7]
            bulkpause = row[8]
            track_id = row[9]
            
            # pause: pauses the user pressed during an activity
            pause_time_sec = 0
            pause_array = []
            if bulkpause:
                pause = bulkpause.split(';')
                for p in pause[:-1]:
                    p = p.split(',')
                    pause_time_sec += int(p[1])
                    pause_array.append(datetime.fromtimestamp(int(p[0])))
                    pause_array.append(timedelta(seconds=int(p[1])))
            pause_time = timedelta(seconds=pause_time_sec)

            # heart rate: heart rate data is stored in a string split by ;
            # every heart rate datum is stored as <second>:<heart rate>, while second is the second since activity start
            heartrate = 0
            heartrate_sec= 0
            timestamp = endtime-costtime-pause_time
            for h in bulkhr.split(';'):
                hr_sec = h.split(',')[0]
                hr = h.split(',')[1]
                if hr != '':
                    heartrate += int(hr)
                if hr_sec != '':
                    heartrate_sec += int(hr_sec)
                else:
                    heartrate_sec += 1
                self.heartrate.addData(heartrate, timestamp + timedelta(seconds=heartrate_sec))

            """ Explanation:
            start lat and lon are stored in location as string with comma.
            all lat and lon are stored in bulkll as integer.
            first lat and lon in bulkll are the same as in location, the following are delta to the previews position.
            As bulkll stores integers, it was not clear where to put the comma.
            Therefore, first the position of the comma is searched in the string from location.
            The position must be counted from the back and not the front, as seen in the following example:
            10.10 - 0.20 = 0.90 -> The position stays the same if counted from the back
            """
            timestamp = endtime-costtime-pause_time
            bulktime = bulktime.split(';')
            p_idx = 0
            lat, lon = geohash.decode(location)
            lat_position_of_comma = str(lat).find('.')
            lon_position_of_comma = str(lon).find('.')
            lat_value = int(bulkll.split(';')[0].split(',')[0])
            lat_position_of_comma -= len(str(lat_value))  # Negative number to count from the back
            lon_value = int(bulkll.split(';')[0].split(',')[1])
            lon_position_of_comma -= len(str(lon_value))  # Negative number to count from the back

            for idx, ll in enumerate(bulkll.split(';')[1:]):
                secs = int(bulktime[idx])
                timestamp += timedelta(seconds=secs)
                if len(pause_array) > p_idx and timestamp > pause_array[p_idx]:
                    timestamp += pause_array[p_idx+1]
                    p_idx += 2
                lat_value += int(ll.split(',')[0])
                lon_value += int(ll.split(',')[1])
                lat_fin = str(lat_value)[:lat_position_of_comma] + "." + str(lat_value)[lat_position_of_comma:]
                lon_fin = str(lon_value)[:lon_position_of_comma] + "." + str(lon_value)[lon_position_of_comma:]
                self.position.addData(timestamp, lat_fin, lon_fin, track_id)

    def decode_user(self, data):
        """ Interprets user data and stores it in the database """
        print("Process user data")
        for row in data:
            try:
                req = url_req.Request(row[2], headers={'User-Agent':"Magic Browser"})
                con = url_req.urlopen(req)
                main_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
                pic_name = "{}_{}".format(row[0], row[1])
                pic_path = os.path.join(main_path, "Report/static/pic/{}.jpg".format(pic_name))
                pic_file = open(pic_path, 'wb')
                pic_file.write(con.read())
                pic_file.close()
            except URLError:
                pic_name = ""
                print("Can not load profile picture, due to the following failure:")
                print(e)

            create_time = datetime.fromtimestamp(int(row[7])).strftime('%Y-%m-%d %H:%M:%S')
            last_login = datetime.fromtimestamp(int(row[8])).strftime('%Y-%m-%d %H:%M:%S')

            gender = "Male" if row[3] == 1 else "Female"

            self.user.setName(row[0])               # Name
            self.user.setBirthday(row[1])         # Birthday
            self.user.setAvatar(pic_name)           # Avatar
            self.user.setGender(gender)             # Gender
            self.user.setHeight(str(row[4]) + " cm")             # Height
            self.user.setWeight(str(round(row[5], 2)) + " kg")             # Weight
            self.user.setCity(row[6])               # City
            self.user.setCreate_Time(create_time)   # Create Time
            self.user.setLast_Login(last_login)     # Last Login
                
    def decode_hr_table(self, data):
        """ Interprets on demand measured heart rate and stores it in the database """
        print("Process heart rate data from heart rate table")
        for row in data:
            timestamp = datetime.fromtimestamp(row[0])
            hr = row[1]
            self.heartrate.addData(hr, timestamp)

    def decode_data(self, data):
        """ Hands several data to the corresponding decoding method """
        for row in data:
            day = datetime.strptime(row[0], '%Y-%m-%d')
            print("Process heart rate, steps and sleep from " + row[0])
            step_data = row[1]            
            self.decode_data_step_data(step_data, day)
            
            hr_data = row[2]
            self.decode_data_hr_data(hr_data, day)
            
            summary_data = json.loads(row[3])
            self.decode_data_summary_data(summary_data)
            
    def decode_data_summary_data(self, data):
        """ Interprets daily summary data to obtain sleep and store is in the database """
        sleep_data = data["slp"]
        sleep_start = datetime.fromtimestamp(sleep_data["st"])
        sleep_end = datetime.fromtimestamp(sleep_data["ed"])
        self.sleep.addData(sleep_start, sleep_end)

    def decode_data_step_data(self, data, day):
        """ Interprets step data to obtain acceleration and steps per minute """
        data = json.loads(data)[0]["value"]
        data_bin = bytearray(data, 'UTF-8')
        data_bin = bytearray(base64.b64decode(data_bin))
        i = 0
        while i < len(data_bin)/3:
            timestamp = day+timedelta(minutes=i)
            type = str(data_bin[i*3])
            acceleleration = str(data_bin[i*3+1])
            step = str(data_bin[i*3+2])
            self.steps.addData(step, timestamp)
            self.acceleration.addData(acceleleration, timestamp)
            i += 1

    def decode_data_hr_data(self, data, day):
        """ Interprets heart rate data from the data table """
        i = 0
        while i < len(data):        
            hr = int(data[i])
            timestamp = day+timedelta(minutes=i)
            self.heartrate.addData(hr, timestamp)
            i += 1
