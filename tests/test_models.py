import pytest
from app import create_app, db
from app.models import User, Product, Cart, Order
from werkzeug.security import check_password_hash


@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


def test_user_creation():
    """Тест создания пользователя"""
    user = User(username='testuser', email='test@test.com')
    user.set_password('password123')

    assert user.username == 'testuser'
    assert user.email == 'test@test.com'
    assert user.check_password('password123') == True
    assert user.check_password('wrong') == False
    # Исправлено: is_admin по умолчанию None, проверяем на None или False
    assert user.is_admin is None or user.is_admin == False


def test_user_creation_with_admin():
    """Тест создания администратора"""
    user = User(username='admin', email='admin@test.com', is_admin=True)
    user.set_password('admin123')

    assert user.username == 'admin'
    assert user.email == 'admin@test.com'
    assert user.is_admin == True
    assert user.check_password('admin123') == True


def test_product_creation():
    """Тест создания товара"""
    product = Product(
        name='Test Product',
        price=99.99,
        description='Test Description',
        stock=10
    )

    assert product.name == 'Test Product'
    assert product.price == 99.99
    assert product.description == 'Test Description'
    assert product.stock == 10


def test_user_password_hashing():
    """Тест хеширования пароля"""
    user = User()
    user.set_password('mypassword')

    assert user.password_hash != 'mypassword'
    assert check_password_hash(user.password_hash, 'mypassword') == True
    assert check_password_hash(user.password_hash, 'wrongpassword') == False