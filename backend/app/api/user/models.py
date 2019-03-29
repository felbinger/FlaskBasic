from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
from datetime import datetime

from app.db import db


class User(db.Model):
    __table_args__ = ({'mysql_character_set': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_520_ci'})
    id = Column('id', Integer, primary_key=True)
    public_id = Column('publicId', String(36), unique=True, nullable=False)
    username = Column('username', String(64), unique=True, nullable=False)
    displayName = Column('displayName', String(128), unique=True, nullable=True)
    email = Column('email', String(64), unique=True, nullable=False)
    verified = Column('verified', Boolean, nullable=False)
    password = Column('password', String(512), nullable=False)
    created = Column('created', DateTime, nullable=False)
    last_login = Column('lastLogin', DateTime)

    role_id = Column('role', Integer, ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    def __init__(self, *args, **kwargs):
        kwargs['password'] = generate_password_hash(kwargs['password'], method='sha512')
        super().__init__(*args, **kwargs, public_id=str(uuid4()), verified=False, created=datetime.utcnow())

    def jsonify(self):
        return {
            'publicId': self.public_id,
            'username': self.username,
            'displayName': self.displayName if self.displayName else self.username,
            'email': self.email,
            'verified': self.verified,
            'created': self.created.strftime("%d.%m.%Y %H:%M:%S"),
            'lastLogin': self.last_login.strftime("%d.%m.%Y %H:%M:%S") if self.last_login else None,
            'role': self.role.jsonify()
        }

    def verify_password(self, password):
        return check_password_hash(self.password, password)
