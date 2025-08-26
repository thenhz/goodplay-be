from datetime import datetime, timezone
from bson import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

class User:
    def __init__(self, email, password_hash=None, first_name=None, last_name=None, 
                 is_active=True, role='user', _id=None, created_at=None, updated_at=None):
        self._id = _id
        self.email = email.lower()
        self.first_name = first_name
        self.last_name = last_name
        self.password_hash = password_hash
        self.is_active = is_active
        self.role = role
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.updated_at = datetime.now(timezone.utc)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        user_dict = {
            '_id': str(self._id) if self._id else None,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'role': self.role,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
        if include_sensitive:
            user_dict['password_hash'] = self.password_hash
        
        return {k: v for k, v in user_dict.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data, include_sensitive=False):
        if not data:
            return None
            
        return cls(
            _id=data.get('_id'),
            email=data.get('email'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            is_active=data.get('is_active', True),
            role=data.get('role', 'user'),
            created_at=data.get('created_at'),
            updated_at=data.get('updated_at'),
            password_hash=data.get('password_hash') if include_sensitive else None
        )
    
    def get_id(self):
        return str(self._id) if self._id else None
    
    def __repr__(self):
        return f'<User {self.email}>'