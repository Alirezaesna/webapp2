import json
import os
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin):
    def __init__(self, id=None, username=None, email=None, password=None, first_name=None, 
                 last_name=None, phone=None, address=None, is_admin=False, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.address = address
        self.is_admin = is_admin
        self.created_at = created_at or datetime.now().isoformat()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'address': self.address,
            'is_admin': self.is_admin,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password_hash'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            phone=data.get('phone'),
            address=data.get('address'),
            is_admin=data.get('is_admin', False),
            created_at=data.get('created_at')
        )

    @classmethod
    def get_all(cls):
        users = []
        try:
            with open('data/users.json', 'r') as f:
                users_data = json.load(f)
                for user_data in users_data:
                    users.append(cls.from_dict(user_data))
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty list if file doesn't exist or is invalid
            pass
        return users
    
    @classmethod
    def get_by_id(cls, user_id):
        users = cls.get_all()
        for user in users:
            if str(user.id) == str(user_id):
                return user
        return None
    
    @classmethod
    def get_by_username(cls, username):
        users = cls.get_all()
        for user in users:
            if user.username == username:
                return user
        return None
    
    @classmethod
    def get_by_email(cls, email):
        users = cls.get_all()
        for user in users:
            if user.email == email:
                return user
        return None
    
    def save(self):
        users = self.get_all()
        
        # If this is a new user, generate a new ID
        if self.id is None:
            max_id = 0
            for user in users:
                if user.id and int(user.id) > max_id:
                    max_id = int(user.id)
            self.id = str(max_id + 1)
            users.append(self)
        else:
            # Update existing user
            for i, user in enumerate(users):
                if str(user.id) == str(self.id):
                    users[i] = self
                    break
        
        # Save to file
        with open('data/users.json', 'w') as f:
            json.dump([user.to_dict() for user in users], f, indent=4)
    
    @classmethod
    def delete(cls, user_id):
        users = cls.get_all()
        users = [user for user in users if str(user.id) != str(user_id)]
        
        # Save to file
        with open('data/users.json', 'w') as f:
            json.dump([user.to_dict() for user in users], f, indent=4)


class Loan:
    def __init__(self, id=None, user_id=None, amount=None, duration=None, purpose=None, 
                 status="pending", approved_by=None, approved_at=None, created_at=None):
        self.id = id
        self.user_id = user_id
        self.amount = amount
        self.duration = duration  # in months
        self.purpose = purpose
        self.status = status  # pending, approved, rejected, completed
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'duration': self.duration,
            'purpose': self.purpose,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id'),
            amount=data.get('amount'),
            duration=data.get('duration'),
            purpose=data.get('purpose'),
            status=data.get('status', 'pending'),
            approved_by=data.get('approved_by'),
            approved_at=data.get('approved_at'),
            created_at=data.get('created_at')
        )

    @classmethod
    def get_all(cls):
        loans = []
        try:
            with open('data/loans.json', 'r') as f:
                loans_data = json.load(f)
                for loan_data in loans_data:
                    loans.append(cls.from_dict(loan_data))
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty list if file doesn't exist or is invalid
            pass
        return loans
    
    @classmethod
    def get_by_id(cls, loan_id):
        loans = cls.get_all()
        for loan in loans:
            if str(loan.id) == str(loan_id):
                return loan
        return None
    
    @classmethod
    def get_by_user(cls, user_id):
        loans = cls.get_all()
        user_loans = [loan for loan in loans if str(loan.user_id) == str(user_id)]
        return user_loans
    
    def save(self):
        loans = self.get_all()
        
        # If this is a new loan, generate a new ID
        if self.id is None:
            max_id = 0
            for loan in loans:
                if loan.id and int(loan.id) > max_id:
                    max_id = int(loan.id)
            self.id = str(max_id + 1)
            loans.append(self)
        else:
            # Update existing loan
            for i, loan in enumerate(loans):
                if str(loan.id) == str(self.id):
                    loans[i] = self
                    break
        
        # Save to file
        with open('data/loans.json', 'w') as f:
            json.dump([loan.to_dict() for loan in loans], f, indent=4)
    
    @classmethod
    def delete(cls, loan_id):
        loans = cls.get_all()
        loans = [loan for loan in loans if str(loan.id) != str(loan_id)]
        
        # Save to file
        with open('data/loans.json', 'w') as f:
            json.dump([loan.to_dict() for loan in loans], f, indent=4)


class Installment:
    def __init__(self, id=None, loan_id=None, amount=None, due_date=None, 
                 paid=False, paid_date=None, created_at=None):
        self.id = id
        self.loan_id = loan_id
        self.amount = amount
        self.due_date = due_date
        self.paid = paid
        self.paid_date = paid_date
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'loan_id': self.loan_id,
            'amount': self.amount,
            'due_date': self.due_date,
            'paid': self.paid,
            'paid_date': self.paid_date,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get('id'),
            loan_id=data.get('loan_id'),
            amount=data.get('amount'),
            due_date=data.get('due_date'),
            paid=data.get('paid', False),
            paid_date=data.get('paid_date'),
            created_at=data.get('created_at')
        )

    @classmethod
    def get_all(cls):
        installments = []
        try:
            with open('data/installments.json', 'r') as f:
                installments_data = json.load(f)
                for installment_data in installments_data:
                    installments.append(cls.from_dict(installment_data))
        except (FileNotFoundError, json.JSONDecodeError):
            # Return empty list if file doesn't exist or is invalid
            pass
        return installments
    
    @classmethod
    def get_by_id(cls, installment_id):
        installments = cls.get_all()
        for installment in installments:
            if str(installment.id) == str(installment_id):
                return installment
        return None
    
    @classmethod
    def get_by_loan(cls, loan_id):
        installments = cls.get_all()
        loan_installments = [inst for inst in installments if str(inst.loan_id) == str(loan_id)]
        return loan_installments
    
    def save(self):
        installments = self.get_all()
        
        # If this is a new installment, generate a new ID
        if self.id is None:
            max_id = 0
            for installment in installments:
                if installment.id and int(installment.id) > max_id:
                    max_id = int(installment.id)
            self.id = str(max_id + 1)
            installments.append(self)
        else:
            # Update existing installment
            for i, installment in enumerate(installments):
                if str(installment.id) == str(self.id):
                    installments[i] = self
                    break
        
        # Save to file
        with open('data/installments.json', 'w') as f:
            json.dump([installment.to_dict() for installment in installments], f, indent=4)
    
    @classmethod
    def delete(cls, installment_id):
        installments = cls.get_all()
        installments = [inst for inst in installments if str(inst.id) != str(installment_id)]
        
        # Save to file
        with open('data/installments.json', 'w') as f:
            json.dump([installment.to_dict() for installment in installments], f, indent=4)
    
    @classmethod
    def delete_by_loan(cls, loan_id):
        installments = cls.get_all()
        installments = [inst for inst in installments if str(inst.loan_id) != str(loan_id)]
        
        # Save to file
        with open('data/installments.json', 'w') as f:
            json.dump([installment.to_dict() for installment in installments], f, indent=4)
