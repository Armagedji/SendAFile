import atexit
import datetime
import os, glob
import shutil

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from werkzeug.security import generate_password_hash, check_password_hash

from data import db_session
from data.Files import Files
from data.downloadform import DownloadForm
from data.uploadform import UploadForm

UPLOAD_FOLDER = './drive/'
ALLOWED_EXTENSIONS = {'txt', 'zip', 'rar', 'img', 'jpg', 'jpeg', 'bmp', 'png'}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_good_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 64 * 1000 * 1000
db_session.global_init("db/files.db")


def temp_clear():
    for file in glob.glob('temp/*'):
        os.remove(file)


def delete_check():
    db_sess = db_session.create_session()
    look_for = datetime.datetime.now()
    for file in db_sess.query(Files).filter(Files.expiration_date < look_for):
        os.remove(file.path[2:])
        db_sess.delete(file)
    db_sess.commit()



scheduler = BackgroundScheduler()
scheduler.add_job(func=temp_clear, trigger='interval', seconds=60)
scheduler.add_job(func=delete_check, trigger='interval', seconds=5)
scheduler.start()


def allowed_file(file):
    return '.' in file and file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)


@app.route("/", methods=['GET', 'POST'])
def file_upload():
    form = UploadForm()
    if request.method == 'POST':
        file = form.file_input.data
        if file and allowed_file(file.filename):
            db_sess = db_session.create_session()
            if len(db_sess.query(Files).all()) == 0:
                x = '1'
            else:
                x = None
                for i in range(1, len(db_sess.query(Files).all()) + 2):
                    for k in db_sess.query(Files).filter(Files.id == i):
                        if k.id == i:
                            no = True
                            break
                    if no:
                        no = False
                        continue
                    else:
                        x = str(i)
                        break
            files = Files()
            filename = file.filename
            files.name = filename
            files.id = int(x)
            files.path = os.path.join(app.config['UPLOAD_FOLDER'], x + '.' + filename.rsplit('.', 1)[1].lower())
            if form.password.data == '':
                files.hashed_password = ''
            else:
                files.hashed_password = generate_password_hash(form.password.data)
            files.expiration_date = datetime.datetime.now() + datetime.timedelta(days=form.days.data)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], x + '.' + filename.rsplit('.', 1)[1].lower()))
            db_sess.add(files)
            db_sess.commit()
            return redirect(url_for('download_file', name=x + '.' + filename.rsplit('.', 1)[1].lower()))
    return render_template("index.html", form=form)


@app.route('/uploads/<name>', methods=['GET', 'POST'])
def download_file(name):
    form = DownloadForm()
    if request.method == "POST":
        db_sess = db_session.create_session()
        for file in db_sess.query(Files).filter(Files.id == int(name.split('.')[0])):
            if file:
                if file.hashed_password == '' or check_password(file.hashed_password, form.password.data):
                    shutil.copy2(file.path[2:], f'temp/{file.name}')
                    return send_from_directory('temp', file.name, as_attachment=True)
                    os.remove(f'temp/{file.name}')
    db_sess = db_session.create_session()
    for file in db_sess.query(Files).filter(Files.path == f'./drive/{name}'):
        if file:
            return render_template('download.html', name=file.name, form=form)
    return render_template('error.html')


app.run()
atexit.register(lambda: scheduler.shutdown())
