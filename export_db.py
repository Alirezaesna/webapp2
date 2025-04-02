import json
import os
from datetime import datetime
from app import app, db
from models import User, Loan, Installment

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

# تابع اصلی برای استخراج داده‌ها
def export_database():
    # اطمینان از وجود پوشه data
    os.makedirs('data', exist_ok=True)
    
    # استخراج کاربران
    users = User.query.all()
    users_data = [serialize_model(user) for user in users]
    with open('data/users.json', 'w', encoding='utf-8') as f:
        json.dump(users_data, f, ensure_ascii=False, indent=4)
    print(f"Exported {len(users_data)} users to data/users.json")
    
    # استخراج وام‌ها
    loans = Loan.query.all()
    loans_data = [serialize_model(loan) for loan in loans]
    with open('data/loans.json', 'w', encoding='utf-8') as f:
        json.dump(loans_data, f, ensure_ascii=False, indent=4)
    print(f"Exported {len(loans_data)} loans to data/loans.json")
    
    # استخراج اقساط
    installments = Installment.query.all()
    installments_data = [serialize_model(installment) for installment in installments]
    with open('data/installments.json', 'w', encoding='utf-8') as f:
        json.dump(installments_data, f, ensure_ascii=False, indent=4)
    print(f"Exported {len(installments_data)} installments to data/installments.json")
    
    return {
        'users': len(users_data),
        'loans': len(loans_data),
        'installments': len(installments_data)
    }

# اجرای اسکریپت در context برنامه
with app.app_context():
    result = export_database()
    print("Database export completed successfully.")
    print(f"Summary: {result['users']} users, {result['loans']} loans, {result['installments']} installments")