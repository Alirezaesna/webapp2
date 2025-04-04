# راهنمای استقرار سیستم قرض‌الحسنه

این راهنما برای استقرار پروژه سیستم قرض‌الحسنه بر روی یک سرور واقعی تهیه شده است.

## پیش‌نیازها

- پایتون 3.8 یا بالاتر
- PostgreSQL 12 یا بالاتر
- pip (مدیر بسته پایتون)
- virtualenv (برای ایجاد محیط مجازی)
- دسترسی به cPanel یا هاست پشتیبانی کننده از Flask

## فایل‌های مورد نیاز برای استقرار

- **requirements.txt**: لیست کتابخانه‌های مورد نیاز
- **wsgi.py**: فایل راه‌اندازی برنامه برای WSGI
- **Procfile**: تنظیمات اجرای برنامه (در صورت استفاده از PaaS مانند Heroku)
- **.env**: تنظیمات محیطی (از الگوی env.example استفاده کنید)

## محتوای requirements.txt
```
email-validator==2.1.0
Flask==2.3.3
Flask-Login==0.6.3
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.1
gunicorn==23.0.0
jdatetime==4.1.1
openpyxl==3.1.2
pandas==2.1.1
psycopg2-binary==2.9.9
SQLAlchemy==2.0.22
Werkzeug==2.3.7
WTForms==3.1.1
xlsxwriter==3.1.6
```

## محتوای .env (نمونه)
```
# Database Connection
DATABASE_URL=postgresql://user:password@localhost:5432/qardhasanah
PGHOST=localhost
PGPORT=5432
PGUSER=user
PGPASSWORD=password
PGDATABASE=qardhasanah

# Flask Application
FLASK_APP=main.py
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here
SESSION_SECRET=your-session-secret-here

# Admin User (Only for first initialization)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

## محتوای Procfile
```
web: gunicorn --bind 0.0.0.0:$PORT --workers 3 wsgi:app
```

## محتوای wsgi.py
```python
from main import app

if __name__ == "__main__":
    app.run()
```