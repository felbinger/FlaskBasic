from app.api import User, Role
from .utils import *


def test_unauthorized_index(app, client):
    resp = client.get('/')
    assert resp.status_code == 302


def test_login(app, client):
    with app.app_context():
        _create_user(app, client)
        resp = client.post('/login', data={'username': 'test', 'password': 'test'})
        assert resp.status_code == 302  # expect redirect to another page
        assert 'session=' in resp.headers['Set-Cookie']


# method to create the default rows in the database
def _generate_default(app, client):
    db = client.db
    with app.app_context():
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                description='Administrator'
            )
            db.session.add(admin_role)
        user_role = Role.query.filter_by(name='user').first()
        if not user_role:
            user_role = Role(
                name='user',
                description='User'
            )
            db.session.add(user_role)
        db.session.commit()


# create a non admin role
def _create_role(app, client):
    db = client.db
    with app.app_context():
        _generate_default(app, client)
        role = Role.query.filter_by(name='user').first()
        if not role:
            role = Role(
                name='user',
                description='User'
            )
            db.session.add(role)
            db.session.commit()
        return role


# create an non admin user
def _create_user(app, client):
    db = client.db
    with app.app_context():
        user = User.query.filter_by(username='max').first()
        if not user:
            user = User(
                username='test',
                password='test',
                role=_create_role(app, client)
            )
            db.session.add(user)
            db.session.commit()
        return user


# generate a session (token in a cookie) for an non admin user
def _generate_user_session(app, client):
    with app.app_context():
        _create_user(app, client)
        resp = client.post('/login', data={'username': 'test', 'password': 'test'})
        assert resp.status_code == 302  # expect redirect to another page
        assert 'session=' in resp.headers['Set-Cookie']
        session_cookie = resp.headers['Set-Cookie'].rsplit("=")[1].rsplit(";")[0]
        return str(session_cookie)
