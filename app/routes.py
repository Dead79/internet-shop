from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.models import User, Product, Cart, Order, OrderItem, Rating, Notification, Ticket, Message
from app.forms import LoginForm, RegistrationForm, ProductForm, AddToCartForm, RatingForm, TicketForm, MessageForm, \
    CloseTicketForm
from functools import wraps
from sqlalchemy import func, inspect
from datetime import datetime, timedelta


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('У вас нет прав доступа к этой странице', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def init_app(app):
    # КОНТЕКСТНЫЙ ПРОЦЕССОР для передачи данных в шаблоны
    @app.context_processor
    def utility_processor():
        """Передает глобальные переменные во все шаблоны"""
        open_tickets_count = 0
        total_tickets_count = 0
        new_orders_count = 0

        if current_user.is_authenticated and current_user.is_admin:
            try:
                open_tickets_count = Ticket.query.filter(Ticket.status != 'closed').count()
                total_tickets_count = Ticket.query.count()
                new_orders_count = Order.query.filter_by(status='pending').count()
            except:
                # Таблицы могут еще не существовать
                pass

        return {
            'now': datetime.utcnow,
            'Ticket': Ticket,
            'open_tickets_count': open_tickets_count,
            'total_tickets_count': total_tickets_count,
            'new_orders_count': new_orders_count
        }

    @app.route('/')
    def index():
        products = Product.query.all()

        # Безопасная проверка уведомлений для админа
        if current_user.is_authenticated and current_user.is_admin:
            try:
                inspector = inspect(db.engine)
                if 'notification' in inspector.get_table_names():
                    unread_notifications = Notification.query.filter_by(is_read=False).count()
                    session['unread_notifications'] = unread_notifications
                else:
                    session['unread_notifications'] = 0
            except Exception as e:
                print(f"Ошибка при загрузке уведомлений: {e}")
                session['unread_notifications'] = 0

        return render_template('index.html', products=products)

    @app.route('/product/<int:id>', methods=['GET', 'POST'])
    def product_detail(id):
        product = Product.query.get_or_404(id)
        cart_form = AddToCartForm()
        rating_form = RatingForm()

        # Проверяем, оценивал ли пользователь этот товар
        user_rating = None
        if current_user.is_authenticated:
            user_rating = Rating.query.filter_by(
                user_id=current_user.id,
                product_id=product.id
            ).first()

        # Получаем все оценки товара
        ratings = Rating.query.filter_by(product_id=product.id).order_by(Rating.created_at.desc()).all()

        return render_template('product.html',
                               product=product,
                               cart_form=cart_form,
                               rating_form=rating_form,
                               user_rating=user_rating,
                               ratings=ratings)

    @app.route('/rate-product/<int:product_id>', methods=['POST'])
    @login_required
    def rate_product(product_id):
        product = Product.query.get_or_404(product_id)
        form = RatingForm()

        if form.validate_on_submit():
            existing_rating = Rating.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first()

            if existing_rating:
                existing_rating.score = form.score.data
                existing_rating.comment = form.comment.data
                flash('Ваша оценка обновлена!', 'success')
            else:
                rating = Rating(
                    user_id=current_user.id,
                    product_id=product_id,
                    score=form.score.data,
                    comment=form.comment.data
                )
                db.session.add(rating)
                flash('Спасибо за вашу оценку!', 'success')

            db.session.commit()

        return redirect(url_for('product_detail', id=product_id))

    @app.route('/my-orders')
    @login_required
    def my_orders():
        """Страница с заказами текущего пользователя"""
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template('my_orders.html', orders=orders)

    @app.route('/order/<int:order_id>')
    @login_required
    def order_detail(order_id):
        """Детальная информация о заказе пользователя"""
        order = Order.query.get_or_404(order_id)

        if order.user_id != current_user.id:
            flash('У вас нет доступа к этому заказу', 'danger')
            return redirect(url_for('my_orders'))

        return render_template('order_detail.html', order=order)

    @app.route('/cancel-order/<int:order_id>', methods=['POST'])
    @login_required
    def cancel_order(order_id):
        """Отмена заказа пользователем с возвратом товаров на склад"""
        order = Order.query.get_or_404(order_id)

        if order.user_id != current_user.id:
            flash('У вас нет доступа к этому заказу', 'danger')
            return redirect(url_for('my_orders'))

        if order.status in ['completed', 'cancelled']:
            flash('Этот заказ нельзя отменить', 'danger')
            return redirect(url_for('order_detail', order_id=order.id))

        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
                flash(f'Товар "{product.name}" ({item.quantity} шт.) возвращен на склад', 'info')

        order.status = 'cancelled'
        db.session.commit()

        flash(f'Заказ #{order.id} успешно отменен. Товары возвращены в магазин.', 'success')
        return redirect(url_for('my_orders'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = RegistrationForm()
        if form.validate_on_submit():
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash('Регистрация прошла успешно! Теперь вы можете войти', 'success')
            return redirect(url_for('login'))

        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()

            if user and user.check_password(form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                flash('Вы успешно вошли в систему!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Неверное имя пользователя или пароль', 'danger')

        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('index'))

    @app.route('/cart')
    @login_required
    def cart():
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        return render_template('cart.html', cart_items=cart_items, total=total)

    @app.route('/api/cart-count')
    @login_required
    def cart_count():
        """API для получения количества товаров в корзине"""
        count = Cart.query.filter_by(user_id=current_user.id).count()
        return {'count': count}

    @app.route('/api/notifications/count')
    @login_required
    @admin_required
    def notifications_count():
        """API для получения количества непрочитанных уведомлений"""
        try:
            count = Notification.query.filter_by(is_read=False).count()
            last_count = session.get('last_notification_count', 0)

            if count > last_count:
                new_count = count - last_count
                session['last_notification_count'] = count
                return {'count': count, 'new': new_count}
            else:
                session['last_notification_count'] = count
                return {'count': count, 'new': 0}
        except Exception as e:
            print(f"Ошибка при подсчете уведомлений: {e}")
            return {'count': 0, 'new': 0}

    @app.route('/api/notifications')
    @login_required
    @admin_required
    def get_notifications():
        """API для получения списка уведомлений"""
        try:
            notifications = Notification.query.filter_by(is_read=False).order_by(Notification.created_at.desc()).limit(
                10).all()
            return jsonify([{
                'id': n.id,
                'message': n.message,
                'type': n.type,
                'order_id': n.order_id,
                'ticket_id': n.ticket_id,
                'created_at': n.created_at.strftime('%H:%M %d.%m.%Y'),
                'is_read': n.is_read
            } for n in notifications])
        except Exception as e:
            print(f"Ошибка при получении уведомлений: {e}")
            return jsonify([])

    @app.route('/api/notifications/mark-read/<int:notification_id>', methods=['POST'])
    @login_required
    @admin_required
    def mark_notification_read(notification_id):
        """Отметить уведомление как прочитанное"""
        try:
            notification = Notification.query.get_or_404(notification_id)
            notification.is_read = True
            db.session.commit()
            return {'success': True}
        except Exception as e:
            print(f"Ошибка при отметке уведомления: {e}")
            return {'success': False}, 500

    @app.route('/api/notifications/mark-all-read', methods=['POST'])
    @login_required
    @admin_required
    def mark_all_notifications_read():
        """Отметить все уведомления как прочитанные"""
        try:
            Notification.query.update({Notification.is_read: True})
            db.session.commit()
            session['last_notification_count'] = 0
            return {'success': True}
        except Exception as e:
            print(f"Ошибка при отметке всех уведомлений: {e}")
            return {'success': False}, 500

    @app.route('/api/notifications/mark-ticket-read/<int:ticket_id>', methods=['POST'])
    @login_required
    @admin_required
    def mark_ticket_notifications_read(ticket_id):
        """Отметить все уведомления по конкретному тикету как прочитанные"""
        try:
            Notification.query.filter_by(
                ticket_id=ticket_id,
                type='ticket_message',
                is_read=False
            ).update({Notification.is_read: True})
            db.session.commit()
            return {'success': True}
        except Exception as e:
            print(f"Ошибка при отметке уведомлений тикета: {e}")
            return {'success': False}, 500

    @app.route('/quick-add-to-cart/<int:product_id>')
    @login_required
    def quick_add_to_cart(product_id):
        """Быстрое добавление товара в корзину"""
        product = Product.query.get_or_404(product_id)

        if product.stock < 1:
            flash(f'Товара "{product.name}" нет в наличии', 'danger')
            return redirect(url_for('index'))

        cart_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()

        if cart_item:
            if cart_item.quantity + 1 > product.stock:
                flash(f'Нельзя добавить больше {product.stock} шт. товара "{product.name}"', 'danger')
                return redirect(request.referrer or url_for('index'))
            cart_item.quantity += 1
        else:
            cart_item = Cart(
                user_id=current_user.id,
                product_id=product_id,
                quantity=1
            )
            db.session.add(cart_item)

        db.session.commit()
        flash(f'Товар "{product.name}" добавлен в корзину', 'success')

        return redirect(request.referrer or url_for('index'))

    @app.route('/add-to-cart/<int:product_id>', methods=['POST'])
    @login_required
    def add_to_cart(product_id):
        product = Product.query.get_or_404(product_id)
        form = AddToCartForm()

        if form.validate_on_submit():
            cart_item = Cart.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first()

            if cart_item:
                if cart_item.quantity + form.quantity.data > product.stock:
                    flash(f'Нельзя добавить больше {product.stock} шт. товара "{product.name}"', 'danger')
                    return redirect(url_for('product_detail', id=product_id))
                cart_item.quantity += form.quantity.data
            else:
                if form.quantity.data > product.stock:
                    flash(f'Нельзя добавить больше {product.stock} шт. товара "{product.name}"', 'danger')
                    return redirect(url_for('product_detail', id=product_id))
                cart_item = Cart(
                    user_id=current_user.id,
                    product_id=product_id,
                    quantity=form.quantity.data
                )
                db.session.add(cart_item)

            db.session.commit()
            flash(f'Товар "{product.name}" добавлен в корзину', 'success')

        return redirect(url_for('cart'))

    @app.route('/remove-from-cart/<int:item_id>')
    @login_required
    def remove_from_cart(item_id):
        cart_item = Cart.query.get_or_404(item_id)

        if cart_item.user_id != current_user.id:
            flash('Ошибка доступа', 'danger')
            return redirect(url_for('cart'))

        db.session.delete(cart_item)
        db.session.commit()
        flash('Товар удален из корзины', 'success')
        return redirect(url_for('cart'))

    @app.route('/checkout')
    @login_required
    def checkout():
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()

        if not cart_items:
            flash('Корзина пуста', 'warning')
            return redirect(url_for('cart'))

        total = sum(item.product.price * item.quantity for item in cart_items)

        return render_template('checkout.html', cart_items=cart_items, total=total)

    @app.route('/place-order', methods=['POST'])
    @login_required
    def place_order():
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()

        if not cart_items:
            return jsonify({'error': 'Корзина пуста'}), 400

        total = sum(item.product.price * item.quantity for item in cart_items)

        order = Order(
            user_id=current_user.id,
            total_amount=total
        )
        db.session.add(order)
        db.session.flush()

        for item in cart_items:
            if item.product.stock < item.quantity:
                db.session.rollback()
                return jsonify({'error': f'Недостаточно товара "{item.product.name}" на складе'}), 400

            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product.id,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity
            )
            db.session.add(order_item)

            item.product.stock -= item.quantity

        for item in cart_items:
            db.session.delete(item)

        try:
            notification = Notification(
                message=f'Новый заказ #{order.id} от пользователя {current_user.username} на сумму {total} руб.',
                type='new_order',
                order_id=order.id,
                is_read=False
            )
            db.session.add(notification)
        except Exception as e:
            print(f"Не удалось создать уведомление: {e}")

        db.session.commit()

        flash('Заказ успешно оформлен!', 'success')
        return redirect(url_for('my_orders'))

    # Админские маршруты
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        products = Product.query.all()
        users = User.query.all()
        orders = Order.query.all()
        recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
        low_stock_products = Product.query.filter(Product.stock < 5, Product.stock > 0).all()
        zero_stock_products = Product.query.filter_by(stock=0).all()

        notifications = []
        try:
            inspector = inspect(db.engine)
            if 'notification' in inspector.get_table_names():
                notifications = Notification.query.filter_by(is_read=False).order_by(
                    Notification.created_at.desc()).all()
        except Exception as e:
            print(f"Ошибка при загрузке уведомлений: {e}")

        return render_template('admin/dashboard.html',
                               products=products,
                               users=users,
                               orders=orders,
                               recent_orders=recent_orders,
                               low_stock_products=low_stock_products,
                               zero_stock_products=zero_stock_products,
                               notifications=notifications)

    @app.route('/admin/product/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_add_product():
        form = ProductForm()
        if form.validate_on_submit():
            product = Product(
                name=form.name.data,
                price=form.price.data,
                description=form.description.data,
                stock=form.stock.data,
                image_url=form.image_url.data
            )
            db.session.add(product)
            db.session.commit()
            flash('Товар успешно добавлен', 'success')
            return redirect(url_for('admin_dashboard'))

        return render_template('admin/add_product.html', form=form)

    @app.route('/admin/product/edit/<int:id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_edit_product(id):
        product = Product.query.get_or_404(id)
        form = ProductForm(obj=product)

        if form.validate_on_submit():
            old_stock = product.stock

            product.name = form.name.data
            product.price = form.price.data
            product.description = form.description.data
            product.stock = form.stock.data
            product.image_url = form.image_url.data

            db.session.commit()

            if old_stock == 0 and form.stock.data > 0:
                flash(f'✅ Товар "{product.name}" снова в наличии! Количество: {form.stock.data} шт.', 'success')

                try:
                    notification = Notification(
                        message=f'Товар "{product.name}" появился в наличии. Количество: {form.stock.data} шт.',
                        type='product_restocked',
                        is_read=False
                    )
                    db.session.add(notification)
                    db.session.commit()
                except Exception as e:
                    print(f"Не удалось создать уведомление: {e}")

            elif old_stock > 0 and form.stock.data == 0:
                flash(f'⚠️ Товар "{product.name}" помечен как "нет в наличии".', 'warning')
            elif form.stock.data == 0:
                flash(f'ℹ️ Товар "{product.name}" остается недоступным для заказа (количество: 0).', 'info')

            flash('✅ Товар успешно обновлен', 'success')
            return redirect(url_for('admin_dashboard'))

        return render_template('admin/edit_product.html', form=form, product=product)

    @app.route('/admin/product/delete/<int:id>')
    @login_required
    @admin_required
    def admin_delete_product(id):
        product = Product.query.get_or_404(id)

        cart_items = Cart.query.filter_by(product_id=id).all()
        if cart_items:
            flash('Нельзя удалить товар, который находится в корзине пользователей', 'danger')
            return redirect(url_for('admin_dashboard'))

        order_items = OrderItem.query.filter_by(product_id=id).all()
        if order_items:
            flash('Нельзя удалить товар, который есть в заказах', 'danger')
            return redirect(url_for('admin_dashboard'))

        Rating.query.filter_by(product_id=id).delete()

        db.session.delete(product)
        db.session.commit()
        flash('Товар удален', 'success')
        return redirect(url_for('admin_dashboard'))

    @app.route('/admin/orders')
    @login_required
    @admin_required
    def admin_orders():
        """Страница со всеми заказами для администратора"""
        status = request.args.get('status')

        query = Order.query

        if status:
            query = query.filter_by(status=status)

        orders = query.order_by(Order.created_at.desc()).all()

        try:
            Notification.query.filter_by(type='new_order', is_read=False).update({Notification.is_read: True})
            db.session.commit()
        except Exception as e:
            print(f"Не удалось обновить уведомления: {e}")

        return render_template('admin/orders.html', orders=orders, current_status=status)

    @app.route('/admin/order/<int:order_id>')
    @login_required
    @admin_required
    def admin_order_detail(order_id):
        """Детальная информация о заказе"""
        order = Order.query.get_or_404(order_id)
        return render_template('admin/order_detail.html', order=order)

    @app.route('/admin/order/cancel/<int:order_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_cancel_order(order_id):
        """Отмена заказа администратором"""
        order = Order.query.get_or_404(order_id)

        if order.status == 'completed':
            flash('Нельзя отменить выполненный заказ', 'danger')
            return redirect(url_for('admin_order_detail', order_id=order.id))

        if order.status == 'cancelled':
            flash('Заказ уже отменен', 'warning')
            return redirect(url_for('admin_order_detail', order_id=order.id))

        for item in order.items:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity

        order.status = 'cancelled'
        db.session.commit()

        flash(f'Заказ #{order.id} отменен. Товары возвращены на склад.', 'success')
        return redirect(url_for('admin_orders'))

    @app.route('/admin/order/delete/<int:order_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_order(order_id):
        """Удаление заказа администратором"""
        order = Order.query.get_or_404(order_id)

        order_id_display = order.id

        if order.status != 'cancelled':
            for item in order.items:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity

        for item in order.items:
            db.session.delete(item)

        db.session.delete(order)
        db.session.commit()

        flash(f'Заказ #{order_id_display} успешно удален. Товары возвращены на склад.', 'success')
        return redirect(url_for('admin_orders'))

    @app.route('/admin/order/update-status/<int:order_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_update_order_status(order_id):
        """Обновление статуса заказа"""
        order = Order.query.get_or_404(order_id)
        new_status = request.form.get('status')
        old_status = order.status

        if new_status in ['pending', 'processing', 'completed', 'cancelled']:

            if new_status == 'cancelled' and old_status != 'cancelled':
                for item in order.items:
                    product = Product.query.get(item.product_id)
                    if product:
                        product.stock += item.quantity
                flash('Товары возвращены на склад', 'info')

            elif old_status == 'cancelled' and new_status != 'cancelled':
                insufficient_stock = []
                for item in order.items:
                    product = Product.query.get(item.product_id)
                    if product and product.stock < item.quantity:
                        insufficient_stock.append(f"{product.name} (нужно {item.quantity}, есть {product.stock})")

                if insufficient_stock:
                    flash(f'Недостаточно товаров на складе: {", ".join(insufficient_stock)}', 'danger')
                    return redirect(url_for('admin_order_detail', order_id=order.id))

                for item in order.items:
                    product = Product.query.get(item.product_id)
                    if product:
                        product.stock -= item.quantity
                flash('Товары списаны со склада', 'info')

            order.status = new_status
            db.session.commit()
            flash(f'Статус заказа #{order.id} изменен с "{old_status}" на "{new_status}"', 'success')
        else:
            flash('Неверный статус', 'danger')

        return redirect(url_for('admin_order_detail', order_id=order.id))

    @app.route('/admin/order/bulk-delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_bulk_delete_orders():
        """Массовое удаление заказов"""
        order_ids = request.form.getlist('order_ids')

        if not order_ids:
            flash('Не выбрано ни одного заказа', 'warning')
            return redirect(url_for('admin_orders'))

        deleted_count = 0
        for order_id in order_ids:
            order = Order.query.get(order_id)
            if order:
                if order.status != 'cancelled':
                    for item in order.items:
                        product = Product.query.get(item.product_id)
                        if product:
                            product.stock += item.quantity

                for item in order.items:
                    db.session.delete(item)
                db.session.delete(order)
                deleted_count += 1

        db.session.commit()
        flash(f'Удалено заказов: {deleted_count}. Товары возвращены на склад.', 'success')
        return redirect(url_for('admin_orders'))

    @app.route('/admin/ratings')
    @login_required
    @admin_required
    def admin_ratings():
        """Страница со всеми оценками для администратора"""
        score = request.args.get('score', type=int)

        query = Rating.query

        if score in [1, 2, 3, 4, 5]:
            query = query.filter_by(score=score)

        ratings = query.order_by(Rating.created_at.desc()).all()

        return render_template('admin/ratings.html', ratings=ratings)

    @app.route('/admin/rating/delete/<int:rating_id>', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_rating(rating_id):
        """Удаление оценки администратором"""
        rating = Rating.query.get_or_404(rating_id)

        db.session.delete(rating)
        db.session.commit()

        flash('Оценка удалена', 'success')
        return redirect(url_for('admin_ratings'))

    # МАРШРУТЫ ДЛЯ ТИКЕТОВ (ОБРАЩЕНИЙ)
    @app.route('/my-tickets')
    @login_required
    def my_tickets():
        """Страница со списком обращений пользователя"""
        tickets = Ticket.query.filter_by(user_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        return render_template('my_tickets.html', tickets=tickets)

    @app.route('/ticket/new', methods=['GET', 'POST'])
    @login_required
    def new_ticket():
        """Создание нового обращения"""
        form = TicketForm()

        user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        form.order_id.choices = [(0, '-- Не связано с заказом --')] + [
            (o.id, f'Заказ #{o.id} от {o.created_at.strftime("%d.%m.%Y")} - {o.total_amount} ₽') for o in user_orders]

        if form.validate_on_submit():
            ticket = Ticket(
                title=form.title.data,
                category=form.category.data,
                priority=form.priority.data,
                user_id=current_user.id,
                order_id=form.order_id.data if form.order_id.data != 0 else None
            )
            db.session.add(ticket)
            db.session.flush()

            message = Message(
                ticket_id=ticket.id,
                user_id=current_user.id,
                message=form.message.data,
                is_admin_reply=False
            )
            db.session.add(message)

            try:
                notification = Notification(
                    message=f'Новое обращение #{ticket.id} от пользователя {current_user.username}: {ticket.title}',
                    type='new_ticket',
                    ticket_id=ticket.id,
                    is_read=False
                )
                db.session.add(notification)
            except Exception as e:
                print(f"Не удалось создать уведомление: {e}")

            db.session.commit()

            flash('Обращение создано! Мы ответим вам в ближайшее время.', 'success')
            return redirect(url_for('view_ticket', ticket_id=ticket.id))

        return render_template('new_ticket.html', form=form)

    @app.route('/ticket/<int:ticket_id>', methods=['GET', 'POST'])
    @login_required
    def view_ticket(ticket_id):
        """Просмотр и ответ в тикете"""
        ticket = Ticket.query.get_or_404(ticket_id)

        if not current_user.is_admin and ticket.user_id != current_user.id:
            flash('У вас нет доступа к этому обращению', 'danger')
            return redirect(url_for('index'))

        form = MessageForm()
        close_form = CloseTicketForm()

        if form.validate_on_submit():
            message = Message(
                ticket_id=ticket.id,
                user_id=current_user.id,
                message=form.message.data,
                is_admin_reply=current_user.is_admin
            )
            db.session.add(message)

            if ticket.status == 'closed':
                ticket.status = 'open'
                flash('Тикет открыт заново', 'info')

            try:
                if current_user.is_admin:
                    notification = Notification(
                        message=f'Новый ответ от администратора в обращении #{ticket.id}',
                        type='ticket_message',
                        ticket_id=ticket.id,
                        is_read=False
                    )
                else:
                    notification = Notification(
                        message=f'Новый ответ от пользователя {current_user.username} в обращении #{ticket.id}',
                        type='ticket_message',
                        ticket_id=ticket.id,
                        is_read=False
                    )
                db.session.add(notification)
            except Exception as e:
                print(f"Не удалось создать уведомление: {e}")

            ticket.updated_at = datetime.utcnow()
            db.session.commit()

            flash('Сообщение отправлено', 'success')
            return redirect(url_for('view_ticket', ticket_id=ticket.id))

        for message in ticket.messages:
            if message.user_id != current_user.id and not message.read_at:
                message.read_at = datetime.utcnow()

        try:
            Notification.query.filter_by(
                ticket_id=ticket.id,
                type='ticket_message',
                is_read=False
            ).update({Notification.is_read: True})
            db.session.commit()
        except Exception as e:
            print(f"Не удалось отметить уведомления: {e}")

        return render_template('view_ticket.html', ticket=ticket, form=form, close_form=close_form)

    @app.route('/ticket/<int:ticket_id>/close', methods=['POST'])
    @login_required
    def close_ticket(ticket_id):
        """Закрытие тикета"""
        ticket = Ticket.query.get_or_404(ticket_id)

        if not current_user.is_admin and ticket.user_id != current_user.id:
            flash('У вас нет доступа к этому обращению', 'danger')
            return redirect(url_for('index'))

        ticket.status = 'closed'
        ticket.closed_at = datetime.utcnow()
        db.session.commit()

        flash('Обращение закрыто', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    @app.route('/ticket/<int:ticket_id>/reopen', methods=['POST'])
    @login_required
    def reopen_ticket(ticket_id):
        """Переоткрытие тикета"""
        ticket = Ticket.query.get_or_404(ticket_id)

        if not current_user.is_admin and ticket.user_id != current_user.id:
            flash('У вас нет доступа к этому обращению', 'danger')
            return redirect(url_for('index'))

        ticket.status = 'open'
        ticket.closed_at = None
        db.session.commit()

        flash('Обращение открыто заново', 'success')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    # ИСПРАВЛЕННАЯ ФУНКЦИЯ admin_tickets
    @app.route('/admin/tickets')
    @login_required
    @admin_required
    def admin_tickets():
        """Страница со всеми обращениями для администратора"""
        status = request.args.get('status')
        priority = request.args.get('priority')

        # Базовый запрос
        query = Ticket.query

        # Фильтруем по статусу, если указан
        if status:
            query = query.filter_by(status=status)

        # Фильтруем по приоритету, если указан
        if priority:
            query = query.filter_by(priority=priority)

        # Сортируем: сначала срочные, потом открытые, потом по дате
        tickets = query.order_by(
            # Сначала срочные
            Ticket.priority == 'urgent',
            # Потом высокие
            Ticket.priority == 'high',
            # Потом открытые (не закрытые)
            Ticket.status != 'closed',
            # Потом по дате (сначала новые)
            Ticket.created_at.desc()
        ).all()

        # Статистика для карточек
        total_tickets = Ticket.query.count()
        open_tickets = Ticket.query.filter(Ticket.status != 'closed').count()
        urgent_tickets = Ticket.query.filter_by(priority='urgent').filter(Ticket.status != 'closed').count()
        in_progress_tickets = Ticket.query.filter_by(status='in_progress').count()
        closed_tickets = Ticket.query.filter_by(status='closed').count()

        return render_template('admin/tickets.html',
                               tickets=tickets,
                               total_tickets=total_tickets,
                               open_tickets=open_tickets,
                               urgent_tickets=urgent_tickets,
                               in_progress_tickets=in_progress_tickets,
                               closed_tickets=closed_tickets,
                               current_status=status,
                               current_priority=priority)

    @app.route('/admin/ticket/<int:ticket_id>/update-priority', methods=['POST'])
    @login_required
    @admin_required
    def update_ticket_priority(ticket_id):
        """Обновление приоритета тикета"""
        ticket = Ticket.query.get_or_404(ticket_id)
        new_priority = request.form.get('priority')

        if new_priority in ['low', 'medium', 'high', 'urgent']:
            ticket.priority = new_priority
            db.session.commit()
            flash(f'Приоритет обновлен на {new_priority}', 'success')

        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    @app.route('/admin/ticket/<int:ticket_id>/update-status', methods=['POST'])
    @login_required
    @admin_required
    def update_ticket_status(ticket_id):
        """Обновление статуса тикета"""
        ticket = Ticket.query.get_or_404(ticket_id)
        new_status = request.form.get('status')

        if new_status in ['open', 'in_progress', 'closed']:
            ticket.status = new_status
            if new_status == 'closed':
                ticket.closed_at = datetime.utcnow()
            db.session.commit()
            flash(f'Статус обновлен на {new_status}', 'success')

        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500