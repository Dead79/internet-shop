from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    cart_items = db.relationship('Cart', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    ratings = db.relationship('Rating', backref='user', lazy=True)
    tickets = db.relationship('Ticket', backref='user', lazy=True)
    messages = db.relationship('Message', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    ratings = db.relationship('Rating', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'

    def average_rating(self):
        """Вычисляет средний рейтинг товара"""
        if not self.ratings:
            return 0
        return sum(r.score for r in self.ratings) / len(self.ratings)

    def rating_count(self):
        """Возвращает количество оценок"""
        return len(self.ratings)

    def is_low_stock(self):
        """Проверяет, мало ли товара на складе"""
        return self.stock < 5


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с продуктом
    product = db.relationship('Product')


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    items = db.relationship('OrderItem', backref='order', lazy=True)
    tickets = db.relationship('Ticket', backref='order', lazy=True)


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)

    # Связь с продуктом
    product = db.relationship('Product')


class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)  # 1-5 звезд
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'product_id', name='unique_user_product_rating'),)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=True)  # Эта строка должна быть
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связи
    order = db.relationship('Order')
    ticket = db.relationship('Ticket', foreign_keys=[ticket_id])

    def __repr__(self):
        return f'<Notification {self.message[:20]}>'


# НОВЫЕ МОДЕЛИ ДЛЯ ДИАЛОГОВ
class Ticket(db.Model):
    """Тикет - обращение пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='open')  # open, in_progress, closed
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    category = db.Column(db.String(50), nullable=False)  # order_issue, payment, delivery, product, other
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime, nullable=True)

    # Связи
    messages = db.relationship('Message', backref='ticket', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Ticket #{self.id} - {self.title}>'

    def last_message(self):
        """Последнее сообщение в тикете"""
        if self.messages:
            return self.messages[-1]
        return None

    def message_count(self):
        """Количество сообщений"""
        return len(self.messages)

    def is_overdue(self):
        """Проверка, просрочен ли тикет (открыт более 3 дней)"""
        if self.status == 'closed':
            return False
        delta = datetime.utcnow() - self.created_at
        return delta.days > 3


class Message(db.Model):
    """Сообщение в тикете"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_admin_reply = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<Message #{self.id} in Ticket #{self.ticket_id}>'

    def mark_as_read(self):
        """Отметить сообщение как прочитанное"""
        self.read_at = datetime.utcnow()
        db.session.commit()