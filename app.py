# coding=utf-8
import json
import os
from string import digits, ascii_uppercase, ascii_lowercase

from flask import abort, Flask, request, jsonify, send_file

from ext import db, mako, render_template
from models import PasteFile

RANDOM_SEQ = ascii_uppercase + ascii_lowercase + digits

app = Flask(__name__)
app.config.from_object("config")
debug = app.config["DEBUG"]
if debug:
    from werkzeug import SharedDataMiddleware

    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/i/': os.path.join(
            os.path.dirname(__file__), app.config["UPLOAD_FOLDER"])
    })

mako.init_app(app)
db.init_app(app)

command_agent_keys = ['curl', 'wget']


def is_command_line_request(request):
    agent = str(request.user_agent).lower()
    if not agent:
        return True
    for k in command_agent_keys:
        if k in agent:
            return True
    return False


@app.route('/r/<img_hash>')
def rsize(img_hash):
    # TODO: rewrite
    print(request.args)
    w = request.args['w']
    h = request.args['h']

    oldPaste = PasteFile.get_by_filehash(img_hash)

    if not oldPaste:
        return abort(404)

    newPaste = PasteFile.rsize(oldPaste, w, h)

    return newPaste.url_i


@app.route('/a/<img_hash>')
def affine(img_hash):
    w = request.args['w']
    h = request.args['h']

    a = request.args['a']
    a = map(float, a.split(','))

    if len(a) != 6:
        return abort(400)

    oldPaste = PasteFile.get_by_filehash(img_hash)

    if not oldPaste:
        return abort(404)

    newPaste = PasteFile.affine(oldPaste, w, h, a)

    return newPaste.url_i


@app.route('/d/<filehash>', methods=["GET"])
def download(filehash):
    pasteFile = PasteFile.get_by_filehash(filehash)

    if not pasteFile:
        return abort(404)

    return send_file(open(pasteFile.path, "rb"),
                     mimetype="application/octet-stream",
                     cache_timeout=2592000,
                     as_attachment=True,
                     attachment_filename=pasteFile.filename)


@app.route('/', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        uploadedFile = request.files['file']
        w = request.form.get('w')
        h = request.form.get('h')
        # text file treat as binary file.
        # if user wanna post a text file, they would use pastebin / gist.
        if not uploadedFile:
            return abort(400)

        if w and h:
            pasteFile = PasteFile.create_file_after_crop(uploadedFile, w, h)
        else:
            pasteFile = PasteFile.create_by_uploadFile(uploadedFile)
        db.session.add(pasteFile)
        db.session.commit()

        if is_command_line_request(request):
            return pasteFile.url_i

        return jsonify(pasteFile.simple_dict())
    return render_template('index.html', **locals())


@app.after_request
def after_request(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route('/j', methods=['POST'])
def j():
    uploadedFile = request.files['file']

    if uploadedFile:
        pasteFile = PasteFile.create_by_uploadFile(uploadedFile)
        db.session.add(pasteFile)
        db.session.commit()
        width, height = pasteFile.image_size

        return jsonify({
            "url": pasteFile.url_i,
            "short_url": pasteFile.url_s,
            "origin_filename": pasteFile.filename,
            "hash": pasteFile.filehash,
            "width": width,
            "height": height
        })

    return abort(400)


@app.route('/p/<filehash>')
def preview(filehash):
    pasteFile = PasteFile.get_by_filehash(filehash)

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filehash)
    if not pasteFile:
        # check file exists
        if not (os.path.exists(filepath) and (not os.path.islink(filepath))):
            return abort(404)

        # linkfile = os.path.join(
        #     app.config['UPLOAD_FOLDER'], filehash.replace('.', '_'))
        # symlink = None
        # if os.path.exists(linkfile):
        #     with open(linkfile) as fp:
        #         symlink = fp.read().strip()

        pasteFile = PasteFile.create_by_old_paste(filehash)
        db.session.add(pasteFile)
        db.session.commit()

    file_json = json.dumps(pasteFile.simple_dict())
    return render_template('success.html', title=pasteFile.filename, file_json=file_json)


@app.route('/s/<symlink>')
def s(symlink):
    pasteFile = PasteFile.get_by_symlink(symlink)

    if not pasteFile:
        return abort(404)

    file_json = json.dumps(pasteFile.simple_dict())
    return render_template('success.html', title=pasteFile.filename, file_json=file_json)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=debug)
