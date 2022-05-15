from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import PasswordField, SubmitField, IntegerField, validators


class UploadForm(FlaskForm):
    file_input = FileField('Загрузить файл', validators=[FileRequired()])
    password = PasswordField('Пароль')
    submit = SubmitField('Загрузить')
    days = IntegerField('Количество дней', default=1,
                        validators=[validators.NumberRange(min=1, max=10, message='Неверное число')])
