

import commands
import flask
import glob
import os
import json
import uuid

import preload


app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.send_from_directory('static', 'index.html')


@app.route('/apps-available')
def apps_available():
    available = [
        x.split(os.path.sep)[1:] for x in (glob.glob(os.path.join("gaia-raw", "apps", "*"))
            + glob.glob(os.path.join("gaia-raw", "external-apps", "*"))
            + glob.glob(os.path.join("gaia-raw", "showcase_apps", "*")))
        if not x.endswith(".py")]

    return flask.jsonify({"apps-available": available})


@app.route('/customize/', methods=['POST'])
def customize():
    name = str(uuid.uuid4())
    fullpath = os.path.join("outputs", name)
    os.mkdir(fullpath)
    os.mkdir(os.path.join(fullpath, "distribution"))
    os.mkdir(os.path.join(fullpath, "external-apps"))
    homescreens_path = os.path.join(fullpath, "distribution", "homescreens.json")
    fl = file(homescreens_path, "w")
    fl.write(flask.request.data)
    fl.close()
    parsed = json.loads(flask.request.data)
    for homescreen in parsed["homescreens"]:
        for appname in homescreen:
            if appname and appname[0] == "external-apps":
                ## TODO symlink the external apps
                result = commands.getoutput(
                    "cd %(fullpath)s%(sep)sexternal-apps && ln -s ..%(sep)s..%(sep)s..%(sep)sexternal-apps%(sep)s%(app-name)s" % {
                        "fullpath": fullpath,
                        "sep": os.path.sep,
                        "app-name": appname[1]})
                app.logger.debug(result)
    result = commands.getoutput(
        "cd %(fullpath)s && zip -r %(name)s.zip distribution external-apps" % {
            "fullpath": fullpath, "sep": os.path.sep, "name": name})
    app.logger.debug(result)
    result = commands.getoutput(
        "mv %(fullpath)s%(sep)s%(name)s.zip outputs" % {
            "fullpath": fullpath, "sep": os.path.sep, "name": name})
    app.logger.debug(result)

    return flask.jsonify({"profile-url": flask.url_for("profiles", name=name)})


@app.route('/profiles/<name>.zip')
def profiles(name):
    name = name + ".zip"
    if os.path.exists(os.path.join("outputs", name)):
        return flask.send_from_directory("outputs", name)
    else:
        return "Not Found", 404


@app.route('/apps/', methods=['POST'])
def apps():
    url = flask.request.data
    manifest = preload.fetch_application(url, "external-apps")
    return flask.jsonify({'name': manifest['shortname']})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

