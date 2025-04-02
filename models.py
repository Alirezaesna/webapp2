from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    loans = db.relationship('Loan', 
                           foreign_keys='Loan.user_id', 
                           backref='user', 
                           lazy='dynamic', 
                           cascade="all, delete-orphan")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @classmethod
    def get_all(cls):
        return cls.query.all()
    
    @classmethod
    def get_by_id(cls, user_id):
        return cls.query.get(user_id)
    
    @classmethod
    def get_by_username(cls, username):
        return cls.query.filter_by(username=username).first()
    
    @classmethod
    def get_by_email(cls, email):
        return cls.query.filter_by(email=email).first()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def delete(cls, user_id):
        user = cls.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()


class Loan(db.Model):
    __tablename__ = 'loans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in months
    purpose = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected, completed
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # Relationships
    installments = db.relationship('Installment', backref='loan', lazy='dynamic', cascade="all, delete-orphan")
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_loans', lazy=True)
    
    @classmethod
    def get_all(cls):
        return cls.query.all()
    
    @classmethod
    def get_by_id(cls, loan_id):
        return cls.query.get(loan_id)
    
    @classmethod
    def get_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def delete(cls, loan_id):
        loan = cls.query.get(loan_id)
        if loan:
            db.session.delete(loan)
            db.session.commit()


class Installment(db.Model):
    __tablename__ = 'installments'
    
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey('loans.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    @classmethod
    def get_all(cls):
        return cls.query.all()
    
    @classmethod
    def get_by_id(cls, installment_id):
        return cls.query.get(installment_id)
    
    @classmethod
    def get_by_loan(cls, loan_id):
        return cls.query.filter_by(loan_id=loan_id).all()
    
    def save(self):
        db.session.add(self)
        db.session.commit()
    
    @classmethod
    def delete(cls, installment_id):
        # Make sure installment_id is treated as int
        try:
            installment_id = int(installment_id)
        except (ValueError, TypeError):
            print(f"Error: Could not convert installment_id to int: {installment_id}")
            return False
            
        print(f"Looking for installment with ID: {installment_id}")
        installment = cls.query.get(installment_id)
        
        if installment:
            print(f"Found installment: {installment.id}, deleting...")
            db.session.delete(installment)
            db.session.commit()
            return True
        else:
            print(f"No installment found with ID: {installment_id}")
            return False
    
    @classmethod
    def delete_by_loan(cls, loan_id):
        cls.query.filter_by(loan_id=loan_id).delete()
        db.session.commit()
