from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.text import slugify
from decimal import Decimal


class UserManager(BaseUserManager):
    """Менеджер для работы с пользователями по email."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен для создания пользователя')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Кастомная модель пользователя с логином по email.
    """
    email = models.EmailField(unique=True, verbose_name='Email')
    username = models.CharField(max_length=150, blank=True, null=True, verbose_name='Имя пользователя')
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Product(models.Model):
    """
    Модель товара в каталоге магазина.
    Хранит информацию о товаре: название, описание, цену и фотографию.
    """
    name = models.CharField(
        max_length=200,
        verbose_name='Название',
        help_text='Название товара'
    )
    description = models.TextField(
        verbose_name='Описание',
        help_text='Полное описание товара'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена',
        help_text='Цена товара в рублях'
    )
    image = models.ImageField(
        upload_to='products/',
        verbose_name='Фотография',
        help_text='Фотография товара'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        verbose_name='URL-адрес',
        help_text='Уникальный идентификатор для URL'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен',
        help_text='Доступен ли товар для покупки'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Автоматически создаём slug из названия, если он не указан
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Cart(models.Model):
    """
    Модель корзины покупок.
    Каждый пользователь имеет одну активную корзину.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return f'Корзина пользователя {self.user.email}'

    def get_total(self):
        """Рассчитывает общую стоимость всех товаров в корзине."""
        return sum(item.get_subtotal() for item in self.items.all())


class CartItem(models.Model):
    """
    Модель позиции в корзине.
    Хранит информацию о товаре, его количестве и цене на момент добавления.
    """
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Корзина'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name='Количество'
    )
    # Фиксируем цену товара на момент добавления в корзину,
    # чтобы изменение цены в каталоге не влияло на корзину
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена на момент добавления'
    )

    class Meta:
        verbose_name = 'Позиция в корзине'
        verbose_name_plural = 'Позиции в корзине'
        unique_together = ['cart', 'product']

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    def get_subtotal(self):
        """Рассчитывает промежуточную сумму по позиции."""
        return self.price * self.quantity


class Order(models.Model):
    """
    Модель заказа.
    Хранит информацию о заказе пользователя и его итоговой сумме.
    Данные заказа фиксируются и не изменяются после оформления.
    """
    STATUS_CREATED = 'created'
    STATUS_IN_ASSEMBLY = 'in_assembly'
    STATUS_READY = 'ready'
    STATUS_DELIVERED = 'delivered'
    STATUS_CHOICES = [
        (STATUS_CREATED, 'Создан'),
        (STATUS_IN_ASSEMBLY, 'В сборке'),
        (STATUS_READY, 'Готов к выдаче'),
        (STATUS_DELIVERED, 'Выдан'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name='Пользователь'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CREATED,
        verbose_name='Статус'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Итоговая сумма'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-created_at']

    def __str__(self):
        return f'Заказ #{self.id} от {self.user.email}'


class OrderItem(models.Model):
    """
    Модель позиции в заказе.
    Хранит информацию о товаре, его количестве и цене на момент оформления заказа.
    Данные фиксируются и не изменяются после оформления.
    """
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='Заказ'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name='Товар'
    )
    quantity = models.PositiveIntegerField(
        verbose_name='Количество'
    )
    # Фиксируем цену товара на момент оформления заказа,
    # чтобы данные заказа не зависели от дальнейших изменений каталога
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Цена на момент оформления'
    )

    class Meta:
        verbose_name = 'Позиция в заказе'
        verbose_name_plural = 'Позиции в заказе'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    def get_subtotal(self):
        """Рассчитывает промежуточную сумму по позиции."""
        return self.price * self.quantity
