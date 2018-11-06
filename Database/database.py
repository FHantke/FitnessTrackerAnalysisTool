from datetime import datetime
from datetime import timedelta
import hashlib
import sqlite3
import os
import math

# from typing import Dict, Any

""" TABLES
Every table is represent as one class with getter and setter methods.
"""


class Sleep:
    start = []
    end = []
    wakeup_day = []

    def addData(self, start, end):
        self.start.append(start)
        self.end.append(end)
        self.wakeup_day.append(end.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0))

    def getStart(self):
        return self.start

    def setStart(self, start):
        self.start.append(start)

    def getEnd(self):
        return self.end

    def setEnd(self, end):
        self.end.append(end)

    def getWakeupDay(self):
        return self.wakeup_day

    def setWakeupDay(self, end):
        self.wakeup_day.append(end.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0))


class Position:
    latitude = []
    longitude = []
    timestamp = []
    tr_id = []

    def addData(self, time, lat, lon, tr_id):
        self.latitude.append(lat)
        self.longitude.append(lon)
        self.timestamp.append(time)
        self.tr_id.append(tr_id)

    def getLatitude(self):
        return self.latitude

    def setLatitude(self, lat):
        self.latitude.append(lat)

    def getLongitude(self):
        return self.longitude

    def setLongitude(self, lon):
        self.longitude.append(lon)

    def getTimestamp(self):
        return self.timestamp

    def setTimestamp(self, time):
        self.timestamp.append(time)

    def getTrId(self):
        return self.tr_id

    def setTrId(self, tr_id):
        self.tr_id.append(tr_id)


class User:
    name = ""
    birthday = ""
    avatar = ""
    height = ""
    weight = ""
    city = ""
    age = ""
    country = ""
    gender = ""
    create_time = None
    last_login = None

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name

    def getBirthday(self):
        return self.birthday

    def setBirthday(self, birthday):
        self.birthday = birthday

    def getAge(self):
        if self.age == "":
            try:  # try to calculate age
                dt = datetime.strptime(self.birthday, '%Y-%m-%d')
                days = (datetime.now() - dt).days
                years = math.floor(days * 0.00273791)
                self.age = "Calculated by this program: {}".format(years)
            except ValueError:
                pass
        return self.age

    def setAge(self, age):
        self.age = age

    def getAvatar(self):
        return self.avatar

    def setAvatar(self, avatar):
        self.avatar = avatar

    def getHeight(self):
        return self.height

    def setHeight(self, height):
        self.height = height

    def getGender(self):
        return self.gender

    def setGender(self, gender):
        self.gender = gender

    def getWeight(self):
        return self.weight

    def setWeight(self, weight):
        self.weight = weight

    def getCity(self):
        return self.city

    def setCity(self, city):
        self.city = city

    def getCountry(self):
        return self.country

    def setCountry(self, country):
        self.country = country

    def getCreate_Time(self):
        return self.create_time

    def setCreate_Time(self, create_time):
        self.create_time = create_time

    def getLast_Login(self):
        return self.last_login

    def setLast_Login(self, last_login):
        self.last_login = last_login


class Heartrate:
    hr = []
    time = []

    def addData(self, hr, time):
        self.hr.append(hr)
        self.time.append(time)

    def getTime(self):
        return self.time

    def setTime(self, hr):
        self.hr.append(hr)

    def getHR(self):
        return self.hr

    def setHR(self, time):
        self.time.append(time)


class Acceleration:
    acceleration = []
    time = []

    def addData(self, acceleration, time):
        self.acceleration.append(acceleration)
        self.time.append(time)

    def getTime(self):
        return self.time

    def setTime(self, time):
        self.time.append(time)

    def getAcceleration(self):
        return self.acceleration

    def setAcceleration(self, acceleration):
        self.acceleration.append(acceleration)


class Steps:
    steps = []
    time = []

    def addData(self, steps, time):
        self.steps.append(steps)
        self.time.append(time)

    def getTime(self):
        return self.time

    def setTime(self, time):
        self.time.append(time)

    def getSteps(self):
        return self.steps

    def setSteps(self, steps):
        self.steps.append(steps)


class CustomAttribute:
    value = []
    definition = []

    def addData(self, definition, value):
        self.definition.append(definition)
        self.value.append(value)

    def getDefinition(self):
        return self.definition

    def setDefinition(self, definition):
        self.definition.append(definition)

    def getValue(self):
        return self.value

    def setValue(self, value):
        self.value.append(value)


""" END OF TABLES ===================================="""


class ReportRequests:
    """
    Handles the requests from the report module
    """

    def __init__(self, db_path, origin_hash=""):
        self.db_path = db_path
        if origin_hash == "":
            self.origin_hash = self.sha256(self.db_path)
        else:
            self.origin_hash = origin_hash

    @staticmethod
    def sha256(fname):
        hash_sha256 = hashlib.sha256()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    @staticmethod
    def decide_time(accuracy):
        time_format = "%Y-%m-%d %H:00:00"
        timedelta_filler = timedelta(hours=1)
        if accuracy == "Seconds":
            time_format = "%Y-%m-%d %H:%M:%S"
            timedelta_filler = timedelta(seconds=1)
        elif accuracy == "Minutes":
            time_format = "%Y-%m-%d %H:%M:00"
            timedelta_filler = timedelta(minutes=1)
        elif accuracy == "Hours":
            time_format = "%Y-%m-%d %H:00:00"
            timedelta_filler = timedelta(hours=1)
        elif accuracy == "Days":
            time_format = "%Y-%m-%d 00:00:00"
            timedelta_filler = timedelta(days=1)
        return time_format, timedelta_filler

    def get_acceleration(self, timestamp_1, timestamp_2, accuracy, toa):
        time_format, timedelta_filler = self.decide_time(accuracy)
        cmd = "SELECT strftime('{}',timestamp) as t, MAX(value) FROM acceleration ".format(time_format)
        cmd += "WHERE timestamp > '{}' AND timestamp < '{}' ".format(timestamp_1, timestamp_2)
        cmd += "AND time_of_aly = {} GROUP BY t ORDER BY t".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_acceleration = c.execute(cmd)

        old_time = timestamp_1
        data_acceleration = []
        for row in c_acceleration:
            cur_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            while old_time < cur_time:
                old_time += timedelta_filler
                data_acceleration.append('0')

            data_acceleration.append(row[1])
            old_time = cur_time + timedelta_filler

        while old_time < timestamp_2:
            data_acceleration.append('0')
            old_time += timedelta_filler
        conn.close()
        return data_acceleration

    def get_heartrate(self, timestamp_1, timestamp_2, accuracy, toa):
        time_format, timedelta_filler = self.decide_time(accuracy)
        cmd = "SELECT strftime('{}',timestamp) as t, MAX(value) FROM heartrate ".format(time_format)
        cmd += "WHERE timestamp > '{}' AND timestamp < '{}' ".format(timestamp_1, timestamp_2)
        cmd += "AND time_of_aly = {} GROUP BY t ORDER BY t".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_heartrate = c.execute(cmd)

        old_time = timestamp_1
        data_heartrate = []
        for row in c_heartrate:
            cur_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            while old_time < cur_time:
                old_time += timedelta_filler
                data_heartrate.append('0')

            data_heartrate.append(row[1])
            old_time = cur_time + timedelta_filler

        while old_time < timestamp_2:
            data_heartrate.append('0')
            old_time += timedelta_filler
        conn.close()
        return data_heartrate

    def get_steps(self, timestamp_1, timestamp_2, accuracy, toa):
        time_format, timedelta_filler = self.decide_time(accuracy)
        cmd = "SELECT strftime('{}',timestamp) as t, SUM(value) FROM steps ".format(time_format)
        cmd += "WHERE timestamp > '{}' AND timestamp < '{}' ".format(timestamp_1, timestamp_2)
        cmd += "AND time_of_aly = {} GROUP BY t ORDER BY t".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_steps = c.execute(cmd)

        old_time = timestamp_1
        data_steps = []
        for row in c_steps:
            cur_time = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            while old_time < cur_time:
                old_time += timedelta_filler
                data_steps.append('0')

            data_steps.append(row[1])
            old_time = cur_time + timedelta_filler

        while old_time < timestamp_2:
            data_steps.append('0')
            old_time += timedelta_filler
        conn.close()
        return data_steps

    def get_sleep(self, timestamp_1, timestamp_2, accuracy, toa, to_string=False):
        time_format, timedelta_filler = self.decide_time(accuracy)
        cmd = "SELECT strftime('%s',start) as s, strftime('%s', end) as e FROM sleep "
        cmd += "WHERE e > '{}'".format(timestamp_1.timestamp())
        cmd += "AND s < '{}' ".format(timestamp_2.timestamp())
        cmd += "AND start != end AND time_of_aly = {} ORDER BY s".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_sleep = c.execute(cmd)

        cur_time = timestamp_1
        row = c_sleep.fetchone()
        if row is None:
            cur_start = datetime.fromtimestamp(0)
            cur_end = datetime.fromtimestamp(0)
        else:
            # 7200 due to two hours difference
            cur_start = datetime.fromtimestamp(int(row[0]) - 7200)
            cur_end = datetime.fromtimestamp(int(row[1]) - 7200)
        data_sleep = []
        while cur_time != timestamp_2:
            if cur_end < cur_time:
                row = c_sleep.fetchone()
                if row is not None:
                    # 7200 due to two hours difference
                    cur_start = datetime.fromtimestamp(int(row[0]) - 7200)
                    cur_end = datetime.fromtimestamp(int(row[1]) - 7200)
            if cur_start <= cur_time < cur_end:
                data_sleep.append('asleep' if to_string else '1')
            else:
                data_sleep.append('awake' if to_string else '0')
            cur_time += timedelta_filler
        conn.close()
        return data_sleep

    def get_all_sleep(self, toa):
        cmd = "SELECT strftime('%s', datetime(start, '+12 hours'))%86400, \
                strftime('%s', datetime(end, '+12 hours'))%86400 \
                FROM sleep WHERE start != end \
                AND time_of_aly = {}".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_sleep = c.execute(cmd)

        sleep_end = []
        sleep_begin = []
        for row in c_sleep:
            sleep_begin.append(row[0])
            sleep_end.append(row[1])
        conn.close()
        return sleep_begin, sleep_end

    def get_user(self, toa):
        cmd = "SELECT name, \
                birthday,   \
                age,        \
                gender,     \
                height,     \
                weight,     \
                city,       \
                country,    \
                create_time,\
                last_login, \
                avatar      \
                FROM user   \
                WHERE time_of_aly = {}".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_user = c.execute(cmd)

        data = []
        for u in c_user:
            user = {}
            user["name"] = u[0]
            user["birthday"] = u[1]
            user["age"] = u[2]
            user["gender"] = u[3]
            user["height"] = u[4]
            user["weight"] = u[5]
            user["city"] = u[6]
            user["country"] = u[7]
            user["create_time"] = u[8]
            user["last_login"] = u[9]
            user["pic"] = u[10]
            data.append(user)
        conn.close()
        return data

    def get_devices(self):
        cmd = "SELECT name, method, time_of_aly FROM device"
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_device = c.execute(cmd)
        device_data = []
        for d in c_device:
            data = {}
            data["name"] = d[0]
            data["method"] = d[1]
            data["timestamp_str"] = datetime.fromtimestamp(d[2]).strftime("%Y-%m-%d %H:%M")
            data["timestamp"] = d[2]
            device_data.append(data)
        conn.close()
        return device_data

    def get_custom_attr(self, toa):
        cmd = "SELECT attribute, value FROM custom_attributes \
                WHERE time_of_aly = {}".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_custom = c.execute(cmd)
        data = []
        for cust in c_custom:
            data.append([cust[0], cust[1]])
        conn.close()
        return data

    def get_all_tracks(self, toa):
        cmd = "SELECT MIN(timestamp), MAX(timestamp), tr_id FROM position "
        cmd += "WHERE time_of_aly = {} GROUP BY tr_id".format(toa)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_tracks = c.execute(cmd)

        all_tracks = []
        for row in c_tracks:
            start = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
            end = datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S')
            duration = math.floor((end - start).seconds / 60)
            all_tracks.append([row[0], row[1], row[2], duration])
        conn.close()
        return all_tracks

    def get_period_tracks(self, toa, timestamp_1, timestamp_2):
        cmd = "SELECT latitude, longitude, timestamp, tr_id FROM position "
        cmd += "WHERE timestamp > '{}' AND timestamp < '{}' ".format(timestamp_1, timestamp_2)
        cmd += "AND time_of_aly = {} GROUP BY timestamp".format(toa)
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_gps = c.execute(cmd)

        gps_data = []
        track_data = []
        cur_tr_id = None
        for row in c_gps:
            if cur_tr_id is None:
                cur_tr_id = row[3]
            if cur_tr_id != row[3]:
                cur_tr_id = row[3]
                gps_data.append(track_data)
                track_data = []

            track_data.append([row[0], row[1], row[2], row[3]])
        conn.close()
        return gps_data

    def get_specific_track(self, toa, track_id):
        cmd = "SELECT latitude, longitude, timestamp, tr_id FROM position "
        cmd += "WHERE tr_id ='{}' AND time_of_aly = {} ".format(track_id, toa)
        cmd += "ORDER BY timestamp"
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c_gps = c.execute(cmd)

        gps_data = []
        timestamp_1 = None
        for row in c_gps:
            if timestamp_1 is None:
                timestamp_1 = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
            timestamp_2 = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S')
            unix_stamp = timestamp_2.timestamp() * 1000
            gps_data.append([row[0], row[1], row[2], unix_stamp])
        conn.close()
        return gps_data

    def remove_analysis(self, analysis_id):
        db_hash = self.sha256(self.db_path)
        if db_hash != self.origin_hash:
            raise ValueError("The sha256 of the database has changed surprisingly")

        print("Remove analysis with id " + analysis_id)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c2 = conn.cursor()

        cmd_sel = "SELECT tbl_name FROM sqlite_master WHERE tbl_name <> 'sqlite_sequence'"
        c_tables = c.execute(cmd_sel)
        for row in c_tables:
            cmd_del = "DELETE FROM {} WHERE time_of_aly='{}'".format(row[0], analysis_id)
            c2.execute(cmd_del)
        conn.commit()
        conn.close()

        new_hash = self.sha256(self.db_path)
        self.origin_hash = new_hash


class DBHandler:
    """
    The class handles the table classes and stores them in a SQLite database
    """
    path = ""
    time_of_aly = -1

    def __init__(self, db_path, device, method):
        print("database is stored at " + db_path)
        self.path = db_path
        self.device = device
        self.method = method
        need_setup = not os.path.exists(db_path)
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        if need_setup:
            self.setup_database()

        self.time_of_aly = datetime.now().timestamp()

    def save_analyses(self):
        self.conn.commit()

    def setup_database(self):
        print("init database")
        # DEVICE
        self.c.execute("CREATE TABLE device(            \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                method TEXT NOT NULL,                   \
                name TEXT NOT NULL,                     \
                company TEXT NOT NULL)")
        # USER
        self.c.execute("CREATE TABLE user(              \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                name TEXT,                              \
                birthday DATE,                          \
                age INTEGER,                            \
                gender TEXT,                            \
                height TEXT,                            \
                weight TEXT,                            \
                city TEXT,                              \
                country TEXT,                           \
                create_time DATE,                       \
                last_login DATE,                        \
                avatar TEXT)")
        # ACCELERATION
        self.c.execute("CREATE TABLE acceleration(      \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                value INTEGER NOT NULL,                 \
                timestamp DATE)")
        # STEPS
        self.c.execute("CREATE TABLE steps(             \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                value INTEGER NOT NULL,                 \
                timestamp DATE)")
        # SLEEP
        self.c.execute("CREATE TABLE sleep(             \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                wakeup_day DATE,                        \
                start DATE,                             \
                end DATE)")
        # POSITION
        self.c.execute("CREATE TABLE position(          \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                latitude REAL, longitude REAL,          \
                timestamp DATE,                         \
                tr_id INTEGER)")
        # HEARTRATE
        self.c.execute("CREATE TABLE heartrate(         \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                value INTEGER NOT NULL,                 \
                timestamp DATE)")
        # CUSTOM ATTRIBUTES
        self.c.execute("CREATE TABLE custom_attributes( \
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   \
                time_of_aly DAY NOT NULL,               \
                attribute INTEGER NOT NULL,             \
                value TEXT NOT NULL)")
        self.conn.commit()

    def insert(self, query):
        if not query.startswith("INSERT"):
            raise Exception("Only insert")
        self.c.execute(query)
        self.conn.commit()

    def save_data(self, data=None):
        if data is None:
            self.c.execute("INSERT INTO device (name, company, method, time_of_aly) VALUES (?, ?, ?, ?)",
                           (self.device, "", self.method, self.time_of_aly))
        elif isinstance(data, Heartrate):
            print("Save heartrate")
            heartrate = data.getHR()
            time = data.getTime()
            for i in range(len(heartrate)):
                if heartrate[i] >= 250:
                    heartrate[i] = 0
                self.c.execute("INSERT INTO heartrate (time_of_aly, value, timestamp) VALUES (?, ?, ?)",
                               (self.time_of_aly, heartrate[i], time[i]))
        elif isinstance(data, CustomAttribute):
            print("Save custom attribute")
            definitions = data.getDefinition()
            values = data.getValue()
            for i in range(len(definitions)):
                self.c.execute("INSERT INTO custom_attributes (time_of_aly, attribute, value) VALUES (?,  ?, ?)",
                               (self.time_of_aly, definitions[i], values[i]))
        elif isinstance(data, User):
            print("Save user")
            self.c.execute("INSERT INTO user (  \
                    time_of_aly,                \
                    name,                       \
                    birthday,                   \
                    age,                        \
                    gender,                     \
                    height,                     \
                    weight,                     \
                    city,                       \
                    country,                    \
                    create_time,                \
                    last_login,                 \
                    avatar)                     \
                    VALUES (?, ?, ?, ?, ?, ?,   \
                    ?, ?, ?, ?, ?, ?)",
                           (self.time_of_aly,
                            data.getName(),
                            data.getBirthday(),
                            data.getAge(),
                            data.getGender(),
                            data.getHeight(),
                            data.getWeight(),
                            data.getCity(),
                            data.getCountry(),
                            data.getCreate_Time(),
                            data.getLast_Login(),
                            data.getAvatar()))
        elif isinstance(data, Acceleration):
            print("Save acceleration")
            acceleration = data.getAcceleration()
            time = data.getTime()
            for i in range(len(acceleration)):
                self.c.execute("INSERT INTO acceleration (time_of_aly, value, timestamp) VALUES (?, ?, ?)",
                               (self.time_of_aly, acceleration[i], time[i]))
        elif isinstance(data, Steps):
            print("Save steps")
            steps = data.getSteps()
            time = data.getTime()
            for i in range(len(steps)):
                self.c.execute("INSERT INTO steps (time_of_aly, value, timestamp) VALUES (?, ?, ?)",
                               (self.time_of_aly, steps[i], time[i]))
        elif isinstance(data, Position):
            print("Save position")
            latitude = data.getLatitude()
            longitude = data.getLongitude()
            timestamp = data.getTimestamp()
            tr_id = data.getTrId()
            for i in range(len(latitude)):
                self.c.execute("INSERT INTO position (          \
                        time_of_aly,                            \
                        latitude,                               \
                        longitude,                              \
                        timestamp,                              \
                        tr_id)                                  \
                        VALUES (?, ?, ?, ?, ?)",
                               (self.time_of_aly, latitude[i], longitude[i], timestamp[i], tr_id[i]))
        elif isinstance(data, Sleep):
            print("Save sleep")
            start = data.getStart()
            end = data.getEnd()
            wakeup_day = data.getWakeupDay()
            for i in range(len(wakeup_day)):
                self.c.execute("INSERT INTO sleep (time_of_aly, wakeup_day, start, end) VALUES (?, ?, ?, ?)",
                               (self.time_of_aly, wakeup_day[i], start[i], end[i]))
        else:
            print("data from {} is not supported yet".format(data))
        self.conn.commit()

        # calc hash
        hash_sha256 = hashlib.sha256()
        with open(self.path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        print("current database hash is {}".format(hash_sha256.hexdigest()))
        return hash_sha256.hexdigest()

    def __del__(self):
        self.conn.close()
        # os.remove(self.path)
