import os
import pandas as pd
from datetime import datetime
from models import User, Loan, Installment
from utils import to_jalali_date, format_currency

def export_users_to_excel(users=None):
    """Export users to Excel file"""
    if users is None:
        users = User.get_all()
    
    data = []
    for user in users:
        data.append({
            'شناسه': user.id,
            'نام کاربری': user.username,
            'ایمیل': user.email,
            'نام': user.first_name,
            'نام خانوادگی': user.last_name,
            'تلفن': user.phone,
            'آدرس': user.address,
            'مدیر': 'بله' if user.is_admin else 'خیر',
            'تاریخ عضویت': to_jalali_date(user.created_at)
        })
    
    df = pd.DataFrame(data)
    
    # Create exports directory if it doesn't exist
    os.makedirs('static/exports', exist_ok=True)
    
    filename = f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    filepath = f'static/exports/{filename}'
    
    # Export to Excel
    df.to_excel(filepath, index=False, engine='xlsxwriter')
    
    return filename

def export_loans_to_excel(loans=None):
    """Export loans to Excel file"""
    if loans is None:
        loans = Loan.get_all()
    
    data = []
    for loan in loans:
        # Get loan user
        user = User.get_by_id(loan.user_id)
        
        # Get approver if exists
        approver_name = ''
        if loan.approved_by:
            approver = User.get_by_id(loan.approved_by)
            if approver:
                approver_name = f"{approver.first_name} {approver.last_name}"
        
        # Translate status to Persian
        status_translation = {
            'pending': 'در انتظار',
            'approved': 'تایید شده',
            'rejected': 'رد شده',
            'completed': 'تکمیل شده'
        }
        
        data.append({
            'شناسه': loan.id,
            'وام گیرنده': f"{user.first_name} {user.last_name}" if user else 'نامشخص',
            'مبلغ': format_currency(loan.amount),
            'مدت (ماه)': loan.duration,
            'هدف': loan.purpose,
            'وضعیت': status_translation.get(loan.status, loan.status),
            'تایید کننده': approver_name,
            'تاریخ تایید': to_jalali_date(loan.approved_at) if loan.approved_at else '',
            'تاریخ درخواست': to_jalali_date(loan.created_at)
        })
    
    df = pd.DataFrame(data)
    
    # Create exports directory if it doesn't exist
    os.makedirs('static/exports', exist_ok=True)
    
    filename = f'loans_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    filepath = f'static/exports/{filename}'
    
    # Export to Excel
    df.to_excel(filepath, index=False, engine='xlsxwriter')
    
    return filename

def export_installments_to_excel(installments=None, filter_status=None):
    """Export installments to Excel file"""
    if installments is None:
        installments = Installment.get_all()
    
    data = []
    for installment in installments:
        # Get associated loan
        loan = Loan.get_by_id(installment.loan_id)
        
        # Get loan user
        user_name = 'نامشخص'
        if loan and loan.user_id:
            user = User.get_by_id(loan.user_id)
            if user:
                user_name = f"{user.first_name} {user.last_name}"
        
        data.append({
            'شناسه': installment.id,
            'شناسه وام': installment.loan_id,
            'وام گیرنده': user_name,
            'مبلغ قسط': format_currency(installment.amount),
            'تاریخ سررسید': to_jalali_date(installment.due_date),
            'وضعیت پرداخت': 'پرداخت شده' if installment.paid else 'پرداخت نشده',
            'تاریخ پرداخت': to_jalali_date(installment.paid_date) if installment.paid_date else '',
            'تاریخ ایجاد': to_jalali_date(installment.created_at)
        })
    
    df = pd.DataFrame(data)
    
    # Create exports directory if it doesn't exist
    os.makedirs('static/exports', exist_ok=True)
    
    status_text = ''
    if filter_status:
        status_map = {
            'all': 'همه',
            'paid': 'پرداخت_شده',
            'unpaid': 'پرداخت_نشده',
            'overdue': 'معوق'
        }
        status_text = f"_{status_map.get(filter_status, '')}"
    
    filename = f'installments{status_text}_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    filepath = f'static/exports/{filename}'
    
    # Export to Excel
    df.to_excel(filepath, index=False, engine='xlsxwriter')
    
    return filename

def export_user_loans_to_excel(user_id):
    """Export loans for a specific user to Excel"""
    loans = Loan.get_by_user(user_id)
    return export_loans_to_excel(loans)

def export_loan_installments_to_excel(loan_id):
    """Export installments for a specific loan to Excel"""
    installments = Installment.get_by_loan(loan_id)
    return export_installments_to_excel(installments)