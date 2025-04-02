import json
import os
from datetime import datetime, date
from app import app, db
from models import User, Loan, Installment
from sqlalchemy.exc import IntegrityError

# تابع تبدیل داده‌های JSON به مدل‌های SQLAlchemy
def deserialize_model(model_class, data):
    # حذف کلید id برای جلوگیری از تداخل با کلیدهای خودکار
    if 'id' in data:
        del data['id']
    
    # تبدیل فیلدهای تاریخ و زمان
    for key, value in list(data.items()):
        if isinstance(value, str) and ('_at' in key or key == 'due_date' or key == 'paid_date'):
            if value is not None:
                try:
                    if 'T' in value:  # تاریخ و زمان ISO format
                        data[key] = datetime.fromisoformat(value)
                    else:  # فقط تاریخ
                        data[key] = date.fromisoformat(value)
                except ValueError:
                    print(f"Cannot convert {key}: {value} to date/datetime")
    
    # ایجاد نمونه مدل با داده‌های JSON
    instance = model_class(**data)
    return instance

# تابع اصلی برای وارد کردن داده‌ها
def import_database(clear_existing=False):
    if clear_existing:
        print("Clearing existing data...")
        db.session.query(Installment).delete()
        db.session.query(Loan).delete()
        db.session.query(User).delete()
        db.session.commit()
    
    # وارد کردن کاربران
    if os.path.exists('data/users.json'):
        with open('data/users.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        for user_data in users_data:
            # ذخیره id اصلی برای استفاده بعدی
            original_id = user_data['id']
            
            user = deserialize_model(User, user_data)
            user.id = original_id  # تنظیم id به مقدار اصلی
            
            try:
                db.session.merge(user)  # از merge استفاده می‌کنیم تا در صورت وجود آپدیت شود
                db.session.commit()
                print(f"Imported user: {user.username} (ID: {user.id})")
            except IntegrityError as e:
                db.session.rollback()
                print(f"Error importing user {user.username}: {str(e)}")
    
    # وارد کردن وام‌ها
    if os.path.exists('data/loans.json'):
        with open('data/loans.json', 'r', encoding='utf-8') as f:
            loans_data = json.load(f)
        
        for loan_data in loans_data:
            original_id = loan_data['id']
            
            loan = deserialize_model(Loan, loan_data)
            loan.id = original_id
            
            try:
                db.session.merge(loan)
                db.session.commit()
                print(f"Imported loan ID: {loan.id} (User ID: {loan.user_id})")
            except IntegrityError as e:
                db.session.rollback()
                print(f"Error importing loan {loan.id}: {str(e)}")
    
    # وارد کردن اقساط
    if os.path.exists('data/installments.json'):
        with open('data/installments.json', 'r', encoding='utf-8') as f:
            installments_data = json.load(f)
        
        for inst_data in installments_data:
            original_id = inst_data['id']
            
            installment = deserialize_model(Installment, inst_data)
            installment.id = original_id
            
            try:
                db.session.merge(installment)
                db.session.commit()
                print(f"Imported installment ID: {installment.id} (Loan ID: {installment.loan_id})")
            except IntegrityError as e:
                db.session.rollback()
                print(f"Error importing installment {installment.id}: {str(e)}")
    
    print("Database import completed.")

# اجرای اسکریپت با پارامتر clear_existing=False برای حفظ داده‌های موجود
# اگر می‌خواهید قبل از وارد کردن داده‌ها، داده‌های موجود پاک شوند، از clear_existing=True استفاده کنید
with app.app_context():
    import_database(clear_existing=False)