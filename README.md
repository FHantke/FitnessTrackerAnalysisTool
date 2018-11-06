# Fitness Tracker Analysis Tool

This tool was designed and developed to analyze fitness trackers and offer useful information for a forensic report.

## Installation

The tool is written in Python 3. It is recommended to use virtualenv to run the tool, so that it runs in an independent enviroment.

### Virtualenv
`sudo apt-get install python3-pip`

`sudo pip3 install virtualenv`

### Fitness Tracker Analysis Tool
Then, to install the analysis tool, just run:
`make all`

### Fitbit Web API
- Register an app at https://dev.fitbit.com/apps/new
- Enter your data (OAuth 2.0 Application Type = Server; Callback URL = http://127.0.0.1:5000; Default Access Type = Read-Only)
- Copy client ID and secret key to main.config
- To obtain intraday data from another logged in account than yours, you need extended permissions. You can request extended permissions at https://dev.fitbit.com/build/reference/web-api/help/

### Google Maps API
- You need a Google developer account
- Go to https://console.cloud.google.com/home/dashboard where you can create a new project
- Go to the API Manager on your project's page and activate Maps JavaScript API from the API library
- Copy the API key to main.config

## Usage
Run the tool by starting `main.py` with the correct parameters.
You can first list all supported devices or methods with `--list_devices` or `--list_methods`.
Afterwards, you can start `main.py --device <your device> --method <choosen method>`.
The tool will extract and store the found information and subsequently present them on a self hosted webpage.

```
usage: main.py [-h] [-d DEVICE] [-m METHOD] [--db_path DB_PATH] [-l LOG] [-D]
               [-M] [--only_report]

optional arguments:
  -h, --help                    show this help message and exit
  -d DEVICE, --device DEVICE    The device, which you want to investigate
  -m METHOD, --method METHOD    The methode, with which you want to investigate
  --db_path DB_PATH             The path, where the database is going to be saved
  -l LOG, --log LOG             Path where log should be created
  -D, --list_devices            Lists all avaible devices
  -M, --list_methods            List all avaible methods
  --only_report                 Starts only the web server
```

## Development
The analysis tool was designed the way that anyone can easily extend the program with new device modules.
Therefore, add a new sub-directory Devices with the company's name and the name of your tracker.
In this sub-directory you can implement your methods, which are python classes.
Each method needs its own file, with one method class, which has the same name as the file.
Furthermore, it needs to be a child of the Device class and it needs to contain an action method.
For more information, please read the source code in the device modules, therfore it is well documented.

```
from Devices.device import Device

class App(Device):
    """ This class receives data from the Mi Fit application, interprets it and stores it in the database """
    def __init__(self):
        super().__init__()
        self.support_heartrate = True
        
    def action(self):
        print("Doing action")
```

## License
This project is licensed under MIT.
Third Party Software which are distributed under their own terms can be found under the following paths:
- Report/static/css/bootstrap/
- Report/static/js/bootstrap/
- Report/static/js/jquery/
- Report/static/js/zingchart/
- Utils/geohash.py

The MIT License (MIT)

Copyright (c) 2018 Florian Hantke

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

