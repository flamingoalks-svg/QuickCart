# QuickCart - Онлайн-витрина

Учебное веб-приложение "QuickCart" — минимальный интернет-магазин без оплаты.

## Используемое ПО

- Python 3.13.3
- Django 5.2.8
- PostgreSQL
- Bootstrap 5.3

## Установка и запуск

1. Склонирйте репозиторий 
```powershell
git clone https://github.com/flamingoalks-svg/QuickCart_Kuznetsova
```

2. В каталоге QuickCart_Kuznetsova создайте виртуальное окружение и активируйте
```powershell
cd QuickCart_Kuznetsova
py -m venv venv
.\venv\Scripts\activate
```

3. Установите зависимости
```powershell
pip install -r .\requirements.txt
```
4. Убедитесь, что PostgreSQL запущен,  внесите настройки в quickcart/settings.py и populate_db.py
```powershell
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'quickcart',    # База данных
        'USER': 'postgres',    # Имя пользователя
        'PASSWORD': '11111111',    # Пароль
        'HOST': 'localhost',    # Адрес сервера БД
        'PORT': '5432',    # Порт
        'OPTIONS': {
            'client_encoding': 'UTF8',
        },
    }
}
```
5. Запустите скрипт для заполнения БД
```powershell
python populate_db.py
```

Этот скрипт автоматически:
- Создаст базу данных PostgreSQL 
- Применит все миграции Django
- Создаст администратора: admin@test.local / pass
- Добавит 20 товаров

6. Включите отправку почты и внесите учетные данные для почтового сервера в файл quickcart/settings.py, если требуется отправка уведомлений
```powershell
# Переменная для включения/отключения отправки email. 
ENABLE_EMAIL_SENDING = True
```

```powershell
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_PORT = 465
EMAIL_USE_SSL = True  # Для Mail.ru используется SSL
EMAIL_USE_TLS = False # TLS и SSL взаимоисключающие
EMAIL_HOST_USER = 'some_login@mail.ru'  # логин
EMAIL_HOST_PASSWORD = 'mail_password'  # пароль
```
7. Для запуска используйте:
```powershell
python manage.py runserver
```

8. Сайт доступен по адресу: http://127.0.0.1:8000/
9. Админка доступна по адресу: http://127.0.0.1:8000/admin/
- Email: admin@test.local
- Пароль: pass
