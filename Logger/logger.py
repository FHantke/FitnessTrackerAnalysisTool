from datetime import datetime
import sys


class Logger(object):
    """
    Handles the logging of the program.
    Is initialized in main.py
    """
    def __init__(self, path, err):
        if err:
            self.terminal = sys.stderr
        else:
            self.terminal = sys.stdout
        self.path = path

    def write(self, message):
        self.terminal.write(message)
        message = message.strip('\n')
        if message is None or message is '':
            return
        log = open(self.path, "a")
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log.write(time + " " + message + "\n")
        log.close()

    def flush(self):
        pass
