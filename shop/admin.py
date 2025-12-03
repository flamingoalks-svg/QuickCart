from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Product, Cart, CartItem, Order, OrderItem


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Административная панель для управления пользователями."""
    list_display = ['email', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Права доступа', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2'),
        }),
    )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Административная панель для управления товарами.
    Позволяет добавлять, редактировать и удалять товары с загрузкой фотографий.
    """
    list_display = ['name', 'price', 'is_active', 'created_at', 'image_preview']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'image_preview']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'price', 'is_active')
        }),
        ('Изображение', {
            'fields': ('image', 'image_preview')
        }),
        ('Дополнительно', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        """Отображает миниатюру фотографии товара в списке и форме."""
        if obj.image:
            from django.utils.html import format_html
            return format_html('<img src="{}" style="max-width: 100px; max-height: 100px;" />', obj.image.url)
        return 'Нет изображения'
    image_preview.short_description = 'Превью'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Административная панель для просмотра корзин пользователей."""
    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Административная панель для просмотра позиций в корзинах."""
    list_display = ['cart', 'product', 'quantity', 'price']
    list_filter = ['cart']


class OrderItemInline(admin.TabularInline):
    """Встроенная форма для отображения позиций заказа."""
    model = OrderItem
    readonly_fields = ['product', 'quantity', 'price']
    extra = 0
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Административная панель для управления заказами."""
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['user', 'total_amount', 'created_at']
    inlines = [OrderItemInline]
    fields = ['user', 'status', 'total_amount', 'created_at']
    
    def has_add_permission(self, request):
        # Запрещаем создание заказов через админку
        return False


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Административная панель для просмотра позиций в заказах."""
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['order']
    readonly_fields = ['order', 'product', 'quantity', 'price']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
