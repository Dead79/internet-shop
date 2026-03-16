import pytest
from app import create_app, db
from app.models import User, Product


@pytest.fixture(scope='function')
def app():
    """Создает тестовое приложение для каждой тестовой функции"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost.localdomain'

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Тестовый клиент"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Тестовый CLI раннер"""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Создает тестового пользователя"""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@test.com',
            is_admin=False
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        # Возвращаем ID вместо объекта, чтобы избежать проблем с сессией
        return user.id


@pytest.fixture
def test_admin(app):
    """Создает тестового админа"""
    with app.app_context():
        admin = User(
            username='admin',
            email='admin@test.com',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        return admin.id


@pytest.fixture
def test_product(app):
    """Создает тестовый товар и возвращает его ID"""
    with app.app_context():
        product = Product(
            name='Test Product',
            price=99.99,
            description='Test Description',
            stock=10
        )
        db.session.add(product)
        db.session.commit()
        # Возвращаем ID, чтобы использовать в тестах
        product_id = product.id
        return product_id


@pytest.fixture
def auth_client(app, client, test_user):
    """Фикстура для авторизованного клиента"""
    with app.app_context():
        # Входим в систему используя тестового пользователя
        client.post('/login', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(app, client, test_admin):
    """Фикстура для авторизованного админа"""
    with app.app_context():
        client.post('/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
    return client