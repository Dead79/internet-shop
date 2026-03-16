from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, IntegerField, TextAreaField, BooleanField, SelectField, \
    HiddenField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange, Optional, ValidationError
from app.models import User


class LoginForm(FlaskForm):
    """Форма входа в систему"""
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])


class RegistrationForm(FlaskForm):
    """Форма регистрации нового пользователя"""
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Это имя пользователя уже занято')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')


class ProductForm(FlaskForm):
    """Форма для добавления и редактирования товаров"""
    name = StringField('Название товара', validators=[
        DataRequired(message='Название товара обязательно'),
        Length(max=100, message='Название не может быть длиннее 100 символов')
    ])

    price = FloatField('Цена', validators=[
        DataRequired(message='Цена обязательна'),
        NumberRange(min=0.01, message='Цена должна быть больше 0')
    ])

    description = TextAreaField('Описание', validators=[
        DataRequired(message='Описание обязательно')
    ])

    stock = IntegerField('Количество на складе', validators=[
        DataRequired(message='Количество обязательно'),
        NumberRange(min=0, message='Количество не может быть отрицательным')
    ])

    image_url = StringField('URL изображения', validators=[
        Optional(),
        Length(max=200, message='URL не может быть длиннее 200 символов')
    ])


class AddToCartForm(FlaskForm):
    """Форма для добавления товара в корзину"""
    quantity = IntegerField('Количество', validators=[
        DataRequired(message='Укажите количество'),
        NumberRange(min=1, max=99, message='Количество должно быть от 1 до 99')
    ], default=1)


class RatingForm(FlaskForm):
    """Форма для оценки товара"""
    score = SelectField('Оценка',
                        choices=[
                            (5, '5 ★ Отлично'),
                            (4, '4 ★ Хорошо'),
                            (3, '3 ★ Нормально'),
                            (2, '2 ★ Плохо'),
                            (1, '1 ★ Ужасно')
                        ],
                        coerce=int,
                        validators=[DataRequired(message='Выберите оценку')])

    comment = TextAreaField('Комментарий (необязательно)', validators=[
        Optional(),
        Length(max=500, message='Комментарий не может быть длиннее 500 символов')
    ])


class TicketForm(FlaskForm):
    """Форма создания тикета"""
    title = StringField('Тема обращения', validators=[
        DataRequired(message='Укажите тему обращения'),
        Length(min=5, max=200, message='Тема должна быть от 5 до 200 символов')
    ])

    category = SelectField('Категория', choices=[
        ('order_issue', 'Проблема с заказом'),
        ('payment', 'Оплата'),
        ('delivery', 'Доставка'),
        ('product', 'Проблема с товаром'),
        ('refund', 'Возврат'),
        ('other', 'Другое')
    ], validators=[DataRequired(message='Выберите категорию')])

    priority = SelectField('Приоритет', choices=[
        ('low', 'Низкий'),
        ('medium', 'Средний'),
        ('high', 'Высокий'),
        ('urgent', 'Срочно!')
    ], default='medium', validators=[DataRequired()])

    order_id = SelectField('Связанный заказ (необязательно)', coerce=int, validators=[Optional()])

    message = TextAreaField('Сообщение', validators=[
        DataRequired(message='Напишите ваше сообщение'),
        Length(min=10, max=2000, message='Сообщение должно быть от 10 до 2000 символов')
    ])


class MessageForm(FlaskForm):
    """Форма отправки сообщения в тикете"""
    message = TextAreaField('Сообщение', validators=[
        DataRequired(message='Напишите ваше сообщение'),
        Length(min=1, max=2000, message='Сообщение слишком длинное')
    ])

    ticket_id = HiddenField()


class CloseTicketForm(FlaskForm):
    """Форма закрытия тикета"""
    pass