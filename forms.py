from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    password = PasswordField('رمز عبور', validators=[DataRequired()])
    remember_me = BooleanField('مرا به خاطر بسپار')
    submit = SubmitField('ورود')

class RegisterForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تکرار رمز عبور', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('نام', validators=[DataRequired()])
    last_name = StringField('نام خانوادگی', validators=[DataRequired()])
    phone = StringField('شماره تلفن', validators=[DataRequired()])
    address = TextAreaField('آدرس', validators=[DataRequired()])
    submit = SubmitField('ثبت نام')
    
    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if user is not None:
            raise ValidationError('این نام کاربری قبلا استفاده شده است. لطفا از نام دیگری استفاده کنید.')
    
    def validate_email(self, email):
        user = User.get_by_email(email.data)
        if user is not None:
            raise ValidationError('این ایمیل قبلا ثبت شده است. لطفا از ایمیل دیگری استفاده کنید.')

class EditProfileForm(FlaskForm):
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    first_name = StringField('نام', validators=[DataRequired()])
    last_name = StringField('نام خانوادگی', validators=[DataRequired()])
    phone = StringField('شماره تلفن', validators=[DataRequired()])
    address = TextAreaField('آدرس', validators=[DataRequired()])
    submit = SubmitField('بروزرسانی پروفایل')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('رمز عبور فعلی', validators=[DataRequired()])
    new_password = PasswordField('رمز عبور جدید', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تکرار رمز عبور جدید', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('تغییر رمز عبور')

class UserForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور', validators=[Optional(), Length(min=6)])
    first_name = StringField('نام', validators=[DataRequired()])
    last_name = StringField('نام خانوادگی', validators=[DataRequired()])
    phone = StringField('شماره تلفن', validators=[DataRequired()])
    address = TextAreaField('آدرس', validators=[DataRequired()])
    is_admin = BooleanField('کاربر مدیر')
    submit = SubmitField('ذخیره کاربر')

class LoanApplicationForm(FlaskForm):
    amount = FloatField('مبلغ وام', validators=[DataRequired(), NumberRange(min=0.01)])
    duration = IntegerField('مدت زمان (ماه)', validators=[DataRequired(), NumberRange(min=1, max=120)])
    purpose = TextAreaField('هدف از دریافت وام', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('ثبت درخواست وام')

class LoanForm(FlaskForm):
    user_id = SelectField('کاربر', coerce=str, validators=[DataRequired()])
    amount = FloatField('مبلغ وام', validators=[DataRequired(), NumberRange(min=0.01)])
    duration = IntegerField('مدت زمان (ماه)', validators=[DataRequired(), NumberRange(min=1, max=120)])
    purpose = TextAreaField('هدف از دریافت وام', validators=[DataRequired(), Length(min=10)])
    status = SelectField('وضعیت', choices=[
        ('pending', 'در انتظار'),
        ('approved', 'تایید شده'),
        ('rejected', 'رد شده'),
        ('completed', 'تکمیل شده')
    ], validators=[DataRequired()])
    submit = SubmitField('ذخیره وام')

class InstallmentForm(FlaskForm):
    loan_id = SelectField('وام', coerce=str, validators=[DataRequired()])
    amount = FloatField('مبلغ قسط', validators=[DataRequired(), NumberRange(min=0.01)])
    due_date = DateField('تاریخ سررسید', format='%Y-%m-%d', validators=[DataRequired()])
    paid = BooleanField('پرداخت شده')
    paid_date = DateField('تاریخ پرداخت', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('ذخیره قسط')

class LoanActionForm(FlaskForm):
    loan_id = HiddenField('شناسه وام', validators=[DataRequired()])
    action = HiddenField('عملیات', validators=[DataRequired()])
    submit = SubmitField('تایید')

class InstallmentPaymentForm(FlaskForm):
    installment_id = HiddenField('شناسه قسط', validators=[DataRequired()])
    submit = SubmitField('علامت‌گذاری به عنوان پرداخت شده')

class InstallmentFilterForm(FlaskForm):
    status = SelectField('وضعیت', choices=[
        ('all', 'همه اقساط'),
        ('paid', 'اقساط پرداخت شده'),
        ('unpaid', 'اقساط پرداخت نشده'),
        ('overdue', 'اقساط معوق')
    ])
    submit = SubmitField('فیلتر')

class DatabaseBackupForm(FlaskForm):
    backup_type = SelectField('نوع پشتیبان‌گیری', choices=[
        ('json', 'JSON (همه داده‌ها)'),
        ('sql', 'SQL (پایگاه داده کامل)'),
        ('both', 'هر دو فرمت')
    ], default='both')
    submit = SubmitField('ایجاد نسخه پشتیبان')

class DatabaseRestoreForm(FlaskForm):
    backup_file = FileField('فایل پشتیبان', validators=[
        FileRequired('لطفا یک فایل انتخاب کنید'),
        FileAllowed(['json', 'sql'], 'فقط فایل‌های JSON یا SQL پشتیبانی می‌شوند')
    ])
    clear_existing = BooleanField('پاک کردن داده‌های موجود قبل از بازیابی')
    submit = SubmitField('بازیابی پایگاه داده')
