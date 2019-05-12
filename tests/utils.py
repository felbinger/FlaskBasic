from app.api import Role, User
import json
import os
import onetimepass
from base64 import b32encode


class Utils:
    def __init__(self, app, client):
        self.app = app
        self.client = client
        self.db = client.db

        with self.app.app_context():
            if not Role.query.filter_by(name="admin").first():
                admin_role = Role(
                    name="admin",
                    description="Administrator"
                )
                self.db.session.add(admin_role)
                if not User.query.filter_by(username="administrator").first():
                    admin_user = User(
                        username='administrator',
                        email='administrator@example.com',
                        verified=True,
                        password='password_for_administrator',
                        role=admin_role,
                        totp_enabled=False
                    )
                    self.db.session.add(admin_user)
            if not Role.query.filter_by(name="user").first():
                user_role = Role(
                    name="user",
                    description="User"
                )
                self.db.session.add(user_role)
                if not User.query.filter_by(username="test").first():
                    normal_user = User(
                        username='test',
                        email='test@example.com',
                        verified=True,
                        password='password_for_test',
                        role=user_role,
                        totp_enabled=False
                    )
                    self.db.session.add(normal_user)
            self.db.session.commit()

    # generate an access token with admin privileges
    def generate_admin_access_token(self, username='administrator',
                                    password='password_for_administrator', refresh=False):
        return self.generate_access_token(username=username, password=password, refresh=refresh)

    def generate_access_token(self, username='test', password='password_for_test', refresh=False):
        with self.app.app_context():
            user = User.query.filter_by(username=username).first()
            if user:
                if user.totp_enabled:
                    resp = self.client.post(
                        '/api/auth',
                        json={'username': username, 'password': password, 'token': self.generate_2fa_token()}
                    )
                else:
                    resp = self.client.post(
                        '/api/auth',
                        json={'username': username, 'password': password}
                    )
                access_token = json.loads(resp.data.decode()).get('accessToken')
                refresh_token = json.loads(resp.data.decode()).get('refreshToken')
                return (access_token, refresh_token) if refresh else access_token

    def get_public_id(self, username='test'):
        with self.app.app_context():
            return User.query.filter_by(username=username).first().public_id

    def enable_2fa(self, username='test'):
        with self.app.app_context():
            user = User.query.filter_by(username=username).first()
            user.totp_enabled = True
            user.totp_secret = b32encode(os.urandom(10)).decode('utf-8')
            self.db.session.commit()

    def generate_2fa_token(self, username='test'):
        with self.app.app_context():
            user = User.query.filter_by(username=username).first()
            if user.totp_enabled:
                return str(onetimepass.get_totp(user.totp_secret))

    def create_user(self, username='random', password='password_for_random', verified=True, role='user'):
        with self.app.app_context():
            if not User.query.filter_by(username=username).first():
                _role = Role.query.filter_by(name=role).first()
                if not _role:
                    _role = Role(
                        name=role,
                        description=role.upper()
                    )
                    self.db.session.add(_role)
                user = User(
                    username=username,
                    email=f'{username}@example.com',
                    verified=verified,
                    password=password,
                    role=_role,
                    totp_enabled=False
                )
                self.db.session.add(user)
            self.db.session.commit()

    def delete_user(self, username='test'):
        with self.app.app_context():
            user = User.query.filter_by(username=username).first()
            if user:
                self.db.session.delete(user)
                self.db.session.commit()
