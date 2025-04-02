import json
import os
from datetime import datetime, timedelta
from models import User, Loan, Installment

def create_admin_if_not_exists():
    """Create admin user if no admin exists"""
    admin = None
    for user in User.get_all():
        if user.is_admin:
            admin = user
            break
    
    if admin is None:
        admin = User(
            username="admin",
            email="admin@qardhasanah.com",
            first_name="System",
            last_name="Admin",
            phone="1234567890",
            address="System",
            is_admin=True
        )
        admin.set_password("admin123")  # Default password, should be changed
        admin.save()
        print("Admin user created with username 'admin' and password 'admin123'")

def format_currency(amount):
    """Format a number as currency"""
    return f"{float(amount):,.2f}"

def create_loan_installments(loan):
    """Create installments for a loan"""
    # Delete any existing installments for this loan
    Installment.delete_by_loan(loan.id)
    
    # Calculate installment amount
    installment_amount = float(loan.amount) / int(loan.duration)
    
    # Create installments
    for i in range(1, int(loan.duration) + 1):
        due_date = (datetime.fromisoformat(loan.created_at.split('T')[0]) + timedelta(days=30*i)).strftime('%Y-%m-%d')
        installment = Installment(
            loan_id=loan.id,
            amount=round(installment_amount, 2),
            due_date=due_date,
            paid=False
        )
        installment.save()

def get_loan_progress(loan):
    """Calculate loan progress and statistics"""
    installments = Installment.get_by_loan(loan.id)
    
    total_amount = float(loan.amount)
    total_installments = len(installments)
    paid_installments = sum(1 for inst in installments if inst.paid)
    paid_amount = sum(float(inst.amount) for inst in installments if inst.paid)
    
    # Calculate percentage completion
    completion_percentage = 0
    if total_amount > 0:
        completion_percentage = (paid_amount / total_amount) * 100
    
    # Check for overdue installments
    today = datetime.now().date()
    overdue_installments = []
    upcoming_installments = []
    
    for inst in installments:
        if not inst.paid and datetime.strptime(inst.due_date, '%Y-%m-%d').date() < today:
            overdue_installments.append(inst)
        elif not inst.paid:
            upcoming_installments.append(inst)
    
    return {
        'total_amount': total_amount,
        'total_installments': total_installments,
        'paid_installments': paid_installments,
        'remaining_installments': total_installments - paid_installments,
        'paid_amount': paid_amount,
        'remaining_amount': total_amount - paid_amount,
        'completion_percentage': completion_percentage,
        'overdue_installments': len(overdue_installments),
        'upcoming_installments': upcoming_installments[:3] if upcoming_installments else []
    }

def get_user_loan_statistics(user_id):
    """Get loan statistics for a user"""
    user_loans = Loan.get_by_user(user_id)
    
    active_loans = [loan for loan in user_loans if loan.status == 'approved']
    completed_loans = [loan for loan in user_loans if loan.status == 'completed']
    pending_loans = [loan for loan in user_loans if loan.status == 'pending']
    
    # Calculate total borrowed amount
    total_borrowed = sum(float(loan.amount) for loan in user_loans if loan.status in ['approved', 'completed'])
    
    # Calculate total remaining amount
    total_remaining = 0
    for loan in active_loans:
        progress = get_loan_progress(loan)
        total_remaining += progress['remaining_amount']
    
    # Get overdue installments
    overdue_count = 0
    for loan in active_loans:
        progress = get_loan_progress(loan)
        overdue_count += progress['overdue_installments']
    
    return {
        'active_loan_count': len(active_loans),
        'completed_loan_count': len(completed_loans),
        'pending_loan_count': len(pending_loans),
        'total_borrowed': total_borrowed,
        'total_remaining': total_remaining,
        'overdue_installments': overdue_count
    }

def get_system_statistics():
    """Get overall system statistics"""
    users = User.get_all()
    loans = Loan.get_all()
    installments = Installment.get_all()
    
    # User statistics
    total_users = len(users)
    admin_users = sum(1 for user in users if user.is_admin)
    normal_users = total_users - admin_users
    
    # Loan statistics
    total_loans = len(loans)
    active_loans = sum(1 for loan in loans if loan.status == 'approved')
    completed_loans = sum(1 for loan in loans if loan.status == 'completed')
    pending_loans = sum(1 for loan in loans if loan.status == 'pending')
    rejected_loans = sum(1 for loan in loans if loan.status == 'rejected')
    
    # Financial statistics
    total_loan_amount = sum(float(loan.amount) for loan in loans if loan.status in ['approved', 'completed'])
    
    # Installment statistics
    total_installments = len(installments)
    paid_installments = sum(1 for inst in installments if inst.paid)
    unpaid_installments = total_installments - paid_installments
    
    # Overdue installments
    today = datetime.now().date()
    overdue_installments = sum(1 for inst in installments 
                              if not inst.paid and datetime.strptime(inst.due_date, '%Y-%m-%d').date() < today)
    
    return {
        'total_users': total_users,
        'admin_users': admin_users,
        'normal_users': normal_users,
        'total_loans': total_loans,
        'active_loans': active_loans,
        'completed_loans': completed_loans,
        'pending_loans': pending_loans,
        'rejected_loans': rejected_loans,
        'total_loan_amount': total_loan_amount,
        'total_installments': total_installments,
        'paid_installments': paid_installments,
        'unpaid_installments': unpaid_installments,
        'overdue_installments': overdue_installments
    }
