import json
import os
import logging
from datetime import datetime, date
from app import app, db
from models import User, Loan, Installment
from sqlalchemy.exc import IntegrityError
from pg_db_utils import restore_database

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تابع تبدیل داده‌های JSON به مدل‌های SQLAlchemy
def deserialize_model(model_class, data):
    """
    تبدیل داده‌های دریافتی از JSON به مدل SQLAlchemy
    
    Args:
        model_class: کلاس مدل SQLAlchemy
        data: دیکشنری داده‌ها از JSON
        
    Returns:
        instance: نمونه ایجاد شده از مدل
    """
    # کپی از داده‌ها برای جلوگیری از تغییر در دیکشنری اصلی
    data_copy = data.copy()
    
    # حذف کلید id برای جلوگیری از تداخل با کلیدهای خودکار
    if 'id' in data_copy:
        original_id = data_copy['id']
        del data_copy['id']
    else:
        original_id = None
    
    # تبدیل فیلدهای تاریخ و زمان
    for key, value in list(data_copy.items()):
        if isinstance(value, str) and ('_at' in key or key == 'due_date' or key == 'paid_date'):
            if value is not None:
                try:
                    if 'T' in value:  # تاریخ و زمان ISO format
                        data_copy[key] = datetime.fromisoformat(value)
                    else:  # فقط تاریخ
                        data_copy[key] = date.fromisoformat(value)
                except ValueError:
                    logging.warning(f"Cannot convert {key}: {value} to date/datetime")
    
    # ایجاد نمونه مدل با داده‌های JSON
    instance = model_class(**data_copy)
    
    # برگرداندن id اصلی
    if original_id is not None:
        instance.id = original_id
        
    return instance

# تابع اصلی برای وارد کردن داده‌ها
def import_database(clear_existing=False, sql_backup_file=None):
    """
    وارد کردن داده‌ها به پایگاه داده
    
    Args:
        clear_existing (bool): آیا داده‌های موجود پاک شوند
        sql_backup_file (str): مسیر فایل پشتیبان SQL برای بازیابی
        
    Returns:
        dict: آمار داده‌های وارد شده
    """
    result = {
        'status': 'success',
        'users': 0,
        'loans': 0,
        'installments': 0,
        'sql_restore': None
    }
    
    # بازیابی از فایل SQL اگر مشخص شده باشد
    if sql_backup_file and os.path.exists(sql_backup_file):
        try:
            logging.info(f"Restoring database from SQL backup: {sql_backup_file}")
            restore_success = restore_database(sql_backup_file)
            result['sql_restore'] = {
                'file': sql_backup_file,
                'success': restore_success
            }
            
            if restore_success:
                logging.info("SQL database restore completed successfully")
                # اگر بازیابی SQL موفق بود، نیازی به وارد کردن JSON نیست
                return result
            else:
                logging.warning("SQL database restore failed, falling back to JSON import")
        except Exception as e:
            logging.error(f"Error restoring database from SQL: {str(e)}")
            result['status'] = 'partial'
            result['sql_restore_error'] = str(e)
    
    # پاک کردن داده‌های موجود
    if clear_existing:
        try:
            logging.info("Clearing existing data...")
            db.session.query(Installment).delete()
            db.session.query(Loan).delete()
            db.session.query(User).delete()
            db.session.commit()
        except Exception as e:
            logging.error(f"Error clearing existing data: {str(e)}")
            db.session.rollback()
            result['status'] = 'partial'
            result['clear_error'] = str(e)
    
    # وارد کردن کاربران از JSON
    if os.path.exists('data/users.json'):
        with open('data/users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        for user_data in users_data:
            try:
                user = deserialize_model(User, user_data)
                db.session.merge(user)  # از merge استفاده می‌کنیم تا در صورت وجود آپدیت شود
                db.session.commit()
                result['users'] += 1
                logging.info(f"Imported user: {user.username} (ID: {user.id})")
            except IntegrityError as e:
                db.session.rollback()
                logging.error(f"Error importing user {user_data.get('username')}: {str(e)}")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Unexpected error importing user {user_data.get('username')}: {str(e)}")
    
    # وارد کردن وام‌ها از JSON
    if os.path.exists('data/loans.json'):
        with open('data/loans.json', 'r', encoding='utf-8') as f:
            loans_data = json.load(f)
        
        for loan_data in loans_data:
            try:
                loan = deserialize_model(Loan, loan_data)
                db.session.merge(loan)
                db.session.commit()
                result['loans'] += 1
                logging.info(f"Imported loan ID: {loan.id} (User ID: {loan.user_id})")
            except IntegrityError as e:
                db.session.rollback()
                logging.error(f"Error importing loan {loan_data.get('id')}: {str(e)}")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Unexpected error importing loan {loan_data.get('id')}: {str(e)}")
    
    # وارد کردن اقساط از JSON
    if os.path.exists('data/installments.json'):
        with open('data/installments.json', 'r', encoding='utf-8') as f:
            installments_data = json.load(f)
        
        for inst_data in installments_data:
            try:
                installment = deserialize_model(Installment, inst_data)
                db.session.merge(installment)
                db.session.commit()
                result['installments'] += 1
                logging.info(f"Imported installment ID: {installment.id} (Loan ID: {installment.loan_id})")
            except IntegrityError as e:
                db.session.rollback()
                logging.error(f"Error importing installment {inst_data.get('id')}: {str(e)}")
            except Exception as e:
                db.session.rollback()
                logging.error(f"Unexpected error importing installment {inst_data.get('id')}: {str(e)}")
    
    logging.info(f"Database import completed: {result['users']} users, {result['loans']} loans, {result['installments']} installments")
    return result

# تابع برای ذخیره فایل آپلود شده
def save_uploaded_file(uploaded_file, filename=None):
    """
    ذخیره فایل آپلود شده در سیستم
    
    Args:
        uploaded_file: فایل آپلود شده (از فایل درخواست)
        filename (str, optional): نام فایل برای ذخیره. اگر مشخص نشود، نام اصلی فایل استفاده می‌شود.
        
    Returns:
        str: مسیر فایل ذخیره شده
    """
    # اطمینان از وجود پوشه data
    os.makedirs('data', exist_ok=True)
    
    # تعیین نام فایل
    if filename is None:
        filename = uploaded_file.filename
    
    # اطمینان از امنیت نام فایل
    from werkzeug.utils import secure_filename
    filename = secure_filename(filename)
    
    # تعیین مسیر فایل
    file_path = os.path.join('data', filename)
    
    # ذخیره فایل
    uploaded_file.save(file_path)
    
    return file_path

# تابع برای بررسی و اطمینان از ایجاد جداول پایگاه داده
def ensure_database_tables():
    """
    بررسی و اطمینان از ایجاد جداول پایگاه داده
    
    Returns:
        bool: True اگر عملیات موفقیت‌آمیز بود، False در غیر این صورت
    """
    try:
        # بررسی وجود جداول
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()
        required_tables = ['users', 'loans', 'installments']
        
        # اگر همه جداول مورد نیاز وجود دارند، کاری نکن
        if all(table in existing_tables for table in required_tables):
            logging.info("All required database tables exist.")
            return True
        
        # ایجاد جداول مورد نیاز
        logging.info("Creating database tables...")
        db.create_all()
        
        # ایجاد حساب مدیر پیش‌فرض اگر وجود نداشته باشد
        from utils import create_admin_if_not_exists
        create_admin_if_not_exists()
        
        logging.info("Database tables created successfully.")
        return True
    except Exception as e:
        logging.error(f"Error ensuring database tables: {str(e)}")
        return False

# اجرای اسکریپت اگر به صورت مستقیم فراخوانی شود
if __name__ == "__main__":
    with app.app_context():
        # اطمینان از وجود جداول پایگاه داده
        ensure_database_tables()
        
        # می‌توان مسیر فایل پشتیبان SQL را نیز مشخص کرد
        # result = import_database(clear_existing=False, sql_backup_file='data/pg_backup_YYYYMMDD_HHMMSS.sql')
        result = import_database(clear_existing=False)
        
        print("Import result:")
        print(f"Status: {result['status']}")
        print(f"Imported: {result['users']} users, {result['loans']} loans, {result['installments']} installments")