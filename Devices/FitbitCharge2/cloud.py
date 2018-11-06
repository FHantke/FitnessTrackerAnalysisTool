from Database.database import Heartrate
from Devices.device import Device
from Devices.FitbitCharge2.API import flask_app
import urllib.request as url_req
from datetime import datetime
from datetime import timedelta
import base64
import os
import sys
import requests
import json


class Cloud(Device):
    """ The class receives information from the Fitbit cloud and stores them in the database """
    fitbit_api_header = ""

    def __init__(self):
        super().__init__()
        self.support_heartrate = True
        self.support_steps = True
        self.support_sleep = True
        self.support_user = True
        self.support_custom_attributes = True
        self.support_position = False
        config_file = open('main.config', 'r')
        config = json.loads(config_file.read())
        self.clientID = config['fitbit_clientID']
        self.secretKey = config['fitbit_secretKey']

    def action(self):
        """
        First, the function requires a start and end date.
        Then, it starts a Flask app to obtain the authentication token.
        With this token, it requests individual information to hand them to the interpretation function.
        """
        print("Enter the start date (i.e. 2018-07-15)")
        start_day = input()
        print("Enter the end date (i.e. 2018-07-15)")
        end_day = input()

        print("Start to request data from {} to {}".format(start_day, end_day))
        self.custom_attributes.addData("Requested information from this day", start_day)
        self.custom_attributes.addData("Requested information until this day", end_day)

        fitbit_code = flask_app.run()

        auth_head = base64.b64encode(bytes(self.clientID + ':' + self.secretKey, 'utf-8')).decode('utf-8')
        headers = {'Authorization': 'Basic ' + auth_head,
                   'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'clientId': self.clientID,
            'grant_type': 'authorization_code',
            'redirect_uri': 'http://127.0.0.1:5000',
            'code': fitbit_code
        }
        res = requests.post("https://api.fitbit.com/oauth2/token", headers=headers, data=data)
        json_data = json.loads(res.text)
        if 'access_token' not in json_data:
            print("Something went wrong wih your authentication")
            print(json_data)
        else:
            print("Successful authenticated")
        token = json_data['access_token']
        self.fitbit_api_header = {'Authorization': 'Bearer ' + token}

        url = "https://api.fitbit.com/1/user/-/profile.json"
        json_data = self.request_api(url)
        self.interpret_user_data(json_data)

        url = "https://api.fitbit.com/1/user/-/devices.json"
        json_data = self.request_api(url)
        self.interpret_devices_data(json_data)

        url = "https://api.fitbit.com/1/user/-/sleep/date/{}/{}.json".format(start_day, end_day)
        json_data = self.request_api(url)
        self.interpret_sleep_data(json_data)

        days = []
        start_day_dt = datetime.strptime(start_day, "%Y-%m-%d")
        end_day_dt = datetime.strptime(end_day, "%Y-%m-%d")
        cur_day = start_day_dt
        while cur_day <= end_day_dt:
            days.append(cur_day.strftime("%Y-%m-%d"))
            cur_day += timedelta(days=1)

        for day in days:
            url = "https://api.fitbit.com/1/user/-/activities/heart/date/{}/1d/1sec.json".format(day)
            json_data = self.request_api(url)
            if not self.interpret_heartrate_data(json_data):
                break
            url = "https://api.fitbit.com/1/user/-/activities/steps/date/{}/1d/1min.json".format(day)
            json_data = self.request_api(url)
            if not self.interpret_steps_data(json_data):
                break

    @staticmethod
    def getJsonData(data, key):
        """
        Helper function, which checks if a key exists in JSON before returning
        :param data: JSON format
        :param key: requested key
        :return: the value if key is valid, "" else
        """
        ret = ""
        if key in data:
            ret = data[key]
        return ret

    def request_api(self, url):
        """
        Helper method, which requests data from the API and returns it in JSON format.
        :param url: requested url
        :return: result as JSON format
        """
        res = requests.get(url, headers=self.fitbit_api_header)
        json_data = json.loads(res.text)
        return json_data

    def interpret_user_data(self, data):
        """ Interprets requested user data and stores them in the database """
        print("Process user data")
        user = data['user']
        avatar = ""
        if 'avatar640' in user:
            avatar = data['user']['avatar640']
        elif 'avatar150' in user:
            avatar = data['user']['avatar150']
        elif 'avatar' in user:
            avatar = data['user']['avatar']

        age = self.getJsonData(user, 'age')
        country = self.getJsonData(user, 'country')
        city = self.getJsonData(user, 'city')
        full_name = self.getJsonData(user, 'fullName')
        weight = self.getJsonData(user, 'weight')
        height = self.getJsonData(user, 'height')
        gender = self.getJsonData(user, 'gender')
        member_since = self.getJsonData(user, 'memberSince')
        date_of_birth = self.getJsonData(user, 'dateOfBirth')

        pic_name = ""
        if avatar != "":
            req = url_req.urlopen(avatar)
            main_path = os.path.dirname(os.path.abspath(sys.modules['__main__'].__file__))
            pic_name = "{}_{}".format(full_name, date_of_birth)
            pic_path = os.path.join(main_path, "Report/static/pic/{}.jpg".format(pic_name))
            pic_file = open(pic_path, 'wb')
            pic_file.write(req.read())
            pic_file.close()

        self.user.setName(full_name)
        self.user.setAge(age)
        self.user.setBirthday(date_of_birth)
        self.user.setAvatar(pic_name)
        self.user.setGender(gender)
        self.user.setHeight(height)
        self.user.setWeight(weight)
        self.user.setCity(city)
        self.user.setCountry(country)
        self.user.setCreate_Time(member_since)

    def interpret_devices_data(self, data):
        """ Interprets the requested device information and stores them in the database """
        print("Process device data")
        definition = "List of user's Fitbit devices"
        val = ""
        for device in data:
            val += "Name: {}, Last time synced: {}" \
                .format(device['deviceVersion'], device['lastSyncTime'])
        self.custom_attributes.addData(definition, val)

    def interpret_sleep_data(self, data):
        """ Interprets the requested sleep information and stores them in the database """
        print("Process sleep data")
        sleep = data['sleep']
        for day in sleep:
            start_sleep = self.getJsonData(day, 'startTime')
            end_sleep = self.getJsonData(day, 'endTime')
            if start_sleep != "" and end_sleep != "":
                start_sleep_dt = datetime.strptime(start_sleep, "%Y-%m-%dT%H:%M:%S.%f")
                end_sleep_dt = datetime.strptime(end_sleep, "%Y-%m-%dT%H:%M:%S.%f")
                self.sleep.addData(start_sleep_dt, end_sleep_dt)

    def interpret_heartrate_data(self, data):
        """ Interprets the requested hear rate information and stores them in the database """
        day = datetime.strptime(data['activities-heart'][0]['dateTime'], "%Y-%m-%d")
        day_data = self.getJsonData(data, "activities-heart-intraday")
        if day == "":
            print("Your Fitbit API key only allows daily data, not intraday")
            print("You need to grant permission from Fitbit.")
            print("Get the permission as described in README")
            return False
        print("Process heart rate from ".format(data['activities-heart'][0]['dateTime']))
        dataset = self.getJsonData(day_data, "dataset")
        i = 0
        for d in dataset:
            i += 1
            delta = d['time'].split(':')
            h = int(delta[0])
            m = int(delta[1])
            s = int(delta[2])
            time = day + timedelta(hours=h, minutes=m, seconds=s)
            heartrate = d['value']
            self.heartrate.addData(heartrate, time)
        return True

    def interpret_steps_data(self, data):
        """ Interprets the requested step information and stores them in the database """
        day = datetime.strptime(data['activities-steps'][0]['dateTime'], "%Y-%m-%d")
        day_data = self.getJsonData(data, "activities-steps-intraday")
        if day == "":
            print("Your Fitbit API key only allows daily data, not per minute")
            print("You need to grant permission from Fitbit")
            return False
        print("Process steps from {}".format(data['activities-steps'][0]['dateTime']))
        dataset = self.getJsonData(day_data, "dataset")
        i = 0
        for d in dataset:
            i += 1
            delta = d['time'].split(':')
            h = int(delta[0])
            m = int(delta[1])
            s = int(delta[2])
            time = day + timedelta(hours=h, minutes=m, seconds=s)
            steps = d['value']
            self.steps.addData(steps, time)
        return True
