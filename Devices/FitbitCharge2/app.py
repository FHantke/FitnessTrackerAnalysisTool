from Devices.device import Device
from datetime import datetime
from datetime import timedelta
from Utils import extract_app_data
import urllib.request as url_req
from urllib.error import URLError
import sqlite3
import os
import sys


class App(Device):
    """ This class receives data from the Fitbit application, interprets it and stores it in the database """
    def __init__(self):
        super().__init__()
        self.support_heartrate = False
        self.support_custom_attributes = True
        self.support_steps = False
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
            print("Extract Fitbit Mobile data from Android phone")
            extractor = extract_app_data.Extractor()
            databases = "/data/data/com.fitbit.FitbitMobile/databases/"
            db_exercise = extractor.extract_one_file(databases + "exercise_db", output_path="tmp")
            db_sleep = extractor.extract_one_file(databases + "sleep", output_path="tmp")
            db_fitbit_db = extractor.extract_one_file(databases + "fitbit-db", output_path="tmp")
            db_social_db = extractor.extract_one_file(databases + "social_db", output_path="tmp")
        else:
            print("Extract Fitbit Mobile data from " + path_to_image)
            databases = os.path.join(path_to_image, "data/data/com.fitbit.FitbitMobile/databases/")
            db_exercise = os.path.join(databases, "exercise_db")
            db_sleep = os.path.join(databases, "sleep")
            db_fitbit_db = os.path.join(databases, "fitbit-db")
            db_social_db = os.path.join(databases, "social_db")

        conn = sqlite3.connect(db_fitbit_db)
        c = conn.cursor()   
        res = c.execute("SELECT DATE_TIME/1000,         \
                                VALUE,                  \
                                OBJECT_TYPE             \
                                FROM TIME_SERIES_OBJECT \
                                ORDER BY DATE_TIME, OBJECT_TYPE")
        self.decode_time_series(res)
        res = c.execute("SELECT FULL_NAME,          \
                                PROFILE_PHOTO_LINK, \
                                CITY,               \
                                COUNTRY_LABEL,      \
                                TIME_CREATED/1000,  \
                                DATE_OF_BIRTH/1000, \
                                HEIGHT,             \
                                TIME_UPDATED/1000,  \
                                GENDER,             \
                                HEIGHT_UNIT,        \
                                WEIGHT_UNIT         \
                                FROM PROFILE ORDER BY ENCODED_ID")
        self.decode_user(res)
        conn.close()

        conn = sqlite3.connect(db_social_db)
        c = conn.cursor()   
        res = c.execute("SELECT WEIGHT FROM USER_PROFILE ORDER BY ENCODED_ID")
        for row in res:
            self.user.setWeight(str(row[0]) + " " + self.weightUnit)
        conn.close()

        conn = sqlite3.connect(db_sleep)
        c = conn.cursor()   
        res = c.execute("SELECT START_TIME/1000,\
                            DURATION            \
                            FROM SLEEP_LOG")
        self.decode_sleep(res)
        conn.close()

        conn = sqlite3.connect(db_exercise)
        c = conn.cursor()
        res = c.execute("SELECT es._id,         \
                            es.START_TIME/1000, \
                            es.STOP_TIME/1000,  \
                            TIME/1000,          \
                            LATITUDE,           \
                            LONGITUDE           \
                            FROM EXERCISE_EVENT ee JOIN EXERCISE_SEGMENT es             \
                            ON ee._id >= es.START_EVENT_ID AND ee._id <= es.END_EVENT_ID\
                            WHERE TIME >= es.START_TIME AND TIME <= es.STOP_TIME        \
                            ORDER BY ee._id")
        self.decode_track(res)
        conn.close()

    def decode_time_series(self, data):
        """ Decodes time series, which holds summarized information of all days. """
        print("Process time series data")
        cur_date = None
        value = ""
        definition = ""
        for row in data:
            object_type = row[2]
            if object_type not in [0, 4, 6, 8]:
                continue
            date = datetime.fromtimestamp(row[0])
            if date != cur_date:
                if value != "":
                    self.custom_attributes.addData(definition, value)
                definition = "Summary of {} (not accurate)".format(date.strftime('%Y-%m-%d'))
                value = ""
                cur_date = date
            if object_type == 0:
                value += "Weight: {}; ".format(row[1])
            elif object_type == 4 and str(row[1]) != "0.0":
                value += "Steps: {}; ".format(row[1])
            elif object_type == 6 and str(row[1]) != "0.0":
                value += "Floors: {}; ".format(row[1])
            elif object_type == 8 and str(row[1]) != "0.0":
                value += "Kilometers: {}; ".format(row[1])

    def decode_user(self, data):
        """ Interprets user's information """
        print("Process user data")
        for row in data:
            try:
                req = url_req.Request(row[1], headers={'User-Agent':"Magic Browser"})
                con = url_req.urlopen(req)
                main_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
                pic_name = "{}_{}".format(row[0], row[5])
                pic_path = os.path.join(main_path, "Report/static/pic/{}.jpg".format(pic_name))
                pic_file = open(pic_path, 'wb')
                pic_file.write(con.read())
                pic_file.close()
            except URLError as e:
                pic_name = ""
                print("Can not load profile picture, due to the following failure:")
                print(e)

            create_time = datetime.fromtimestamp(row[4]).strftime('%Y-%m-%d %H:%M:%S')
            birthday = datetime.fromtimestamp(row[5]).strftime('%Y-%m-%d')
            last_login = datetime.fromtimestamp(row[7]).strftime('%Y-%m-%d %H:%M:%S')
            self.weightUnit = row[10]
            self.user.setName(row[0])
            self.user.setAvatar(pic_name)
            self.user.setCity(row[2])
            self.user.setCountry(row[3])
            self.user.setCreate_Time(create_time)
            self.user.setBirthday(birthday)
            self.user.setHeight(str(row[6]) + " " + str(row[9]))
            self.user.setLast_Login(last_login)
            self.user.setGender(row[8])
        
    def decode_sleep(self, data):
        """ Interprets sleep information """
        print("Process sleep data")
        for row in data:
            sleep_start = datetime.fromtimestamp(row[0])
            sleep_end = datetime.fromtimestamp(row[0]) + timedelta(milliseconds=(int(row[1])))
            self.sleep.addData(sleep_start, sleep_end)
        
    def decode_track(self, data):
        """ Decodes activity track's position data """
        print("Process GPS and track data")
        new_track = ""
        for row in data:
                tr_id = str(row[0])
                if new_track != tr_id:
                    # Custom attr, due to the fact that first and last track point
                    # in track had other time - strange behaviour
                    definition = "Real begin of track " + tr_id
                    begin = datetime.fromtimestamp(row[1]).strftime('%Y-%m-%d %H:%M:%S')
                    self.custom_attributes.addData(definition, begin)
                    definition = "Real end of track " + tr_id
                    end = datetime.fromtimestamp(row[2]).strftime('%Y-%m-%d %H:%M:%S')
                    self.custom_attributes.addData(definition, end)
                    new_track = tr_id

                timestamp = datetime.fromtimestamp(row[3])
                lat = row[4]
                lon = row[5]
                self.position.addData(timestamp, lat, lon, tr_id)
