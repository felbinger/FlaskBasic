from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from uuid import uuid4
from datetime import datetime
import onetimepass

from app.db import db


class User(db.Model):
    __table_args__ = ({'mysql_character_set': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_520_ci'})
    id = Column('id', Integer, primary_key=True)
    public_id = Column('publicId', String(36), unique=True, nullable=False)
    username = Column('username', String(64), unique=True, nullable=False)
    displayName = Column('displayName', String(128), unique=True, nullable=True)
    email = Column('email', String(64), unique=True, nullable=False)
    verified = Column('verified', Boolean, nullable=False, default=False)
    _password = Column('password', String(512), nullable=False)
    created = Column('created', DateTime, nullable=False, default=datetime.utcnow())
    last_login = Column('lastLogin', DateTime)

    role_id = Column('role', Integer, ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    totp_enabled = Column('2fa_enabled', Boolean, nullable=False, default=False)
    totp_secret = Column('2fa_secret', String(128), nullable=True, default=None)
    code_viewed = Column('2fa_qr_viewed', Boolean, nullable=False, default=False)

    def __init__(self, *args, **kwargs):
        kwargs['_password'] = generate_password_hash(kwargs['password'], method='sha512')
        super().__init__(*args, **kwargs, public_id=str(uuid4()))

    def jsonify(self):
        return {
            'publicId': self.public_id,
            'username': self.username,
            'displayName': self.displayName if self.displayName else self.username,
            'email': self.email,
            'verified': self.verified,
            'created': self.created.isoformat(),
            'lastLogin': self.last_login.isoformat()if self.last_login else None,
            'role': self.role.jsonify(),
            '2fa': self.totp_enabled
        }

    def verify_password(self, password):
        return check_password_hash(self._password, password)

    def get_totp_uri(self):
        return f'otpauth://totp/FlaskBasic:{self.username}?secret={self.totp_secret}&issuer=FlaskBasic'

    def verify_totp(self, token):
        return onetimepass.valid_totp(token, self.totp_secret)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self._password = generate_password_hash(password, method=current_app.config.get('HASH_METHOD'))

    """
    @property
    def totp_secret(self):
        raise AttributeError('totp_secret is not a readable attribute')

    @totp_secret.setter
    def totp_secret(self, secret):
        self._totp_secret = secret
    """
