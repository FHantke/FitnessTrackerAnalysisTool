from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask import redirect
from datetime import datetime, timedelta
import math
import copy
import json

app = Flask(__name__)
TIME_OF_THE_ANALYSIS = None

STANDARD_LABEL = {"text": "null",
                  "default-value": "0",
                  "font-family": "Georgia",
                  "font-size": 10,
                  "vertical-align": "top",
                  "background-color": "white",
                  "border-width": 2,
                  "border-color": "#FFFFFF",
                  "border-radius": "5px",
                  "x": "90%",
                  "y": "15%",
                  "height": "7%",
                  "width": "5%",
                  "padding": "5%"}


def init(db, main):
    global DatabaseModule
    global main_log
    DatabaseModule = db
    main_log = main


def perzentile(data, p):
    if len(data) == 0:
        return 0
    data.sort()
    np = (len(data) * p) - 1
    if np.is_integer():
        np = int(np)
        ret = (data[np] + data[np + 1]) / 2
    else:
        ret = data[math.ceil(np)]
    return ret


@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def index():
    """
    The home page lists all analyses and links to the reports.
    Furthermore, the opportunity is give to compare analyses.
    :return: Either the rendered index.html or the redirect to a specific analysis
    """
    global TIME_OF_THE_ANALYSIS
    time_of_aly = request.values.get('time_of_aly')
    if time_of_aly is not None:  # redirect the user to specific analysis report
        TIME_OF_THE_ANALYSIS = time_of_aly
        return redirect(url_for('user_report'))
    try:
        device_data = DatabaseModule.get_devices()
    except ValueError as e:
        print(e)
        return str(e)
    return render_template(
        'index.html',
        title="Fitness Tracker Report",
        device_data=device_data,
        hash=DatabaseModule.origin_hash)


@app.route("/shutdown", methods=['GET', 'POST'])
def shutdown():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "You can close this side."


@app.route("/remove/<analysis_id>", methods=['GET', 'POST'])
def remove_analysis(analysis_id):
    """
    The link to remove a specific analysis
    :param analysis_id: The time_of_analysis of the specific analysis
    :return: Redirect to index
    """
    DatabaseModule.remove_analysis(analysis_id)
    return redirect(url_for('index'))


@app.route("/custom", methods=['GET', 'POST'])
def custom_report():
    """ The custom report lists all custom attributes in a table. """
    global TIME_OF_THE_ANALYSIS
    if TIME_OF_THE_ANALYSIS is None:
        return redirect(url_for('index'))
    try:
        data = DatabaseModule.get_custom_attr(TIME_OF_THE_ANALYSIS)
    except ValueError as e:
        print(e)
        return str(e)
    return render_template(
        'report_custom.html',
        title="Custom Attributes Report",
        data=data)


@app.route("/log", methods=['GET', 'POST'])
def log_report():
    """ The log report shows the log file. The user can filter and search the log. """
    log_main = open(main_log, 'r').readlines()
    data_main = []
    for line in log_main:
        split_line = line.split(' ')
        data_main.append([' '.join(split_line[:2]), ' '.join(split_line[2:])])
    return render_template(
        'log.html',
        title="Logs",
        data_main=data_main)


@app.route("/user", methods=['GET', 'POST'])
def user_report():
    """ The user report lists information about the trackers/app user. """
    global TIME_OF_THE_ANALYSIS
    if TIME_OF_THE_ANALYSIS is None:
        return redirect(url_for('index'))
    try:
        data = DatabaseModule.get_user(TIME_OF_THE_ANALYSIS)
    except ValueError as e:
        print(e)
        return str(e)
    for user in data:
        user["pic"] = url_for('static', filename="pic/{}.jpg".format(user["pic"]))
    return render_template(
        'report_user.html',
        title="User Report",
        data=data)


@app.route("/data", methods=['GET', 'POST'])
def data_report():
    """ The data report displays several charts with the found data """
    global TIME_OF_THE_ANALYSIS
    if TIME_OF_THE_ANALYSIS is None:
        return redirect(url_for('index'))

    # Initial option
    timestamp_1 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=90)
    timestamp_2 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    accuracy = "Hours"
    flag_heartrate = True
    flag_steps = True
    flag_sleep = True
    flag_acceleration = True

    # Optional option
    if request.method == 'POST':
        timestamp_1 = datetime.strptime(request.form["from"], '%Y-%m-%d')
        timestamp_2 = datetime.strptime(request.form["until"], '%Y-%m-%d')
        accuracy = request.form["accuracy"]
        flag_heartrate = "heartrate" in request.form
        flag_steps = "steps" in request.form
        flag_sleep = "sleep" in request.form
        flag_acceleration = "accelerration" in request.form
    from_date = timestamp_1.timestamp() * 1000

    # Calculation of sleep boxplot
    try:
        sleep_begin, sleep_end = DatabaseModule.get_all_sleep(TIME_OF_THE_ANALYSIS)
    except ValueError as e:
        print(e)
        return str(e)
    sleep_data = []
    if len(sleep_begin) > 0:
        sleep_begin_q1 = (perzentile(sleep_begin, 0.25) + 39600) * 1000
        sleep_begin_median = (perzentile(sleep_begin, 0.5) + 39600) * 1000
        sleep_begin_q3 = (perzentile(sleep_begin, 0.75) + 39600) * 1000
        sleep_begin_min = (min(sleep_begin) + 39600) * 1000
        sleep_begin_max = (max(sleep_begin) + 39600) * 1000
        sleep_end_q1 = (perzentile(sleep_end, 0.25) + 39600) * 1000
        sleep_end_median = (perzentile(sleep_end, 0.5) + 39600) * 1000
        sleep_end_q3 = (perzentile(sleep_end, 0.75) + 39600) * 1000
        sleep_end_min = (min(sleep_end) + 39600) * 1000
        sleep_end_max = (max(sleep_end) + 39600) * 1000

        sleep_data = [
            [sleep_begin_min, sleep_begin_q1, sleep_begin_median, sleep_begin_q3, sleep_begin_max],
            [sleep_end_min, sleep_end_q1, sleep_end_median, sleep_end_q3, sleep_end_max]]

    # Preperation of the main chart. Different order depending on the selected options.
    detail_data = []
    detail_labels = []
    plot_pos = 0
    if flag_heartrate:
        try:
            data_heartrate = DatabaseModule.get_heartrate(timestamp_1, timestamp_2, accuracy, TIME_OF_THE_ANALYSIS)
        except ValueError as e:
            print(e)
            return str(e)
        detail_data.append({"values": data_heartrate,
                            "text": "Heartrate",
                            "background-color": "#DD0000"})
        label = copy.deepcopy(STANDARD_LABEL)
        label["text"] = "Heartrate:<br>%plot-{}-value".format(plot_pos)
        label["border-color"] = "#DD0000"
        label["x"] = "{}%".format(90 - plot_pos * 5)
        detail_labels.append(label)
        plot_pos += 1

    if flag_steps:
        try:
            data_steps = DatabaseModule.get_steps(timestamp_1, timestamp_2, accuracy, TIME_OF_THE_ANALYSIS)
        except ValueError as e:
            print(e)
            return str(e)
        detail_data.append({"values": data_steps, "text": "Steps", "background-color": "#0000DD"})
        label = copy.deepcopy(STANDARD_LABEL)
        label["text"] = "Steps:<br>%plot-{}-value".format(plot_pos)
        label["border-color"] = "#0000DD"
        label["x"] = "{}%".format(90 - plot_pos * 5)
        detail_labels.append(label)
        plot_pos += 1

    if flag_sleep:
        try:
            data_sleep = DatabaseModule.get_sleep(timestamp_1, timestamp_2, accuracy, TIME_OF_THE_ANALYSIS)
        except ValueError as e:
            print(e)
            return str(e)
        detail_data.append({"values": data_sleep, "text": " Sleep", "background-color": "#00DD00"})
        label = copy.deepcopy(STANDARD_LABEL)
        label["text"] = "Sleep:<br>%plot-{}-value".format(plot_pos)
        label["border-color"] = "#00DD00"
        label["x"] = "{}%".format(90 - plot_pos * 5)
        detail_labels.append(label)
        plot_pos += 1

    if flag_acceleration:
        try:
            data_acceleration = DatabaseModule.get_acceleration(timestamp_1, timestamp_2, accuracy, TIME_OF_THE_ANALYSIS)
        except ValueError as e:
            print(e)
            return str(e)
        detail_data.append({"values": data_acceleration,
                            "text": "Acceleration",
                            "background-color": "#DD00DD"})
        label = copy.deepcopy(STANDARD_LABEL)
        label["text"] = "Acceleration:<br>%plot-{}-value".format(plot_pos)
        label["border-color"] = "#DD00DD"
        label["x"] = "{}%".format(90 - plot_pos * 5)
        detail_labels.append(label)
        plot_pos += 1

    # Preparation of calendar chart
    calendar_data = []
    calendar_start = timestamp_2.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    calendar_end = timestamp_2.replace(month=12, day=31, hour=23, minute=59, second=59, microsecond=0)
    calendar_year = calendar_start.year
    try:
        calendar_days = DatabaseModule.get_steps(calendar_start, calendar_end, "Days", TIME_OF_THE_ANALYSIS)
    except ValueError as e:
        print(e)
        return str(e)
    for day in calendar_days:
        calendar_data.append([calendar_start.strftime('%Y-%m-%d'), day])
        calendar_start += timedelta(days=1)

    return render_template(
        'report_data.html',
        title="Data Report",
        calendar_year=calendar_year,
        calendar_data=calendar_data,
        sleep_data=sleep_data,
        detail_data=detail_data,
        detail_labels=detail_labels,
        from_date=from_date,
        from_str=timestamp_1.strftime("%Y-%m-%d"),
        until_str=timestamp_2.strftime("%Y-%m-%d"),
        accuracy=accuracy)


@app.route("/map", methods=['GET', 'POST'])
def map_report():
    """ The map report shows all found activity paths on Google Maps. """
    global TIME_OF_THE_ANALYSIS
    if TIME_OF_THE_ANALYSIS is None:
        return redirect(url_for('index'))
    timestamp_1 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=365)
    timestamp_2 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    if request.method == 'POST':
        timestamp_1 = datetime.strptime(request.form["from"], '%Y-%m-%d')
        timestamp_2 = datetime.strptime(request.form["until"], '%Y-%m-%d')

    try:
        gps_data = DatabaseModule.get_period_tracks(TIME_OF_THE_ANALYSIS, timestamp_1, timestamp_2)
        all_tracks = DatabaseModule.get_all_tracks(TIME_OF_THE_ANALYSIS)
    except ValueError as e:
        print(e)
        return str(e)

    # Preparation for bubble chart
    bubbles = [[],[]]
    ids = [[],[]]
    deltas = [i[3] for i in all_tracks]
    duration_q3 = (perzentile(deltas, 0.75))
    for track in all_tracks:
        start = datetime.strptime(track[0], '%Y-%m-%d %H:%M:%S')
        start_milli = start.timestamp() * 1000
        if duration_q3 < track[3]:
            bubbles[1].append([start_milli % 86400000, int(start.strftime('%w')), track[3]])
            ids[1].append(track[2])
        else:
            bubbles[0].append([start_milli % 86400000, int(start.strftime('%w')), track[3]])
            ids[0].append(track[2])

    config_file = open('main.config', 'r')
    config = json.loads(config_file.read())
    google_maps_apiKey = config['google_maps_apiKey']

    return render_template('report_maps.html',
                           title="Map Report",
                           gps_data=gps_data,
                           bubbles=bubbles,
                           ids=ids,
                           duration_q3=duration_q3,
                           google_maps_apiKey=google_maps_apiKey,
                           from_str=timestamp_1.strftime("%Y-%m-%d"),
                           until_str=timestamp_2.strftime("%Y-%m-%d"),
                           all_tracks=all_tracks)


@app.route("/map/<int:track_id>", methods=['GET', 'POST'])
def map_id_report(track_id):
    """ The map id report shows a specific track with its statistics """
    global TIME_OF_THE_ANALYSIS
    if TIME_OF_THE_ANALYSIS is None:
        return redirect(url_for('index'))
    accuracy = "Minutes"
    if request.method == 'POST':
        accuracy = request.form["accuracy"]

    try:
        gps_data = DatabaseModule.get_specific_track(TIME_OF_THE_ANALYSIS, track_id)
    except ValueError as e:
        print(e)
        return str(e)
    from_date = gps_data[0][3]
    timestamp_1 = datetime.fromtimestamp(from_date / 1000)
    timestamp_2 = datetime.fromtimestamp(gps_data[-1][3] / 1000)

    chart_data = []
    labels = []
    data_heartrate = DatabaseModule.get_heartrate(timestamp_1, timestamp_2, accuracy, TIME_OF_THE_ANALYSIS)
    chart_data.append({"values": data_heartrate, "text": "Heartrate", "background-color": "#DD0000"})
    label = copy.deepcopy(STANDARD_LABEL)
    label["text"] = "Heartrate:<br>%plot-1-value"
    label["border-color"] = "#DD0000"
    label["x"] = "85%"
    labels.append(label)

    data_steps = DatabaseModule.get_steps(timestamp_1, timestamp_2, accuracy, TIME_OF_THE_ANALYSIS)
    chart_data.append({"values": data_steps, "text": "Steps", "background-color": "#0000DD"})
    label = copy.deepcopy(STANDARD_LABEL)
    label["text"] = "Steps:<br>%plot-2-value"
    label["border-color"] = "#0000DD"
    label["x"] = "80%"
    labels.append(label)

    config_file = open('main.config', 'r')
    config = json.loads(config_file.read())
    google_maps_apiKey = config['google_maps_apiKey']

    return render_template('report_maps_id.html',
                           title="Map Report",
                           track_id=track_id,
                           gps_data=gps_data,
                           labels=labels,
                           google_maps_apiKey=google_maps_apiKey,
                           chart_data=chart_data,
                           from_date=from_date,
                           accuracy=accuracy)


@app.route("/compare", methods=['GET', 'POST'])
def compare_report():
    """ The compare report displays information on the selected analysis to compare them """
    if request.method == 'GET':
        return redirect(url_for('index'))

    timestamp_1 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=5)
    timestamp_2 = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    accuracy = "Minutes"
    if "from" in request.form:
        timestamp_1 = datetime.strptime(request.form["from"], '%Y-%m-%d')
    if "until" in request.form:
        timestamp_2 = datetime.strptime(request.form["until"], '%Y-%m-%d')
    if "accuracy" in request.form:
        accuracy = request.form["accuracy"]
    from_date = timestamp_1.timestamp() * 1000

    colors = ["#0000DD", "#00DD00", "#DD0000", "#DD00DD", "#DDDD00", "#00DDDD",
              "#000066", "#006600", "#660000", "#660066", "#666600", "#006666"]

    step_data = []
    sleep_data = []
    acceleration_data = []
    heartrate_data = []
    labels = []
    devices = []

    i = 0
    length = len(colors)
    requested_analyses = []
    for item in request.form:
        if item.split(':')[0] != 'a':
            continue
        requested_analyses.append(item)
        aly_time = item.split(':')[1]
        aly_device = item.split(':')[2]
        aly_method = item.split(':')[3]
        devices.append([aly_device + " " + aly_method, colors[i % length]])

        try:
            data_1 = DatabaseModule.get_steps(timestamp_1, timestamp_2, accuracy, aly_time)
            data_2 = DatabaseModule.get_heartrate(timestamp_1, timestamp_2, accuracy, aly_time)
            data_3 = DatabaseModule.get_sleep(timestamp_1, timestamp_2, accuracy, aly_time, to_string=True)
            data_4 = DatabaseModule.get_acceleration(timestamp_1, timestamp_2, accuracy, aly_time)
        except ValueError as e:
            print(e)
            return str(e)

        step_data.append(
            {"values": data_1,
             "text": aly_device + " " + aly_method,
             "background-color": colors[i % length]})
        heartrate_data.append(
            {"values": data_2,
             "text": aly_device + " " + aly_method,
             "background-color": colors[i % length]})
        sleep_data.append(
            {"values": data_3,
             "text": aly_device + " " + aly_method,
             "background-color": colors[i % length],
             "alpha": "0.5"})
        acceleration_data.append(
            {"values": data_4,
             "text": aly_device + " " + aly_method,
             "background-color": colors[i % length]})
        label = copy.deepcopy(STANDARD_LABEL)
        label["text"] = "%plot-{}-value".format(i)
        label["border-color"] = colors[i % length]
        label["x"] = "{}%".format(90 - i * 5)
        labels.append(label)
        i += 1

    return render_template(
        'report_compare.html',
        title="Compare Report",
        from_str=timestamp_1.strftime("%Y-%m-%d"),
        until_str=timestamp_2.strftime("%Y-%m-%d"),
        accuracy=accuracy,
        labels=labels,
        step_data=step_data,
        sleep_data=sleep_data,
        acceleration_data=acceleration_data,
        heartrate_data=heartrate_data,
        from_date=from_date,
        devices=devices,
        requested_analyses=requested_analyses)
