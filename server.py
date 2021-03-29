from flask import Flask, render_template, request
from PIL import Image
import requests
import shutil
import os
import urllib.parse
from flask.json import jsonify
from configparser import ConfigParser
import time
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import random
from flask_socketio import send, emit, disconnect, SocketIO
import sqlite3


os.environ["DISPLAY"] = ":0"
TEMPLATES_AUTO_RELOAD = True

# con = sqlite3.connect('settings.sqlite')
# cur = con.cursor()
# t = '''
# CREATE TABLE IF NOT EXISTS run_mode (
#     id INTEGER PRIMARY KEY,
#     mode TEXT NOT NULL,
#     active INTEGER DEFAULT 0
# );'''
# cur.execute(t)
## Needs to be mutable
run_mode_images = []
index = [0]
scheduler

app = Flask(__name__, template_folder='templates')
socketio = SocketIO(app)

@socketio.on('currentImage')
def handle_message(data):
    print('received message: ' + data)

@socketio.on('connect')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

@app.route('/', methods=['GET'])
def root():
    # return app.send_static_file("index.html")
    # return send_from_directory("static", "index.html")
    return render_template('index.html') # Return index.html


@app.route('/navigation.html', methods=['GET'])
def nav():
    return render_template('navigation.html') # Return index.html

@app.route('/poster/current', methods=["GET"])
def get_current_poster():
    return getImageConfig()

@app.route('/poster/url', methods=['POST'])
def set_poster():
    if not os.path.exists('./static/images'):
        os.makedirs('./static/images')

    url = urllib.parse.unquote(request.form['posterImageURL'])
    url2 = url.rsplit('/', 1)[-1]
    fileExtension = url.rsplit('.', 1)[-1]
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        with open("./static/images/" + url2, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
            print ("Saved file: ./static/images/" + url2)
    setImageConfig(url2)
    launchImage(url2)
    build_dynamic_run_mode()
    resp = jsonify(success=True)
    return resp

@app.route('/poster/url/random')
def set_poster_random():
    imgpath = "./static/images"
    images = []
    for filename in os.listdir(imgpath):
        images.append(filename)
    index = random.randint(0, len(images) - 1)
    setImageConfig(images[index])
    launchImage(images[index])
    return jsonify(success=True)


@app.route('/poster/img/<img>', methods=['GET'])
def get_poster(img):
    setImageConfig(img)
    launchImage(img)
    resp = jsonify(success=True)
    return resp

@app.route('/poster/img/<img>', methods=['DELETE'])
def delete_poster(img):
    # fileExtension = img.rsplit('.', 1)[-1]
    img2 = urllib.parse.unquote(img).strip()
    # imgt = Image.open("./static/images/" + img)
    # transposed = imgt.transpose(Image.ROTATE_270)

    # transposed.save("img_t." + fileExtension)
    print("./static/images/" + img2)
    os.remove("./static/images/" + img2)
    resp = jsonify(success=True)
    return resp
    # return get_posters_cached()


@app.route('/posters/cached')
def get_posters_cached():
    imgpath = "./static/images"
    images = []
    for filename in os.listdir(imgpath):
        images.append(filename)
    return render_template('cached.html', images=images)


@app.route('/runmode/<mode>/<value>', methods=['PUT'])
def saveRunMode(mode, value):
    config = ConfigParser()
    config.read('config.ini')
    config.set('runmode', mode, value)

    with open('config.ini', 'w') as f:
        config.write(f)
    # if (mode == "dynamic"):
        # build_dynamic_run_mode()
    return jsonify(success=True)

@app.route('/runmode', methods=['GET'])
def getRunMode():
    config = ConfigParser()
    config.read('config.ini')
    r = dict(config.items('runmode'))
    return jsonify(r)

@app.route('/runmode/static', methods=['GET'])
def getRunModeStatic():
    config = ConfigParser()
    config.read('config.ini')
    r = dict(config.items('static'))
    return jsonify(r)

@app.route('/runmode/dynamic', methods=['GET'])
def getRunModeDynamic():
    config = ConfigParser()
    config.read('config.ini')
    r = dict(config.items('dynamic'))
    return jsonify(r)

@app.route('/runmode/dynamic/<mode>/<vaue>', methods=['PUT'])
def setRunModeDynamic(mode, value):
    config = ConfigParser()
    config.read('config.ini')
    config.set('dynamic', mode, value)

    with open('config.ini', 'w') as f:
        config.write(f)
    build_dynamic_run_mode()
    return jsonify(success=True)

@app.route('/schedule/<interval>')
def setScheduleInterval():
    scheduler.shutdown()
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=run_mode, args=[index], trigger="interval", seconds=300)

def launchImage(filename):
    fileExtension = filename.rsplit('.', 1)[-1]
    url1 = urllib.parse.unquote(filename)
    imgt = Image.open("./static/images/" + filename)
    transposed = imgt.transpose(Image.ROTATE_270)

    transposed.save("img_t." + fileExtension)
    os.system('sudo killall feh; feh --hide-pointer --full-screen --zoom max "./img_t.{0}" &'.format(fileExtension))
    socketio.emit('currentImage', filename)
    setImageConfig(filename)
    return

def setImageConfig(filename):
    config = ConfigParser()
    config.read('config.ini')
    config.set('main', "current", filename)

    with open('config.ini', 'w') as f:
        config.write(f)

def getImageConfig():
    config = ConfigParser()
    config.read('config.ini')
    return config.get("main", "current")

#####
# Scheduled Tasks
#####
def print_date_time():
    print(time.strftime("%A, %d. %B %Y %I:%M:%S %p"))

def build_dynamic_run_mode():
    index = 0
    config = ConfigParser()
    config.read('config.ini')
    r = dict(config.items('dynamic'))
    if (r['random_rotating'] == "true"):
        imgpath = "./static/images"
        run_mode_images.clear()
        for filename in os.listdir(imgpath):
            run_mode_images.append(filename)
        print("Random Rotating Selected")



## Reads next in list of ones to display
## List gets built from the set run mode options
def run_mode(index):
    config = ConfigParser()
    config.read('config.ini')
    r = dict(config.items('runmode'))
    if (r['mode'] == "static"):
        print("STATIC ")
        return
    if (len(run_mode_images) < 1):
        print("NOT ENOUGH")
        return
    else:
        index[0] += 1
        if (index[0] >= len(run_mode_images)):
            index[0] = 0
        current_image = run_mode_images[index[0]]
        launchImage(current_image)

    # Order of importance
#INIT
launchImage(getImageConfig())
build_dynamic_run_mode()

scheduler = BackgroundScheduler()
scheduler.add_job(func=run_mode, args=[index], trigger="interval", seconds=300)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(host='0.0.0.0')