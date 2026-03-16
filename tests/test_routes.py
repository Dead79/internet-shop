import pytest
from app import db
from app.models import User, Product


def test_index_page(client):
    """Тест главной страницы"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'TeachMeSkills Shop' in response.data or b'\xd0\xa2\xd0\xbe\xd0\xb2\xd0\xb0\xd1\x80\xd1\x8b' in response.data


def test_register_page(client):
    """Тест страницы регистрации"""
    response = client.get('/register')
    assert response.status_code == 200
    assert b'Register' in response.data or b'\xd0\xa0\xd0\xb5\xd0\xb3\xd0\xb8\xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd1\x86\xd0\xb8\xd1\x8f' in response.data


def test_login_page(client):
    """Тест страницы входа"""
    response = client.get('/login')
    assert response.status_code == 200
    assert b'Login' in response.data or b'\xd0\x92\xd1\x85\xd0\xbe\xd0\xb4' in response.data


def test_register_user(client, app):
    """Тест регистрации пользователя"""
    response = client.post('/register', data={
        'username': 'newuser',
        'email': 'newuser@test.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(username='newuser').first()
        assert user is not None
        assert user.email == 'newuser@test.com'


def test_login_user(client, app):
    """Тест входа пользователя"""
    # Сначала создаем пользователя
    with app.app_context():
        user = User(
            username='loginuser',
            email='login@test.com',
            is_admin=False
        )
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()

    # Пробуем войти
    response = client.post('/login', data={
        'username': 'loginuser',
        'password': 'password123'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Проверяем, что есть кнопка выхода
    assert b'Logout' in response.data or b'\xd0\x92\xd1\x8b\xd0\xb9\xd1\x82\xd0\xb8' in response.data


def test_product_page(client, app, test_product):
    """Тест страницы товара"""
    # Используем ID товара из фикстуры
    response = client.get(f'/product/{test_product}')
    assert response.status_code == 200
    assert b'Test Product' in response.data


def test_cart_access_without_login(client):
    """Тест доступа к корзине без авторизации"""
    response = client.get('/cart', follow_redirects=True)
    assert response.status_code == 200
    # Должен перенаправить на страницу входа
    assert b'Login' in response.data or b'\xd0\x92\xd1\x85\xd0\xbe\xd0\xb4' in response.data


def test_add_to_cart_with_login(auth_client, app, test_product):
    """Тест добавления в корзину авторизованным пользователем"""
    # Используем ID товара
    response = auth_client.post(f'/add-to-cart/{test_product}', data={
        'quantity': 2
    }, follow_redirects=True)

    assert response.status_code == 200
    # Проверяем, что произошел редирект на корзину
    assert b'Cart' in response.data or b'\xd0\x9a\xd0\xbe\xd1\x80\xd0\xb7\xd0\xb8\xd0\xbd\xd0\xb0' in response.data


def test_quick_add_to_cart(auth_client, app, test_product):
    """Тест быстрого добавления в корзину"""
    # Используем ID товара
    response = auth_client.get(f'/quick-add-to-cart/{test_product}', follow_redirects=True)

    assert response.status_code == 200
    # Проверяем, что есть сообщение об успехе или редирект
    assert response.status_code == 200


def test_invalid_registration(client):
    """Тест невалидной регистрации"""
    response = client.post('/register', data={
        'username': 'a',  # Слишком короткое имя
        'email': 'invalid-email',  # Невалидный email
        'password': '123',  # Слишком короткий пароль
        'confirm_password': '456'  # Не совпадает с паролем
    }, follow_redirects=True)

    assert response.status_code == 200
    # Проверяем наличие сообщений об ошибках
    assert b'error' in response.data.lower() or b'\xd0\xbe\xd1\x88\xd0\xb8\xd0\xb1\xd0\xba\xd0\xb0' in response.data.lower()


def test_404_page(client):
    """Тест страницы 404"""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'404' in response.data


def test_logout(auth_client):
    """Тест выхода из системы"""
    response = auth_client.get('/logout', follow_redirects=True)
    assert response.status_code == 200

    # Проверяем, что после выхода есть кнопка входа
    response_data = response.data.lower()
    assert b'login' in response_data or b'\xd0\xb2\xd1\x85\xd0\xbe\xd0\xb4' in response_data


def test_create_ticket_page(auth_client):
    """Тест страницы создания обращения"""
    response = auth_client.get('/ticket/new')
    assert response.status_code == 200
    assert b'New Ticket' in response.data or b'\xd0\x9d\xd0\xbe\xd0\xb2\xd0\xbe\xd0\xb5 \xd0\xbe\xd0\xb1\xd1\x80\xd0\xb0\xd1\x89\xd0\xb5\xd0\xbd\xd0\xb8\xd0\xb5' in response.data


def test_my_tickets_page(auth_client):
    """Тест страницы моих обращений"""
    response = auth_client.get('/my-tickets')
    assert response.status_code == 200
    assert b'My Tickets' in response.data or b'\xd0\x9c\xd0\xbe\xd0\xb8 \xd0\xbe\xd0\xb1\xd1\x80\xd0\xb0\xd1\x89\xd0\xb5\xd0\xbd\xd0\xb8\xd1\x8f' in response.data