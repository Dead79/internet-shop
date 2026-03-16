import pytest
from app import db
from app.models import User, Ticket, Message


def test_ticket_creation(app, test_user):
    """Тест создания тикета"""
    with app.app_context():
        ticket = Ticket(
            title='Test Ticket',
            category='other',
            priority='medium',
            user_id=test_user
        )
        db.session.add(ticket)
        db.session.commit()

        assert ticket.id is not None
        assert ticket.title == 'Test Ticket'
        assert ticket.status == 'open'
        assert ticket.user_id == test_user


def test_message_creation(app, test_user):
    """Тест создания сообщения"""
    with app.app_context():
        # Создаем тикет
        ticket = Ticket(
            title='Test Ticket',
            category='other',
            priority='medium',
            user_id=test_user
        )
        db.session.add(ticket)
        db.session.commit()

        # Создаем сообщение
        message = Message(
            ticket_id=ticket.id,
            user_id=test_user,
            message='Test message',
            is_admin_reply=False
        )
        db.session.add(message)
        db.session.commit()

        assert message.id is not None
        assert message.message == 'Test message'
        assert message.ticket_id == ticket.id