from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField


class DownloadForm(FlaskForm):
    password = PasswordField('Пароль')
    submit = SubmitField('Скачать')
