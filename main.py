from Logger.logger import Logger
from Database.database import DBHandler
from Database.database import ReportRequests
import importlib
import argparse
import sys
import os
from Report import index


def collect_arg_options(detail):
    """
    Collects all available devices and methods dynamically.
    :param detail: True to print also the methods of the devices
    :return: An array with an entry for each device and its methods.
             [[device_1, method_1_1, method_1_2], [device_2, method_2_1]]
    """
    dir_path = os.path.dirname(os.path.realpath(__file__))
    all_args = []
    for d in os.listdir("{}/Devices".format(dir_path)):
        device_path = "{}/Devices/{}".format(dir_path, d)
        if not os.path.isdir(device_path) or d == "__pycache__":
            continue
        arg = [d]
        if detail:
            for m in os.listdir(device_path):
                if os.path.isfile("{}/{}".format(device_path, m)) and m != "module.py":
                    arg.append("{}".format(m.replace('.py', '')))
        all_args.append(arg)
    return all_args


def extract_data(device_name, method_name, db_path):
    """
    Calls the selected method from the investigated device.
    Thereafter, it handles the interaction with the database module.
    :param device_name: The name of the device module
    :param method_name: The name of the method
    :param db_path: The path to the program's database
    :return: The current database hash to check it in the report module.
             If no data was stored, the hash is an empty string.
    """
    print("Start to extract data from " + device_name + " with " + method_name)
    db_handler = DBHandler(db_path, device_name, method_name)
    classname = method_name[0].upper() + method_name[1:]
    imp = importlib.import_module("Devices.{}.{}".format(device_name, method_name))
    method = eval("imp.{}".format(classname))()
    method.action()

    print("Store extracted data")
    db_hash = db_handler.save_data()

    if method.support_heartrate:
        heartrate = method.getHeartrate()
        db_hash = db_handler.save_data(heartrate)
    if method.support_steps:
        steps = method.getSteps()
        db_hash = db_handler.save_data(steps)
    if method.support_user:
        user = method.getUser()
        db_hash = db_handler.save_data(user)
    if method.support_sleep:
        sleep = method.getSleep()
        db_hash = db_handler.save_data(sleep)
    if method.support_acceleration:
        acceleration = method.getAcceleration()
        db_hash = db_handler.save_data(acceleration)
    if method.support_position:
        position = method.getPosition()
        db_hash = db_handler.save_data(position)
    if method.support_custom_attributes:
        custom_attributes = method.getCustomAttributes()
        db_hash = db_handler.save_data(custom_attributes)

    return db_hash


def main():
    """
    The main method handles all arguments of the call.
    It triggers the two phases, extracting data and reporting data.
    usage: main.py [-h] [-d DEVICE] [-m METHOD] [--db_path DB_PATH]
               [--db_hash DB_HASH] [-l LOG] [-D] [-M] [--only_report]
    """
    parser = argparse.ArgumentParser(
        description='The program was developed to extract data from common fitness trackers and show the findings in standardized reports.'
                    'It works in two phases, first obtaining and storing information in a database.'
                    'Second it starts a Flask application with HTML reports.')
    parser.add_argument('-d', '--device', help='The device, which you want to investigate.')
    parser.add_argument('-m', '--method', help='The method, with which you want to investigate')
    parser.add_argument('--db_path', help='Change the path, where the database shouled be stored.')
    parser.add_argument('--db_hash', help='The sha265 hash of the given database.')
    parser.add_argument('-l', '--log', help='Change the path where log files should be stored.')
    parser.add_argument('-D', '--list_devices', action='store_true',
                        help='Lists all available devices')
    parser.add_argument('-M', '--list_methods', action='store_true',
                        help='List all available methods')
    parser.add_argument('--only_report', action='store_true',
                        help='Skips the first phase and only start the web server and report.')
    args = parser.parse_args()

    # Initial logger
    if args.log is not None:
        main_log = os.path.join(args.log, "main.log")
    else:
        main_log = "main.log"

    # Use the same log since flask writes both std.
    sys.stdout = Logger(main_log, err=False)
    sys.stderr = Logger(main_log, err=True)

    print("Start analysis: " + str(sys.argv))

    # List all devices and methods
    if args.list_devices:
        devices = collect_arg_options(False)
        for device in devices:
            print(device[0])
        sys.exit(0)

    if args.list_methods:
        devices = collect_arg_options(True)
        for device in devices:
            for i, method in enumerate(device):
                print(method if i == 0 else "\t" + method)
        sys.exit(0)

    # Optional database path
    if args.db_path:
        db_path = args.db_path
    else:
        db_path = "data.db"

    # Optional database hash, only useful if --only_report
    db_hash = ""
    if args.db_hash:
        db_hash = args.db_hash

    # Checks if method and device are correct
    if not args.only_report:
        if args.device is None and args.method is None:
            print("You added a method. Please add a device you want to use with --device")
            sys.exit(0)
        if args.device is None and args.method is not None:
            print("Please add device and method you want to use with --device and --method")
            sys.exit(0)
        if args.device is not None and args.method is None:
            print("You added a device. Please add a method you want to use with --method")
            sys.exit(0)
        correct = False
        devices = collect_arg_options(True)
        for device in devices:
            if device[0] == args.device:
                for method in device:
                    if method == args.method:
                        correct = True
        if correct is False:
            print("Your device or method is not available. Probably it is spelled wrong.")
            sys.exit(0)
        db_hash = extract_data(args.device, args.method, db_path)

    # Starts report
    reportDb = ReportRequests(db_path, db_hash)
    index.init(reportDb, main_log)
    index.app.run(host="localhost")
    print("Last database is: " + reportDb.origin_hash)
    print("End analysis")


if __name__ == "__main__":
    main()
