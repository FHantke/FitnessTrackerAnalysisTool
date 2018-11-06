from flask import render_template
from flask import Flask
from flask import request
import json

""" This flask application directs the user to the Fitbit authorization server.
    It catches the authorize code and returns it back to the origin python module.
"""

app = Flask(__name__)
fitbit_code = ""


def run():
    global fitbit_code
    app.run(host='localhost')
    return fitbit_code


def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()


@app.route("/")
@app.route("/index")
def index_route():
    global fitbit_code
    fitbit_code = request.args.get('code')
    if fitbit_code is not None:
        shutdown_server()
        return "You can close this side."
    config_file = open('main.config', 'r')
    config = json.loads(config_file.read())
    clientID = config['fitbit_clientID']
    return render_template('fitbit_index.html', clientID=clientID)
