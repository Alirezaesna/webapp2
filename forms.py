from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField, DateField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if user is not None:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.get_by_email(email.data)
        if user is not None:
            raise ValidationError('Email already registered. Please use a different one.')

class EditProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Change Password')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    is_admin = BooleanField('Admin User')
    submit = SubmitField('Save User')

class LoanApplicationForm(FlaskForm):
    amount = FloatField('Loan Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    duration = IntegerField('Duration (months)', validators=[DataRequired(), NumberRange(min=1, max=120)])
    purpose = TextAreaField('Purpose of Loan', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Apply for Loan')

class LoanForm(FlaskForm):
    user_id = SelectField('User', coerce=str, validators=[DataRequired()])
    amount = FloatField('Loan Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    duration = IntegerField('Duration (months)', validators=[DataRequired(), NumberRange(min=1, max=120)])
    purpose = TextAreaField('Purpose of Loan', validators=[DataRequired(), Length(min=10)])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Loan')

class InstallmentForm(FlaskForm):
    loan_id = SelectField('Loan', coerce=str, validators=[DataRequired()])
    amount = FloatField('Installment Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    paid = BooleanField('Paid')
    paid_date = DateField('Payment Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Save Installment')

class LoanActionForm(FlaskForm):
    loan_id = HiddenField('Loan ID', validators=[DataRequired()])
    action = HiddenField('Action', validators=[DataRequired()])
    submit = SubmitField('Confirm')

class InstallmentPaymentForm(FlaskForm):
    installment_id = HiddenField('Installment ID', validators=[DataRequired()])
    submit = SubmitField('Mark as Paid')

class InstallmentFilterForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('all', 'All Installments'),
        ('paid', 'Paid Installments'),
        ('unpaid', 'Unpaid Installments'),
        ('overdue', 'Overdue Installments')
    ])
    submit = SubmitField('Filter')
