# 🛒 Интернет-магазин TeachMeSkills

Веб-приложение интернет-магазина с функционалом просмотра товаров, корзины, оформления заказов, системой рейтингов и админ-панелью.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green)
![SQLite](https://img.shields.io/badge/SQLite-3-blue)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple)

## 👤 Информация о проекте

**Разработчик:** [Dead79](https://github.com/Dead79) (EVGENIY)  
**Email:** 79greed@gmail.com  
**Репозиторий:** [internet-shop](https://github.com/Dead79/internet-shop)

## 📋 Содержание
- [О проекте](#о-проекте)
- [Технологии](#технологии)
- [Установка и запуск](#установка-и-запуск)
- [Тестирование](#тестирование)

## 🎯 О проекте

Этот проект является домашним заданием в рамках обучения в TeachMeSkills. Представляет собой полноценный интернет-магазин с разделением прав доступа (администратор/пользователь), системой заказов и возможностью оценивать товары.

**Статус:** Активная разработка

## 🛠 Технологии

### Backend:
- **Python 3.8+**
- **Flask 2.3.3** - веб-фреймворк
- **Flask-SQLAlchemy 3.0.5** - ORM для работы с БД
- **Flask-Login 0.6.2** - управление сессиями пользователей
- **Flask-WTF 1.1.1** - работа с формами и CSRF защита
- **WTForms 3.0.1** - валидация форм
- **SQLite** - база данных

### Frontend:
- **Bootstrap 5** - CSS фреймворк
- **Bootstrap Icons** - иконки
- **SweetAlert2** - красивые уведомления
- **HTML5/CSS3** - разметка и стили

### Тестирование:
- **pytest 7.4.0**
- **pytest-flask 1.2.0**

## 🚀 Установка и запуск

### Предварительные требования
- Python 3.8 или выше
- pip (менеджер пакетов Python)
- Git

### Пошаговая установка

1. **Клонируйте репозиторий**

git clone https://github.com/Dead79/internet-shop.git
cd internet-shop


# Windows
python -m venv venv
venv\Scripts\activate

# MacOS/Linux
python3 -m venv venv
source venv/bin/activate

Установите зависимости

pip install -r requirements.txt

Запустите приложение

python main.py
Откройте браузер и перейдите по адресу

text
http://127.0.0.1:5000
Данные для входа
Администратор:

Логин: admin

Пароль: admin123

Обычный пользователь:

Зарегистрируйтесь самостоятельно через форму регистрации

🧪 Тестирование
Запуск всех тестов
bash
pytest tests/ -v
Запуск конкретного теста
bash
pytest tests/test_models.py -v
pytest tests/test_routes.py -v
Тесты покрывают:
Создание моделей

Хеширование паролей

Регистрацию и вход

Доступ к страницам

Валидацию форм

Обработку ошибок

❗ Возможные ошибки и их решение
1. Ошибка: "ImportError: No module named 'flask'"
Решение: Установите зависимости

bash
pip install -r requirements.txt
2. Ошибка: "sqlite3.OperationalError: no such table"
Решение: Удалите файл shop.db и перезапустите приложение

bash
rm shop.db  # или del shop.db в Windows
python main.py
3. Ошибка: "CSRF token missing"
Решение: Обновите страницу и отправьте форму заново

4. Не работает вход под admin
Решение: Приложение создает админа автоматически при первом запуске.
Если не работает, удалите shop.db и перезапустите.

5. Порт 5000 уже используется
Решение: Измените порт в main.py

python
app.run(debug=True, port=5001)


📄 Лицензия
Проект является учебным и предназначен для демонстрации навыков веб-разработки в рамках курса TeachMeSkills.

Автор: Dead79