from flask import Flask, render_template, request
from PIL import Image
import requests
import shutil
import os
import urllib.parse
from flask.json import jsonify
from configparser import ConfigParser

from os import listdir
from os.path import isfile, join


os.environ["DISPLAY"] = ":0"
TEMPLATES_AUTO_RELOAD = True


app = Flask(__name__, template_folder='templates')


@app.route('/', methods=['GET'])
def root():
    # return app.send_static_file("index.html")
    # return send_from_directory("static", "index.html")
    return render_template('index.html') # Return index.html

@app.route('/navigation.html', methods=['GET'])
def nav():
    return render_template('navigation.html') # Return index.html

# @app.route('/cached', methods=['GET'])
# def cached():
#     return render_template('cached.html') # Return index.html


# @app.route('/hello/<name>')
# def hello(name=None):
#     return render_template('hello.html', name=name)

# @app.route('/<name>')
# def hello_name(name):
#     return "Hello {}!".format(name)

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
    launchImage(url2)
    # img = Image.open("./static/images/" + url2)
    # transposed = img.transpose(Image.ROTATE_270)
    #
    # transposed.save("img_t." + fileExtension)
    # os.system('feh --hide-pointer --full-screen --zoom max "./img_t.{0}" &'.format(fileExtension))
    # # return "Loading poster {}".format(url)
    resp = jsonify(success=True)
    return resp

@app.route('/poster/img/<img>', methods=['GET'])
def get_poster(img):
    launchImage(img)
    resp = jsonify(success=True)
    return resp
    #return "Loading poster {}".format(url)

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
        # images.append(os.path.join("/static/images", filename))
        images.append(filename)
        # if filename.endswith(".jpg") and filename != "notapril.jpg":
        #     allninjas.append(os.path.join('static/images', filename))
        # else:
        #     continue
    # return jsonify(images)
    return render_template('cached.html', images=images)
    # onlyfiles = [f for f in listdir(imgpath) if isfile(join(imgpath, f))]
    # return os.listdir(imgpath)


@app.route('/runmode', methods=['PUT'])
def saveRunMode():
    config = ConfigParser()

    config.read('config.ini')
    config.add_section('runmode')
    config.set('runmode', 'manual', 'value1')
    config.set('runmode', 'random', 'value2')
    config.set('runmode', 'random_rotating', 'value3')
    config.set('runmode', 'plex', 'value3')

    with open('config.ini', 'w') as f:
        config.write(f)
    return jsonify(success=True)

@app.route('/runmode', methods=['GET'])
def getRunMode():
    config = ConfigParser()

    config.read('config.ini')

    print(config.get('runmode', 'manual')) # -> "value1")
    print(config.get('runmode', 'random'))  # -> "value2"
    print(config.get('runmode', 'random_rotating'))  # -> "value3"
    print(config.get('runmode', 'plex'))  # -> "value3"


def launchImage(filename):
    fileExtension = filename.rsplit('.', 1)[-1]
    url1 = urllib.parse.unquote(filename)
    imgt = Image.open("./static/images/" + filename)
    transposed = imgt.transpose(Image.ROTATE_270)

    transposed.save("img_t." + fileExtension)
    os.system('sudo killall feh; feh --hide-pointer --full-screen --zoom max "./img_t.{0}" &'.format(fileExtension))
    return

if __name__ == '__main__':
    app.run(host='0.0.0.0')