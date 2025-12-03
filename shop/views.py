from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.conf import settings
from django.core.paginator import Paginator
from django.db import transaction
from django.core.mail import send_mail
from .models import User, Product, Cart, CartItem, Order, OrderItem


def register(request):
    """
    Регистрация нового пользователя.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, 'Пароли не совпадают.')
            return render(request, 'shop/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Пользователь с таким email уже существует.')
            return render(request, 'shop/register.html')
        
        user = User.objects.create_user(email=email, password=password)
        login(request, user)
        messages.success(request, 'Регистрация успешна! Добро пожаловать!')
        return redirect('shop:product_list')
    
    return render(request, 'shop/register.html')


def login_view(request):
    """
    Вход пользователя в систему.
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему.')
            return redirect('shop:product_list')
        else:
            messages.error(request, 'Неверный email или пароль.')
    
    return render(request, 'shop/login.html')


def logout_view(request):
    """
    Выход пользователя из системы.
    """
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('shop:product_list')


def product_list(request):
    """
    Отображает список активных товаров с пагинацией.
    """
    products = Product.objects.filter(is_active=True)
    
    # Пагинация: по 12 товаров на страницу
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'shop/product_list.html', {
        'page_obj': page_obj,
    })


def product_detail(request, slug):
    """
    Отображает страницу товара с подробной информацией.
    """
    product = get_object_or_404(Product, slug=slug, is_active=True)
    return render(request, 'shop/product_detail.html', {
        'product': product,
    })


@login_required
def add_to_cart(request, product_id):
    """
    Добавляет товар в корзину текущего пользователя.
    Если товар уже есть в корзине, увеличивает количество.
    """
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Получаем или создаём корзину для пользователя
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Проверяем, есть ли уже этот товар в корзине
    cart_item, item_created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'price': product.price}
    )
    
    if not item_created:
        # Если товар уже есть, увеличиваем количество
        cart_item.quantity += 1
        cart_item.save()
        messages.success(request, f'Количество товара "{product.name}" увеличено в корзине.')
    else:
        # Если товар добавлен впервые, фиксируем цену
        cart_item.price = product.price
        cart_item.save()
        messages.success(request, f'Товар "{product.name}" добавлен в корзину.')
    
    return redirect('shop:product_detail', slug=product.slug)


@login_required
def cart_view(request):
    """
    Отображает содержимое корзины текущего пользователя.
    """
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    total = cart.get_total()
    
    return render(request, 'shop/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
    })


@login_required
def update_cart_item(request, item_id):
    """
    Изменяет количество товара в корзине.
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Количество товара обновлено.')
        else:
            cart_item.delete()
            messages.success(request, 'Товар удалён из корзины.')
    
    return redirect('shop:cart')


@login_required
def remove_from_cart(request, item_id):
    """
    Удаляет товар из корзины.
    """
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'Товар "{product_name}" удалён из корзины.')
    return redirect('shop:cart')


@login_required
def checkout(request):
    """
    Отображает страницу оформления заказа и обрабатывает подтверждение.
    """
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    if not cart_items.exists():
        messages.warning(request, 'Ваша корзина пуста.')
        return redirect('shop:cart')
    
    total = cart.get_total()
    
    if request.method == 'POST':
        # Оформляем заказ
        with transaction.atomic():
            # Создаём заказ
            order = Order.objects.create(
                user=request.user,
                total_amount=total
            )
            
            # Создаём позиции заказа на основе корзины
            # Фиксируем данные заказа, чтобы они не изменялись
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.price
                )
            
            # Очищаем корзину после оформления заказа
            cart.items.all().delete()
        
        # --- ОТПРАВКА EMAIL-УВЕДОМЛЕНИЯ ---
        if settings.ENABLE_EMAIL_SENDING:
            recipient_email = request.user.email
            if "@" in recipient_email:
                domain = recipient_email.split('@')[1]
                if domain == "test.local":
                    print(f"DEBUG: Пропуск отправки email на тестовый домен: {recipient_email}")
                    messages.info(request, "Заказ успешно оформлен! Отправка подтверждения на тестовый домен 'test.local' пропущена.")
                else:
                    try:
                        subject = f'Заказ #{order.id} в магазине QuickCart успешно оформлен!'
                        message = (
                            f'Здравствуйте, {request.user.email}!\n\n'
                            f'Ваш заказ #{order.id} на сумму {order.total_amount} ₽ был успешно создан.\n'
                            f'Вы можете отследить его статус в личном кабинете на нашем сайте.\n\n'
                            'Спасибо за покупку!'
                        )
                        # from_email не указываем, будет использован DEFAULT_FROM_EMAIL из settings.py
                        recipient_list = [request.user.email]

                        send_mail(subject, message, from_email=None, recipient_list=recipient_list)
                        messages.success(request, f'Заказ #{order.id} успешно оформлен! Подтверждение отправлено на вашу почту.')
                    except Exception as e:
                        # Если отправка письма не удалась, заказ все равно оформлен.
                        # Просто сообщаем пользователю об успехе оформления, но без упоминания письма.
                        # В реальном проекте здесь стоит логировать ошибку 'e'.
                        print(f"ERROR: Ошибка при отправке email для заказа #{order.id} на {recipient_email}: {e}")
                        messages.success(request, f'Заказ #{order.id} успешно оформлен!')
            else:
                print(f"ERROR: Некорректный формат email для получателя: {recipient_email}")
                messages.error(request, "Заказ оформлен, но возникла ошибка с форматом email для отправки подтверждения.")
        else:
            # Отправка email отключена в настройках
            messages.success(request, f'Заказ #{order.id} успешно оформлен!')

        return redirect('shop:order_detail', order_id=order.id)
    
    return render(request, 'shop/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'total': total,
    })


@login_required
def order_list(request):
    """
    Отображает список заказов текущего пользователя.
    """
    orders = Order.objects.filter(user=request.user)
    return render(request, 'shop/order_list.html', {
        'orders': orders,
    })


@login_required
def order_detail(request, order_id):
    """
    Отображает детальную информацию о заказе.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    return render(request, 'shop/order_detail.html', {
        'order': order,
        'order_items': order_items,
    })
