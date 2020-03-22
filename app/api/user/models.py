from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, LargeBinary
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from uuid import uuid4
from datetime import datetime
import onetimepass

from app.utils import db


class User(db.Model):
    __table_args__ = ({'mysql_character_set': 'utf8mb4', 'mysql_collate': 'utf8mb4_unicode_520_ci'})
    id: int = Column('id', Integer, primary_key=True)
    public_id: str = Column('publicId', String(36), unique=True, nullable=False)
    username: str = Column('username', String(64), unique=True, nullable=False)
    displayName: str = Column('displayName', String(128), unique=True, nullable=True)
    email: str = Column('email', String(64), nullable=False)
    verified: bool = Column('verified', Boolean, nullable=False, default=False)
    _password: str = Column('password', String(512), nullable=False)
    created: datetime = Column('created', DateTime, nullable=False, default=datetime.utcnow())
    last_login: datetime = Column('lastLogin', DateTime)

    role_id: int = Column('role', Integer, ForeignKey('role.id'), nullable=False)
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    totp_enabled: bool = Column('2fa_enabled', Boolean, nullable=False, default=False)
    totp_secret: str = Column('2fa_secret', String(128), nullable=True, default=None)

    gpg_enabled: bool = Column('gpg_enabled', Boolean, nullable=False, default=False)
    gpg_fingerprint: str = Column('gpg_fingerprint', String(128), nullable=True, default=None)
    gpg_public_key: str = Column('gpg_public_key', LargeBinary, nullable=True)

    def __init__(self, *args: list, **kwargs: dict) -> "User":
        kwargs['_password']: str = generate_password_hash(kwargs['password'], method='sha512')
        super().__init__(*args, **kwargs, public_id=str(uuid4()))

    def jsonify(self) -> dict:
        return {
            'publicId': self.public_id,
            'username': self.username,
            'displayName': self.displayName if self.displayName else self.username,
            'email': self.email,
            'verified': self.verified,
            'created': self.created.isoformat(),
            'lastLogin': self.last_login.isoformat()if self.last_login else None,
            'role': self.role.jsonify(),
            '2fa': self.totp_enabled,
            'gpg': self.gpg_enabled
        }

    def verify_password(self, password: str) -> bool:
        return check_password_hash(self._password, password)

    def get_totp_uri(self) -> str:
        return f'otpauth://totp/FlaskBasic:{self.username}?secret={self.totp_secret}&issuer=FlaskBasic'

    def verify_totp(self, token: str) -> bool:
        """
        This method will return true if the totp secret is none,
        maybe 2fa has been enabled in the database without providing a totp secret by an admin
        """
        ret = True
        if self.totp_secret:
            ret = onetimepass.valid_totp(token, self.totp_secret)
        return ret

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password: str):
        self._password = generate_password_hash(password, method=current_app.config.get('HASH_METHOD'))
