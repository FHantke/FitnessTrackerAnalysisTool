import struct
import time
import sys
import select
from datetime import datetime
from datetime import timedelta
from Crypto.Cipher import AES
from bluepy.btle import Peripheral, DefaultDelegate, ADDR_TYPE_RANDOM, BTLEException

from Devices.device import Device
from Utils import ble_scanner

# Code is based on https://github.com/creotiv/MiBand2

UUID_SVC_MIBAND2 = "0000fee100001000800000805f9b34fb"
UUID_CHAR_AUTH = "00000009-0000-3512-2118-0009af100700"
UUID_SVC_ALERT = "0000180200001000800000805f9b34fb"
UUID_CHAR_ALERT = "00002a0600001000800000805f9b34fb"
UUID_SVC_HEART_RATE = "0000180d00001000800000805f9b34fb"
UUID_CHAR_HRM_MEASURE = "00002a3700001000800000805f9b34fb"
UUID_CHAR_HRM_CONTROL = "00002a3900001000800000805f9b34fb"
UUID_SVC_BATTERY = "0000181c00001000800000805f9b34fb"
UUID_CHAR_BATTERY = "00000006-0000-3512-2118-0009af100700"
UUID_CHAR_GOAL = "00000003-0000-3512-2118-0009af100700"
UUID_CHAR_ACTIVITY_DATA = "00000005-0000-3512-2118-0009af100700"
UUID_CHAR_FETCH = "00000004-0000-3512-2118-0009af100700"
UUID_CHAR_REAL_TIME_STEPS = "00000007-0000-3512-2118-0009af100700"

CCCD_UUID = 0x2902


class Band(Device):
    """ This class initializes the Peripheral class, which connects to the Mi Band 2.
        Thereafter, it triggers the Peripheral class to extract information from the tracker.
    """

    def __init__(self):
        super().__init__()
        self.lastNotification = datetime.now()
        self.support_heartrate = True
        self.support_steps = True
        self.support_user = False
        self.support_acceleration = True

    def action(self):
        try:
            print("Try to scan for BLE devices")
            ble_scanner.getDevices(False)
        except BTLEException:
            print("You need root permissions to scan BLE.")
        print("Please enter MAC of the tracker device")
        mac = input()

        print('Connecting to ' + mac)
        band = MiBand2BLE(self, mac)
        band.setSecurityLevel(level="medium")

        band.authenticate()
        print(band.state)

        print("Please enter the date you want to start from (i.e. 2018-09-18)")
        start_date = input()
        print('Data from {} are requested.'.format(start_date))

        band.prepare_fetch_activity_data()
        try:
            timestamp = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            timestamp = datetime.strptime("01.01.2018 01:01", "%d.%m.%Y %H:%M")  # the tracker returns a available date
        band.start_fetch_activity_data(timestamp)
        self.lastNotification = datetime.now()
        while band.active and datetime.now() - self.lastNotification < timedelta(seconds=20):  # timeout if no notifi
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                break
            band.waitForNotifications(0.1)
        print("Disconnecting " + mac)
        band.disconnect()
        del band

    def updateLastNotification(self, timestamp):
        self.lastNotification = timestamp

    def addStepData(self, step, timestamp):
        self.steps.addData(step, timestamp)

    def addHRData(self, hr, timestamp):
        self.heartrate.addData(hr, timestamp)

    def addAccelerationData(self, acc, timestamp):
        self.acceleration.addData(acc, timestamp)


class MiBand2BLE(Peripheral):
    """ This class is a sub class of Periperal and communicates with the tracker """
    _KEY = b'\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40\x41\x42\x43\x44\x45'
    _send_key_cmd = struct.pack('<18s', b'\x01\x08' + _KEY)
    _send_rnd_cmd = struct.pack('<2s', b'\x02\x08')
    _send_enc_key = struct.pack('<2s', b'\x03\x08')
    timestamp = ''
    first_timestamp = ''
    last_timestamp = ''
    active = False
    pkg = 0

    def __init__(self, band_class, addr):
        Peripheral.__init__(self, addr, addrType=ADDR_TYPE_RANDOM)
        print("Connected")

        svc = self.getServiceByUUID(UUID_SVC_MIBAND2)
        self.char_auth = svc.getCharacteristics(UUID_CHAR_AUTH)[0]
        self.cccd_auth = self.char_auth.getDescriptors(forUUID=CCCD_UUID)[0]

        self.char_activity_data = self.getCharacteristics(uuid=UUID_CHAR_ACTIVITY_DATA)[0]
        self.cccd_activity_data = self.char_activity_data.getDescriptors(forUUID=CCCD_UUID)[0]
        self.char_fetch = self.getCharacteristics(uuid=UUID_CHAR_FETCH)[0]
        self.cccd_fetch_auth = self.char_fetch.getDescriptors(forUUID=CCCD_UUID)[0]

        self.timeout = 5.0
        self.state = None
        # Enable auth service notifications on startup
        self.auth_notif(True)
        self.waitForNotifications(0.1)  # Let Mi Band time to settle
        self.band_class = band_class

    def auth_notif(self, status):
        if status:
            print("Enabling Auth Service notifications status...")
            self.cccd_auth.write(b"\x01\x00", True)
        elif not status:
            print("Disabling Auth Service notifications status...")
            self.cccd_auth.write(b"\x00\x00", True)
        else:
            print("Something went wrong while changing the Auth Service notifications status...")

    def send_key(self):
        print("Sending Key...")
        self.char_auth.write(self._send_key_cmd)
        self.waitForNotifications(self.timeout)

    def req_rdn(self):
        print("Requesting random number...")
        self.char_auth.write(self._send_rnd_cmd)
        self.waitForNotifications(self.timeout)

    def send_enc_rdn(self, data):
        print("Sending encrypted random number")
        aes = AES.new(self._KEY, AES.MODE_ECB)
        cmd = self._send_enc_key + aes.encrypt(data)
        send_cmd = struct.pack('<18s', cmd)
        self.char_auth.write(send_cmd)
        self.waitForNotifications(self.timeout)

    def authenticate(self):
        self.setDelegate(AuthenticationDelegate(self, self.band_class))
        self.req_rdn()

        while True:
            self.waitForNotifications(0.1)
            if self.state == "AUTHENTICATED":
                return True
            elif self.state:
                return False

    def prepare_fetch_activity_data(self):
        """ The method activates the characteristics to communicate """
        self.cccd_fetch_auth.write(b'\x01\x00', False)
        self.cccd_activity_data.write(b'\x01\x00', False)

    def start_fetch_activity_data(self, start_timestamp):
        """ The method sends the timestamp from which information should be received to trigger the communication """
        print("Trigger activity communication")
        year = start_timestamp.year.to_bytes(2, byteorder='little')
        month = start_timestamp.month.to_bytes(1, byteorder='little')
        day = start_timestamp.day.to_bytes(1, byteorder='little')
        hour = start_timestamp.hour.to_bytes(1, byteorder='little')
        minute = start_timestamp.minute.to_bytes(1, byteorder='little')
        ts = year + month + day + hour + minute
        trigger = b'\x01\x01' + ts + b'\x00\x08'
        self.char_fetch.write(trigger, False)
        self.active = True


class AuthenticationDelegate(DefaultDelegate):

    def __init__(self, device, band_class):
        DefaultDelegate.__init__(self)
        self.device = device
        self.band_class = band_class

    def handleNotification(self, hnd, data):
        """
        This method handles notifications from the tracker.
        :param hnd: Received handle
        :param data: Received data
        """
        # Debug purposes
        # print("HANDLE: " + str(hex(hnd)))
        # print("DATA: " + str(data))

        # The authentication characteristic handles the authentication protocol.
        if hnd == self.device.char_auth.getHandle():
            if data[:3] == b'\x10\x01\x01':
                self.device.req_rdn()
            elif data[:3] == b'\x10\x01\x04':
                self.device.state = "ERROR: Key Sending failed"
            elif data[:3] == b'\x10\x02\x01':
                random_nr = data[3:]
                self.device.send_enc_rdn(random_nr)
            elif data[:3] == b'\x10\x02\x04':
                self.device.state = "ERROR: Something wrong when requesting the random number..."
            elif data[:3] == b'\x10\x03\x01':
                print("Authenticated!")
                self.device.state = "AUTHENTICATED"
            elif data[:3] == b'\x10\x03\x04':
                print("Encryption Key Auth Fail, sending new key...")
                self.device.send_key()
            else:
                self.device.state = "ERROR: Auth failed"
        # The fetch characteristic controls the communication with the activity characteristic.
        # It can trigger the communication.
        elif hnd == self.device.char_fetch.getHandle():
            if data[:3] == b'\x10\x01\x01':
                # get timestamp from what date the data actually is received
                year = int.from_bytes(data[7:9], byteorder='little')
                month = int.from_bytes(data[9:10], byteorder='little')
                day = int.from_bytes(data[10:11], byteorder='little')
                hour = int.from_bytes(data[11:12], byteorder='little')
                minute = int.from_bytes(data[12:13], byteorder='little')
                self.device.timestamp = datetime(year, month, day, hour, minute)
                self.device.first_timestamp = datetime(year, month, day, hour, minute)
                print("Fetch data from {}-{}-{} {}:{}".format(year, month, day, hour, minute))
                self.device.char_fetch.write(b'\x02', False)
            elif data[:3] == b'\x10\x02\x01':
                self.device.active = False
                return
            else:
                print("Unexpected data on handle " + hex(hnd) + ": " + str(data))
                return
        # The activity characteristic sends the previews recorded information from one given timestamp until now.
        elif hnd == self.device.char_activity_data.getHandle():
            if len(data) % 4 is not 1:
                if self.device.last_timestamp > datetime.now() - timedelta(minutes=5):
                    self.device.active = False
                    return
                print("Trigger more communication")
                time.sleep(1)
                t = self.device.last_timestamp + timedelta(minutes=1)
                self.device.start_fetch_activity_data(t)
            else:
                pkg = self.device.pkg
                # pkg_head = int.from_bytes(data[0:1], byteorder='little')
                # print("Packet: {} (real) - {} (head)".format(pkg, pkg_head))
                self.device.pkg += 1
                i = 1
                while i < len(data):
                    index = int(pkg) * 4 + (i - 1) / 4
                    timestamp = self.device.first_timestamp + timedelta(minutes=index)
                    self.device.last_timestamp = timestamp
                    # timestamp = timestamp + timedelta(hours=1)
                    # category = int.from_bytes(data[i:i + 1], byteorder='little')
                    intensity = int.from_bytes(data[i + 1:i + 2], byteorder='little')
                    steps = int.from_bytes(data[i + 2:i + 3], byteorder='little')
                    heart_rate = int.from_bytes(data[i + 3:i + 4], byteorder='little')

                    print("{}: acceleration {}; steps {}; heart rate {};".format(
                        timestamp.strftime('%d.%m - %H:%M'),
                        intensity,
                        steps,
                        heart_rate)
                    )

                    self.band_class.addHRData(heart_rate, timestamp)
                    self.band_class.addStepData(steps, timestamp)
                    self.band_class.addAccelerationData(intensity, timestamp)
                    self.band_class.updateLastNotification(datetime.now())
                    i += 4

                    d = datetime.now().replace(second=0, microsecond=0) - timedelta(minutes=5)
                    if timestamp == d:
                        self.device.active = False
                        return
        else:
            print("Unhandled Response on handle " + hex(hnd) + ": " + str(data))
