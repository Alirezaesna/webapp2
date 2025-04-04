from flask import render_template, redirect, url_for, flash, request, jsonify, abort, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from io import BytesIO

from app import app, login_manager
from models import User, Loan, Installment
from forms import (LoginForm, RegisterForm, EditProfileForm, ChangePasswordForm, 
                  LoanApplicationForm, LoanForm, InstallmentForm, UserForm,
                  LoanActionForm, InstallmentPaymentForm, InstallmentFilterForm,
                  DatabaseBackupForm, DatabaseRestoreForm)
from utils import (create_admin_if_not_exists, format_currency, create_loan_installments,
                  get_loan_progress, get_user_loan_statistics, get_system_statistics, to_jalali_date)
from excel_export import (export_users_to_excel, export_loans_to_excel, export_installments_to_excel, 
                         export_user_loans_to_excel, export_loan_installments_to_excel)
from export_db import export_database, list_backup_files
from import_db import import_database, save_uploaded_file, ensure_database_tables

# Admin user will be created when the application starts
# (moved to main.py)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

@app.template_filter('currency')
def currency_filter(value):
    return format_currency(value)

@app.template_filter('format_date')
def format_date_filter(value, format='%Y-%m-%d'):
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return value
    
    # Convert to Jalali date
    return to_jalali_date(value)

@app.context_processor
def inject_globals():
    return {
        'datetime': datetime,
        'current_year': datetime.now().year,
        'User': User,
        'Loan': Loan
    }

@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.get_by_username(form.username.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('نام کاربری یا رمز عبور نامعتبر است', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    logout_user()
    flash('شما از سیستم خارج شدید.', 'info')
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            address=form.address.data,
            is_admin=False
        )
        user.set_password(form.password.data)
        user.save()
        
        flash('حساب کاربری شما ایجاد شد! اکنون می‌توانید وارد شوید.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    loans = Loan.get_by_user(current_user.id)
    
    # Get loan statistics
    loan_stats = get_user_loan_statistics(current_user.id)
    
    # Get active loans with progress
    active_loans = []
    for loan in loans:
        if loan.status == 'approved':
            loan_data = {
                'loan': loan,
                'progress': get_loan_progress(loan)
            }
            active_loans.append(loan_data)
    
    # Get recent installments
    upcoming_installments = []
    for loan in loans:
        if loan.status == 'approved':
            progress = get_loan_progress(loan)
            upcoming_installments.extend(progress['upcoming_installments'])
    
    # Sort by due date
    upcoming_installments.sort(key=lambda x: x.due_date)
    
    return render_template('dashboard_user.html', 
                          loans=loans,
                          active_loans=active_loans,
                          loan_stats=loan_stats,
                          upcoming_installments=upcoming_installments[:5])

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Get system statistics
    stats = get_system_statistics()
    
    # Get recent loans
    loans = Loan.get_all()
    recent_loans = sorted(loans, key=lambda x: x.created_at, reverse=True)[:5]
    
    # Get users with active loans
    users = User.get_all()
    users_with_loans = []
    
    for user in users:
        if not user.is_admin:
            loan_count = len([loan for loan in loans if str(loan.user_id) == str(user.id) and loan.status != 'rejected'])
            if loan_count > 0:
                users_with_loans.append({
                    'user': user,
                    'loan_count': loan_count
                })
    
    # Get overdue installments
    installments = Installment.get_all()
    today = datetime.now().date()
    overdue_installments = []
    
    for inst in installments:
        if not inst.paid and inst.due_date < today:
            loan = Loan.get_by_id(inst.loan_id)
            if loan and loan.status == 'approved':
                user = User.get_by_id(loan.user_id)
                overdue_installments.append({
                    'installment': inst,
                    'loan': loan,
                    'user': user
                })
    
    # Sort by due date (oldest first)
    overdue_installments.sort(key=lambda x: x['installment'].due_date)
    
    return render_template('dashboard_admin.html',
                          stats=stats,
                          recent_loans=recent_loans,
                          users_with_loans=users_with_loans[:10],
                          overdue_installments=overdue_installments[:10])

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    users = User.get_all()
    return render_template('admin_users.html', users=users)

@app.route('/admin/users/export_excel')
@login_required
def admin_export_users_excel():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        filename = export_users_to_excel()
        flash(f'گزارش کاربران با موفقیت به اکسل تبدیل شد.', 'success')
        return redirect(url_for('static', filename=f'exports/{filename}'))
    except Exception as e:
        flash(f'خطا در ایجاد فایل اکسل: {str(e)}', 'danger')
        return redirect(url_for('admin_users'))

@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    form = UserForm()
    if form.validate_on_submit():
        # Check if username or email already exists
        if User.get_by_username(form.username.data):
            flash('Username already exists.', 'danger')
            return render_template('admin_user_form.html', form=form, title='Add New User')
        
        if User.get_by_email(form.email.data):
            flash('Email already exists.', 'danger')
            return render_template('admin_user_form.html', form=form, title='Add New User')
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            address=form.address.data,
            is_admin=form.is_admin.data
        )
        
        if form.password.data:
            user.set_password(form.password.data)
        else:
            # Set a default password
            user.set_password('changeme123')
        
        user.save()
        flash('User added successfully.', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_user_form.html', form=form, title='Add New User')

@app.route('/admin/users/edit/<user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_users'))
    
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        # Check if username already exists (but not for this user)
        existing_user = User.get_by_username(form.username.data)
        if existing_user and str(existing_user.id) != str(user_id):
            flash('Username already exists.', 'danger')
            return render_template('admin_user_form.html', form=form, title='Edit User')
        
        # Check if email already exists (but not for this user)
        existing_user = User.get_by_email(form.email.data)
        if existing_user and str(existing_user.id) != str(user_id):
            flash('Email already exists.', 'danger')
            return render_template('admin_user_form.html', form=form, title='Edit User')
        
        user.username = form.username.data
        user.email = form.email.data
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.phone = form.phone.data
        user.address = form.address.data
        user.is_admin = form.is_admin.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        user.save()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_user_form.html', form=form, title='Edit User')

@app.route('/admin/users/delete/<user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin_users'))
    
    # Check if user is an admin
    if user.is_admin:
        # Count admin users
        admin_count = sum(1 for u in User.get_all() if u.is_admin)
        if admin_count <= 1:
            flash('Cannot delete the only admin user.', 'danger')
            return redirect(url_for('admin_users'))
    
    # Check if user has active loans
    user_loans = Loan.get_by_user(user_id)
    active_loans = [loan for loan in user_loans if loan.status == 'approved']
    if active_loans:
        flash('Cannot delete user with active loans.', 'danger')
        return redirect(url_for('admin_users'))
    
    User.delete(user_id)
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/loans')
@login_required
def admin_loans():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Filter loans by status if provided
    status_filter = request.args.get('status', 'all')
    
    loans = Loan.get_all()
    if status_filter != 'all':
        loans = [loan for loan in loans if loan.status == status_filter]
    
    # Add user information to each loan
    loans_with_users = []
    for loan in loans:
        user = User.get_by_id(loan.user_id)
        loans_with_users.append({
            'loan': loan,
            'user': user
        })
    
    return render_template('admin_loans.html', 
                          loans=loans_with_users, 
                          status_filter=status_filter)

@app.route('/admin/loans/export_excel')
@login_required
def admin_export_loans_excel():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Filter loans by status if provided
    status_filter = request.args.get('status', 'all')
    
    loans = Loan.get_all()
    if status_filter != 'all':
        loans = [loan for loan in loans if loan.status == status_filter]
    
    try:
        filename = export_loans_to_excel(loans)
        flash(f'گزارش وام‌ها با موفقیت به اکسل تبدیل شد.', 'success')
        return redirect(url_for('static', filename=f'exports/{filename}'))
    except Exception as e:
        flash(f'خطا در ایجاد فایل اکسل: {str(e)}', 'danger')
        return redirect(url_for('admin_loans'))

@app.route('/admin/loans/add', methods=['GET', 'POST'])
@login_required
def admin_add_loan():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    form = LoanForm()
    
    # Populate user choices
    users = User.get_all()
    form.user_id.choices = [(str(user.id), f"{user.username} ({user.first_name} {user.last_name})") 
                           for user in users if not user.is_admin]
    
    if form.validate_on_submit():
        loan = Loan(
            user_id=form.user_id.data,
            amount=form.amount.data,
            duration=form.duration.data,
            purpose=form.purpose.data,
            status=form.status.data,
            approved_by=current_user.id if form.status.data == 'approved' else None,
            approved_at=datetime.now().isoformat() if form.status.data == 'approved' else None
        )
        loan.save()
        
        # Create installments if loan is approved
        if loan.status == 'approved':
            create_loan_installments(loan)
        
        flash('Loan added successfully.', 'success')
        return redirect(url_for('admin_loans'))
    
    return render_template('admin_loan_form.html', form=form, title='Add New Loan')

@app.route('/admin/loans/edit/<loan_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_loan(loan_id):
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    loan = Loan.get_by_id(loan_id)
    if not loan:
        flash('Loan not found.', 'danger')
        return redirect(url_for('admin_loans'))
    
    form = LoanForm(obj=loan)
    
    # Populate user choices
    users = User.get_all()
    form.user_id.choices = [(str(user.id), f"{user.username} ({user.first_name} {user.last_name})") 
                           for user in users if not user.is_admin]
    
    if form.validate_on_submit():
        original_status = loan.status
        
        loan.user_id = form.user_id.data
        loan.amount = form.amount.data
        loan.duration = form.duration.data
        loan.purpose = form.purpose.data
        loan.status = form.status.data
        
        # Set approval details if status changed to approved
        if loan.status == 'approved' and original_status != 'approved':
            loan.approved_by = current_user.id
            loan.approved_at = datetime.now().isoformat()
        
        loan.save()
        
        # Create or update installments if loan is approved
        if loan.status == 'approved' and (original_status != 'approved' or 
                                          form.amount.data != loan.amount or
                                          form.duration.data != loan.duration):
            create_loan_installments(loan)
        
        flash('Loan updated successfully.', 'success')
        return redirect(url_for('admin_loans'))
    
    return render_template('admin_loan_form.html', form=form, title='Edit Loan')

@app.route('/admin/loans/view/<loan_id>')
@login_required
def admin_view_loan(loan_id):
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    loan = Loan.get_by_id(loan_id)
    if not loan:
        flash('Loan not found.', 'danger')
        return redirect(url_for('admin_loans'))
    
    user = User.get_by_id(loan.user_id)
    approved_by = User.get_by_id(loan.approved_by) if loan.approved_by else None
    
    # Get loan progress
    progress = get_loan_progress(loan)
    
    # Get installments
    installments = sorted(Installment.get_by_loan(loan_id), key=lambda x: x.due_date)
    
    return render_template('view_loan.html', 
                          loan=loan, 
                          user=user, 
                          approved_by=approved_by,
                          progress=progress,
                          installments=installments,
                          is_admin=True)

@app.route('/admin/loans/action', methods=['POST'])
@login_required
def admin_loan_action():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    form = LoanActionForm()
    if form.validate_on_submit():
        loan = Loan.get_by_id(form.loan_id.data)
        if not loan:
            flash('Loan not found.', 'danger')
            return redirect(url_for('admin_loans'))
        
        if form.action.data == 'approve':
            loan.status = 'approved'
            loan.approved_by = current_user.id
            loan.approved_at = datetime.now().isoformat()
            loan.save()
            
            # Create installments
            create_loan_installments(loan)
            
            flash('Loan approved successfully.', 'success')
        
        elif form.action.data == 'reject':
            loan.status = 'rejected'
            loan.save()
            flash('Loan rejected.', 'success')
        
        elif form.action.data == 'complete':
            loan.status = 'completed'
            loan.save()
            flash('Loan marked as completed.', 'success')
        
        elif form.action.data == 'delete':
            # Delete all installments first
            Installment.delete_by_loan(loan.id)
            # Then delete the loan
            Loan.delete(loan.id)
            flash('Loan deleted successfully.', 'success')
            return redirect(url_for('admin_loans'))
        
        return redirect(url_for('admin_view_loan', loan_id=loan.id))
    
    flash('Invalid form submission.', 'danger')
    return redirect(url_for('admin_loans'))

@app.route('/admin/installments')
@login_required
def admin_installments():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    form = InstallmentFilterForm(request.args, meta={'csrf': False})
    
    installments = Installment.get_all()
    today = datetime.now().date()
    
    # Filter by status
    if form.status.data == 'paid':
        installments = [inst for inst in installments if inst.paid]
    elif form.status.data == 'unpaid':
        installments = [inst for inst in installments if not inst.paid]
    elif form.status.data == 'overdue':
        installments = [inst for inst in installments if not inst.paid and 
                        inst.due_date < today]
    
    # Add loan and user information
    installments_with_info = []
    for inst in installments:
        loan = Loan.get_by_id(inst.loan_id)
        if loan and loan.status == 'approved':  # Only show installments for approved loans
            user = User.get_by_id(loan.user_id)
            installments_with_info.append({
                'installment': inst,
                'loan': loan,
                'user': user
            })
    
    # Sort by due date
    installments_with_info.sort(key=lambda x: x['installment'].due_date)
    
    return render_template('admin_installments.html', 
                          installments=installments_with_info,
                          form=form)

@app.route('/admin/installments/export_excel')
@login_required
def admin_export_installments_excel():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Get filter status from query parameters
    status_filter = request.args.get('status', 'all')
    
    installments = Installment.get_all()
    today = datetime.now().date()
    
    # Filter by status
    if status_filter == 'paid':
        installments = [inst for inst in installments if inst.paid]
    elif status_filter == 'unpaid':
        installments = [inst for inst in installments if not inst.paid]
    elif status_filter == 'overdue':
        installments = [inst for inst in installments if not inst.paid and inst.due_date < today]
    
    # Filter to only include installments for approved loans
    filtered_installments = []
    for inst in installments:
        loan = Loan.get_by_id(inst.loan_id)
        if loan and loan.status == 'approved':
            filtered_installments.append(inst)
    
    try:
        filename = export_installments_to_excel(filtered_installments, status_filter)
        flash(f'گزارش اقساط با موفقیت به اکسل تبدیل شد.', 'success')
        return redirect(url_for('static', filename=f'exports/{filename}'))
    except Exception as e:
        flash(f'خطا در ایجاد فایل اکسل: {str(e)}', 'danger')
        return redirect(url_for('admin_installments'))

@app.route('/admin/installments/add', methods=['GET', 'POST'])
@login_required
def admin_add_installment():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    form = InstallmentForm()
    
    # Populate loan choices
    loans = Loan.get_all()
    approved_loans = []
    for loan in loans:
        if loan.status == 'approved':
            user = User.get_by_id(loan.user_id)
            if user:
                approved_loans.append((str(loan.id), f"{user.username} - {format_currency(loan.amount)}"))
    
    form.loan_id.choices = approved_loans
    
    if form.validate_on_submit():
        installment = Installment(
            loan_id=form.loan_id.data,
            amount=form.amount.data,
            due_date=form.due_date.data,
            paid=form.paid.data,
            paid_date=form.paid_date.data if form.paid.data and form.paid_date.data else None
        )
        installment.save()
        flash('Installment added successfully.', 'success')
        return redirect(url_for('admin_installments'))
    
    return render_template('admin_installment_form.html', form=form, title='Add New Installment')

@app.route('/admin/installments/edit/<installment_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_installment(installment_id):
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    installment = Installment.get_by_id(installment_id)
    if not installment:
        flash('Installment not found.', 'danger')
        return redirect(url_for('admin_installments'))
    
    form = InstallmentForm(obj=installment)
    
    # Due date and paid date are already date objects
    form.due_date.data = installment.due_date
    form.paid_date.data = installment.paid_date
    
    # Populate loan choices
    loans = Loan.get_all()
    approved_loans = []
    for loan in loans:
        if loan.status == 'approved':
            user = User.get_by_id(loan.user_id)
            if user:
                approved_loans.append((str(loan.id), f"{user.username} - {format_currency(loan.amount)}"))
    
    form.loan_id.choices = approved_loans
    
    if form.validate_on_submit():
        installment.loan_id = form.loan_id.data
        installment.amount = form.amount.data
        installment.due_date = form.due_date.data
        installment.paid = form.paid.data
        installment.paid_date = form.paid_date.data if form.paid.data and form.paid_date.data else None
        
        installment.save()
        flash('Installment updated successfully.', 'success')
        return redirect(url_for('admin_installments'))
    
    return render_template('admin_installment_form.html', form=form, title='Edit Installment')

@app.route('/admin/installments/pay/<installment_id>', methods=['POST'])
@login_required
def admin_pay_installment(installment_id):
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    installment = Installment.get_by_id(installment_id)
    if not installment:
        flash('Installment not found.', 'danger')
        return redirect(url_for('admin_installments'))
    
    installment.paid = True
    installment.paid_date = datetime.now().date()
    installment.save()
    
    # Check if all installments are paid for this loan
    loan = Loan.get_by_id(installment.loan_id)
    if loan:
        installments = Installment.get_by_loan(loan.id)
        all_paid = all(inst.paid for inst in installments)
        
        # If all paid, mark loan as completed
        if all_paid and loan.status == 'approved':
            loan.status = 'completed'
            loan.save()
    
    flash('Installment marked as paid.', 'success')
    return redirect(url_for('admin_installments'))

@app.route('/admin/installments/delete/<installment_id>', methods=['POST'])
@login_required
def admin_delete_installment(installment_id):
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    installment = Installment.get_by_id(installment_id)
    if not installment:
        flash('Installment not found.', 'danger')
        return redirect(url_for('admin_installments'))
    
    # Try to delete the installment
    print(f"Attempting to delete installment ID: {installment_id}")
    
    # Convert ID to str and then let the model convert it to int
    result = Installment.delete(str(installment_id))
    
    if result:
        flash('Installment deleted successfully.', 'success')
    else:
        flash('Error: Could not delete installment. Please try again.', 'danger')
        
    return redirect(url_for('admin_installments'))

@app.route('/apply-loan', methods=['GET', 'POST'])
@login_required
def apply_loan():
    if current_user.is_admin:
        flash('Admins cannot apply for loans.', 'warning')
        return redirect(url_for('admin_dashboard'))
    
    form = LoanApplicationForm()
    if form.validate_on_submit():
        loan = Loan(
            user_id=current_user.id,
            amount=form.amount.data,
            duration=form.duration.data,
            purpose=form.purpose.data,
            status='pending'
        )
        loan.save()
        flash('Loan application submitted successfully. It will be reviewed by an admin.', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('apply_loan.html', form=form)

@app.route('/my-loans')
@login_required
def my_loans():
    if current_user.is_admin:
        return redirect(url_for('admin_loans'))
    
    loans = Loan.get_by_user(current_user.id)
    
    # Add loan progress information
    loans_with_progress = []
    for loan in loans:
        progress = get_loan_progress(loan)
        loans_with_progress.append({
            'loan': loan,
            'progress': progress
        })
    
    return render_template('my_loans.html', loans=loans_with_progress)

@app.route('/my-loans/export_excel')
@login_required
def export_my_loans_excel():
    if current_user.is_admin:
        return redirect(url_for('admin_export_loans_excel'))
    
    try:
        filename = export_user_loans_to_excel(current_user.id)
        flash(f'گزارش وام‌های شما با موفقیت به اکسل تبدیل شد.', 'success')
        return redirect(url_for('static', filename=f'exports/{filename}'))
    except Exception as e:
        flash(f'خطا در ایجاد فایل اکسل: {str(e)}', 'danger')
        return redirect(url_for('my_loans'))

@app.route('/view-loan/<loan_id>')
@login_required
def view_loan(loan_id):
    loan = Loan.get_by_id(loan_id)
    if not loan:
        flash('Loan not found.', 'danger')
        return redirect(url_for('my_loans'))
    
    # Check if the loan belongs to the current user or if user is admin
    if str(loan.user_id) != str(current_user.id) and not current_user.is_admin:
        flash('You do not have permission to view this loan.', 'danger')
        return redirect(url_for('my_loans'))
    
    user = User.get_by_id(loan.user_id)
    approved_by = User.get_by_id(loan.approved_by) if loan.approved_by else None
    
    # Get loan progress
    progress = get_loan_progress(loan)
    
    # Get installments
    installments = sorted(Installment.get_by_loan(loan_id), key=lambda x: x.due_date)
    
    return render_template('view_loan.html', 
                          loan=loan, 
                          user=user, 
                          approved_by=approved_by,
                          progress=progress,
                          installments=installments,
                          is_admin=current_user.is_admin)

@app.route('/view-loan/<loan_id>/export_installments_excel')
@login_required
def export_loan_installments_excel(loan_id):
    loan = Loan.get_by_id(loan_id)
    if not loan:
        flash('Loan not found.', 'danger')
        return redirect(url_for('my_loans'))
    
    # Check if the loan belongs to the current user or if user is admin
    if str(loan.user_id) != str(current_user.id) and not current_user.is_admin:
        flash('You do not have permission to view this loan.', 'danger')
        return redirect(url_for('my_loans'))
    
    try:
        filename = export_loan_installments_to_excel(loan_id)
        flash(f'گزارش اقساط وام با موفقیت به اکسل تبدیل شد.', 'success')
        return redirect(url_for('static', filename=f'exports/{filename}'))
    except Exception as e:
        flash(f'خطا در ایجاد فایل اکسل: {str(e)}', 'danger')
        return redirect(url_for('view_loan', loan_id=loan_id))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = EditProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        # Check if email is already taken by another user
        existing_user = User.get_by_email(form.email.data)
        if existing_user and str(existing_user.id) != str(current_user.id):
            flash('Email already exists.', 'danger')
        else:
            current_user.email = form.email.data
            current_user.first_name = form.first_name.data
            current_user.last_name = form.last_name.data
            current_user.phone = form.phone.data
            current_user.address = form.address.data
            
            current_user.save()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('profile'))
    
    return render_template('profile.html', form=form)

@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            current_user.save()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('profile'))
    
    return render_template('change_password.html', form=form)

@app.route('/admin/database')
@login_required
def admin_database_management():
    """پنل مدیریت پشتیبان‌گیری و بازیابی پایگاه داده"""
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # فرم‌های مورد نیاز
    backup_form = DatabaseBackupForm()
    restore_form = DatabaseRestoreForm()
    
    # لیست فایل‌های پشتیبان موجود
    backup_files = list_backup_files()
    
    # آمار پایگاه داده
    from pg_db_utils import get_db_statistics
    db_stats = get_db_statistics()
    
    # اطمینان از وجود جداول پایگاه داده
    ensure_database_tables()
    
    return render_template('admin_database.html',
                          backup_form=backup_form,
                          restore_form=restore_form,
                          backup_files=backup_files,
                          db_stats=db_stats)

@app.route('/admin/database/backup', methods=['POST'])
@login_required
def admin_database_backup():
    """ایجاد نسخه پشتیبان از پایگاه داده"""
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    form = DatabaseBackupForm()
    if form.validate_on_submit():
        try:
            backup_type = form.backup_type.data
            
            if backup_type == 'json':
                # فقط پشتیبان JSON
                result = export_database(postgres_backup=False, json_backup=True)
            elif backup_type == 'sql':
                # فقط پشتیبان SQL
                result = export_database(postgres_backup=True, json_backup=False)
            else:
                # هر دو نوع پشتیبان
                result = export_database(postgres_backup=True, json_backup=True)
            
            if result['status'] == 'success':
                flash('نسخه پشتیبان با موفقیت ایجاد شد.', 'success')
            else:
                flash('نسخه پشتیبان با مشکلاتی ایجاد شد. لطفا لاگ‌ها را بررسی کنید.', 'warning')
        except Exception as e:
            flash(f'خطا در ایجاد نسخه پشتیبان: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"خطا در فیلد {getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('admin_database_management'))

@app.route('/admin/database/restore', methods=['POST'])
@login_required
def admin_database_restore():
    """بازیابی پایگاه داده از فایل پشتیبان"""
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    form = DatabaseRestoreForm()
    if form.validate_on_submit():
        try:
            # ذخیره فایل آپلود شده
            uploaded_file = form.backup_file.data
            clear_existing = form.clear_existing.data
            
            # تعیین نوع فایل
            is_sql = uploaded_file.filename.lower().endswith('.sql')
            
            # ذخیره فایل
            file_path = save_uploaded_file(uploaded_file)
            
            # بازیابی پایگاه داده
            if is_sql:
                # بازیابی از فایل SQL
                result = import_database(clear_existing=clear_existing, sql_backup_file=file_path)
            else:
                # بازیابی از فایل JSON
                result = import_database(clear_existing=clear_existing)
            
            if result['status'] == 'success':
                flash('پایگاه داده با موفقیت بازیابی شد.', 'success')
            else:
                flash('پایگاه داده با مشکلاتی بازیابی شد. لطفا لاگ‌ها را بررسی کنید.', 'warning')
        except Exception as e:
            flash(f'خطا در بازیابی پایگاه داده: {str(e)}', 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"خطا در فیلد {getattr(form, field).label.text}: {error}", 'danger')
    
    return redirect(url_for('admin_database_management'))

@app.route('/admin/database/download/<path:filename>')
@login_required
def admin_database_download(filename):
    """دانلود فایل پشتیبان"""
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    try:
        # تعیین مسیر فایل
        file_path = os.path.join('data', secure_filename(filename))
        
        # بررسی وجود فایل
        if not os.path.exists(file_path):
            flash('فایل مورد نظر یافت نشد.', 'danger')
            return redirect(url_for('admin_database_management'))
        
        # دانلود فایل
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        flash(f'خطا در دانلود فایل: {str(e)}', 'danger')
        return redirect(url_for('admin_database_management'))

@app.route('/reports')
@login_required
def reports():
    if not current_user.is_admin:
        flash('Access denied: Admin privileges required.', 'danger')
        return redirect(url_for('user_dashboard'))
    
    # Get system statistics
    stats = get_system_statistics()
    
    # Get loan status distribution for chart
    loan_status = {
        'approved': stats['active_loans'],
        'completed': stats['completed_loans'],
        'pending': stats['pending_loans'],
        'rejected': stats['rejected_loans']
    }
    
    # Get installment status distribution for chart
    installment_status = {
        'paid': stats['paid_installments'],
        'unpaid': stats['unpaid_installments'] - stats['overdue_installments'],
        'overdue': stats['overdue_installments']
    }
    
    # Get monthly loan data for trend chart
    loans = Loan.get_all()
    monthly_data = {}
    
    for loan in loans:
        if loan.status in ['approved', 'completed']:
            # Get month and year from created_at
            # loan.created_at is already a datetime object, no need to parse
            month_year = loan.created_at.strftime('%Y-%m')
            
            if month_year not in monthly_data:
                monthly_data[month_year] = {
                    'count': 0,
                    'amount': 0
                }
            
            monthly_data[month_year]['count'] += 1
            monthly_data[month_year]['amount'] += float(loan.amount)
    
    # Sort monthly data by date
    sorted_months = sorted(monthly_data.keys())
    
    monthly_loan_counts = [monthly_data[month]['count'] for month in sorted_months]
    monthly_loan_amounts = [monthly_data[month]['amount'] for month in sorted_months]
    
    return render_template('reports.html', 
                          stats=stats,
                          loan_status=loan_status,
                          installment_status=installment_status,
                          months=sorted_months,
                          monthly_loan_counts=monthly_loan_counts,
                          monthly_loan_amounts=monthly_loan_amounts)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
