"""
Скрипт для создания базы данных, пользователей и наполнения базы товарами.
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Создаём базу данных, если её ещё нет
print('Проверка и создание базы данных...')
try:
    # Подключаемся к системной базе данных postgres
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='11111',
        database='postgres'
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    conn.set_client_encoding('UTF8')
    cur = conn.cursor()
    
    # Проверяем, существует ли база данных
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'quickcart'")
    exists = cur.fetchone()
    
    if not exists:
        # Создаём базу данных
        cur.execute('CREATE DATABASE quickcart')
        print('База данных quickcart создана')
    else:
        print('База данных quickcart уже существует')
    
    cur.close()
    conn.close()
except Exception as e:
    print(f'Ошибка при создании базы данных: {e}')
    print('Убедитесь, что PostgreSQL запущен и доступен')
    exit(1)

# Теперь инициализируем Django
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quickcart.settings')
django.setup()

from django.core.management import call_command
from django.core.files import File
from shop.models import User, Product
import shutil
from pathlib import Path

# Применяем миграции
print('\nПрименение миграций...')
try:
    call_command('migrate', verbosity=0)
    print('Миграции применены')
except Exception as e:
    print(f'Ошибка при применении миграций: {e}')
    exit(1)

# Создаём администратора
if not User.objects.filter(email='admin@test.local').exists():
    User.objects.create_superuser('admin@test.local', 'pass')
    print('Администратор создан: admin@test.local / pass')
else:
    print('Администратор уже существует')

# Создаём обычного пользователя
#if not User.objects.filter(email='user@test.local').exists():
#    User.objects.create_user('user@test.local', 'pass')
#    print('Пользователь создан: user@test.local / pass')
#else:
#    print('Пользователь уже существует')

# Данные товаров с сайта mvideo (6 ноутбуков, 14 смартфонов)
products_data = [
    # Ноутбуки (6 штук)
    {
        'name': 'Ноутбук ASUS VivoBook 15 X1504VA-NJ144W',
        'description': 'Ноутбук ASUS VivoBook 15 X1504VA-NJ144W с процессором Intel Core i5-1335U, 16 ГБ ОЗУ, SSD 512 ГБ, экран 15.6" Full HD, Windows 11 Home. Идеален для работы и учёбы.',
        'price': 59999.00,
    },
    {
        'name': 'Ноутбук Lenovo IdeaPad 3 15IAU7',
        'description': 'Ноутбук Lenovo IdeaPad 3 15IAU7 с процессором Intel Core i3-1215U, 8 ГБ ОЗУ, SSD 256 ГБ, экран 15.6" HD, Windows 11 Home. Отличный выбор для повседневных задач.',
        'price': 34999.00,
    },
    {
        'name': 'Ноутбук HP 15s-eq2000ur',
        'description': 'Ноутбук HP 15s-eq2000ur с процессором AMD Ryzen 5 5500U, 8 ГБ ОЗУ, SSD 512 ГБ, экран 15.6" Full HD, Windows 11 Home. Надёжный помощник для работы.',
        'price': 44999.00,
    },
    {
        'name': 'Ноутбук Acer Aspire 3 A315-59',
        'description': 'Ноутбук Acer Aspire 3 A315-59 с процессором Intel Core i5-1235U, 8 ГБ ОЗУ, SSD 512 ГБ, экран 15.6" Full HD, Windows 11 Home. Сбалансированное решение.',
        'price': 49999.00,
    },
    {
        'name': 'Ноутбук Dell Inspiron 15 3520',
        'description': 'Ноутбук Dell Inspiron 15 3520 с процессором Intel Core i5-1235U, 8 ГБ ОЗУ, SSD 256 ГБ, экран 15.6" Full HD, Windows 11 Home. Качество и надёжность Dell.',
        'price': 54999.00,
    },
    {
        'name': 'Ноутбук MSI Modern 15 B13M',
        'description': 'Ноутбук MSI Modern 15 B13M с процессором Intel Core i7-1355U, 16 ГБ ОЗУ, SSD 512 ГБ, экран 15.6" Full HD, Windows 11 Home. Мощный и стильный.',
        'price': 79999.00,
    },
    
    # Смартфоны (14 штук)
    {
        'name': 'Смартфон Samsung Galaxy A54 5G',
        'description': 'Смартфон Samsung Galaxy A54 5G с экраном 6.4" Super AMOLED, процессором Exynos 1380, 8 ГБ ОЗУ, 128 ГБ памяти, камера 50 Мп, 5G. Отличный выбор для повседневного использования.',
        'price': 29999.00,
    },
    {
        'name': 'Смартфон Apple iPhone 15',
        'description': 'Смартфон Apple iPhone 15 с экраном 6.1" Super Retina XDR, процессором A17 Pro, 128 ГБ памяти, камера 48 Мп. Флагман Apple с передовыми технологиями.',
        'price': 79999.00,
    },
    {
        'name': 'Смартфон Xiaomi Redmi Note 12 Pro',
        'description': 'Смартфон Xiaomi Redmi Note 12 Pro с экраном 6.67" AMOLED, процессором MediaTek Dimensity 1080, 8 ГБ ОЗУ, 256 ГБ памяти, камера 200 Мп. Отличное соотношение цена-качество.',
        'price': 24999.00,
    },
    {
        'name': 'Смартфон Realme 11 Pro',
        'description': 'Смартфон Realme 11 Pro с экраном 6.7" AMOLED, процессором MediaTek Dimensity 7050, 12 ГБ ОЗУ, 512 ГБ памяти, камера 200 Мп. Мощный и стильный.',
        'price': 34999.00,
    },
    {
        'name': 'Смартфон OnePlus Nord CE 3 Lite',
        'description': 'Смартфон OnePlus Nord CE 3 Lite с экраном 6.72" IPS, процессором Snapdragon 695, 8 ГБ ОЗУ, 256 ГБ памяти, камера 108 Мп. Быстрый и надёжный.',
        'price': 19999.00,
    },
    {
        'name': 'Смартфон Google Pixel 7a',
        'description': 'Смартфон Google Pixel 7a с экраном 6.1" OLED, процессором Google Tensor G2, 8 ГБ ОЗУ, 128 ГБ памяти, камера 64 Мп. Чистый Android и отличная камера.',
        'price': 44999.00,
    },
    {
        'name': 'Смартфон Honor 90',
        'description': 'Смартфон Honor 90 с экраном 6.7" AMOLED, процессором Snapdragon 7 Gen 1, 12 ГБ ОЗУ, 512 ГБ памяти, камера 200 Мп. Стильный дизайн и мощные характеристики.',
        'price': 39999.00,
    },
    {
        'name': 'Смартфон Vivo Y100',
        'description': 'Смартфон Vivo Y100 с экраном 6.38" AMOLED, процессором Snapdragon 695, 8 ГБ ОЗУ, 128 ГБ памяти, камера 64 Мп. Компактный и функциональный.',
        'price': 17999.00,
    },
    {
        'name': 'Смартфон OPPO Reno10',
        'description': 'Смартфон OPPO Reno10 с экраном 6.7" AMOLED, процессором MediaTek Dimensity 7050, 8 ГБ ОЗУ, 256 ГБ памяти, камера 64 Мп. Отличная камера и дизайн.',
        'price': 32999.00,
    },
    {
        'name': 'Смартфон Motorola Edge 40',
        'description': 'Смартфон Motorola Edge 40 с экраном 6.55" pOLED, процессором MediaTek Dimensity 8020, 8 ГБ ОЗУ, 256 ГБ памяти, камера 50 Мп. Быстрый и стильный.',
        'price': 37999.00,
    },
    {
        'name': 'Смартфон Nothing Phone (2)',
        'description': 'Смартфон Nothing Phone (2) с экраном 6.7" LTPO OLED, процессором Snapdragon 8+ Gen 1, 12 ГБ ОЗУ, 512 ГБ памяти, камера 50 Мп. Уникальный дизайн.',
        'price': 59999.00,
    },
    {
        'name': 'Смартфон Tecno Camon 20 Pro',
        'description': 'Смартфон Tecno Camon 20 Pro с экраном 6.67" AMOLED, процессором MediaTek Helio G99, 8 ГБ ОЗУ, 256 ГБ памяти, камера 108 Мп. Отличная камера за разумную цену.',
        'price': 15999.00,
    },
    {
        'name': 'Смартфон Infinix Note 30 Pro',
        'description': 'Смартфон Infinix Note 30 Pro с экраном 6.78" AMOLED, процессором MediaTek Helio G99, 8 ГБ ОЗУ, 256 ГБ памяти, камера 108 Мп. Большой экран и мощная батарея.',
        'price': 16999.00,
    },
    {
        'name': 'Смартфон POCO X5 Pro',
        'description': 'Смартфон POCO X5 Pro с экраном 6.67" AMOLED, процессором Snapdragon 778G, 8 ГБ ОЗУ, 256 ГБ памяти, камера 108 Мп. Игровой смартфон по доступной цене.',
        'price': 22999.00,
    },
]

# Создаём папку для изображений, если её нет
from django.conf import settings
media_products_dir = settings.MEDIA_ROOT / 'products'
media_products_dir.mkdir(parents=True, exist_ok=True)

# Путь к папке с исходными изображениями
imgs_dir = Path(__file__).parent / 'imgs'

# Добавляем товары в базу
print('\nДобавление товаров в базу...')
created_count = 0
updated_count = 0
for product_data in products_data:
    # Генерируем имя файла изображения на основе названия товара
    # Заменяем пробелы и специальные символы на подчёркивания, убираем скобки
    safe_name = product_data['name'].replace(' ', '_').replace('(', '').replace(')', '').replace('+', '_')
    image_filename = f"{safe_name}.jpg"
    image_path = imgs_dir / image_filename
    
    # Проверяем, существует ли уже такой товар
    product = Product.objects.filter(name=product_data['name']).first()
    
    if product:
        # Если товар существует, обновляем изображение из папки imgs
        if image_path.exists():
            # Копируем изображение из папки imgs
            try:
                with open(image_path, 'rb') as f:
                    product.image.save(image_filename, File(f), save=True)
                updated_count += 1
                print(f'Изображение обновлено для товара "{product.name}"')
            except Exception as e:
                print(f'Ошибка при копировании изображения для {product_data["name"]}: {e}')
        else:
            print(f'Предупреждение: изображение не найдено для товара "{product_data["name"]}": {image_path}')
        continue
    
    # Создаём новый товар
    product = Product.objects.create(
        name=product_data['name'],
        description=product_data['description'],
        price=product_data['price'],
        is_active=True
    )
    
    # Привязываем изображение, если оно существует
    if image_path.exists():
        try:
            with open(image_path, 'rb') as f:
                product.image.save(image_filename, File(f), save=True)
        except Exception as e:
            print(f'Ошибка при сохранении изображения для {product_data["name"]}: {e}')
    else:
        print(f'Предупреждение: изображение не найдено для товара "{product_data["name"]}": {image_path}')
    
    created_count += 1
    print(f'Товар "{product.name}" создан (цена: {product.price} ₽)')

print(f'\nСоздано новых товаров: {created_count}')
print(f'Обновлено изображений: {updated_count}')
print(f'Всего товаров в базе: {Product.objects.count()}')
print(f'Изображения товаров сохранены в: {media_products_dir}')

