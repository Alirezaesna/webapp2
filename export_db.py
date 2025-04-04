import json
import os
import logging
from datetime import datetime
from app import app, db
from models import User, Loan, Installment
from pg_db_utils import backup_database

# تنظیم لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# تابع تبدیل داده‌ها به فرمت قابل سریالایز برای JSON
def serialize_model(obj):
    data = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            data[column.name] = value.isoformat()
        elif hasattr(value, 'isoformat'):  # برای اشیاء date
            data[column.name] = value.isoformat()
        else:
            data[column.name] = value
    return data

# تابع استخراج داده‌ها به فرمت JSON
def export_database_to_json():
    """
    صادر کردن داده‌های پایگاه داده به فایل‌های JSON
    
    Returns:
        dict: آمار داده‌های استخراج شده
    """
    # اطمینان از وجود پوشه data
    os.makedirs('data', exist_ok=True)
    
    # استخراج کاربران
    users = User.query.all()
    users_data = [serialize_model(user) for user in users]
    with open('data/users.json', 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)
    logging.info(f"Exported {len(users_data)} users to data/users.json")
    
    # استخراج وام‌ها
    loans = Loan.query.all()
    loans_data = [serialize_model(loan) for loan in loans]
    with open('data/loans.json', 'w', encoding='utf-8') as f:
        json.dump(loans_data, f, ensure_ascii=False, indent=4)
    logging.info(f"Exported {len(loans_data)} loans to data/loans.json")
    
    # استخراج اقساط
    installments = Installment.query.all()
    installments_data = [serialize_model(installment) for installment in installments]
    with open('data/installments.json', 'w', encoding='utf-8') as f:
        json.dump(installments_data, f, ensure_ascii=False, indent=4)
    logging.info(f"Exported {len(installments_data)} installments to data/installments.json")
    
    return {
        'users': len(users_data),
        'loans': len(loans_data),
        'installments': len(installments_data)
    }

# تابع اصلی که هر دو روش استخراج را انجام می‌دهد
def export_database(postgres_backup=True, json_backup=True):
    """
    پشتیبان‌گیری از پایگاه داده با روش‌های پیشرفته
    
    Args:
        postgres_backup (bool): آیا از PostgreSQL نسخه پشتیبان تهیه شود
        json_backup (bool): آیا داده‌ها به فرمت JSON استخراج شوند
        
    Returns:
        dict: گزارش عملیات پشتیبان‌گیری
    """
    result = {'status': 'success', 'json': None, 'postgres': None}
    
    # استخراج به فرمت JSON
    if json_backup:
        try:
            json_result = export_database_to_json()
            result['json'] = json_result
            logging.info(f"JSON export completed: {json_result}")
        except Exception as e:
            logging.error(f"JSON export failed: {str(e)}")
            result['status'] = 'partial'
            result['json_error'] = str(e)
    
    # تهیه نسخه پشتیبان PostgreSQL
    if postgres_backup:
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'data/pg_backup_{timestamp}.sql'
            backup_path = backup_database(backup_file)
            
            if backup_path:
                result['postgres'] = {'file': backup_path}
                logging.info(f"PostgreSQL backup completed: {backup_path}")
            else:
                result['status'] = 'partial'
                result['postgres_error'] = "Backup operation failed"
                logging.error("PostgreSQL backup failed")
        except Exception as e:
            logging.error(f"PostgreSQL backup failed: {str(e)}")
            result['status'] = 'partial'
            result['postgres_error'] = str(e)
    
    return result

# اجرای اسکریپت در context برنامه
if __name__ == "__main__":
    with app.app_context():
        result = export_database()
        if result['status'] == 'success':
            print("Database export completed successfully.")
            if result.get('json'):
                print(f"JSON Summary: {result['json']['users']} users, {result['json']['loans']} loans, {result['json']['installments']} installments")
            if result.get('postgres'):
                print(f"PostgreSQL backup saved to: {result['postgres']['file']}")
        else:
            print("Database export completed with some issues. Check the logs for details.")