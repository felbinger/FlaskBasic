from app.api import Role, User
import json


# method to add default roles to database
def generate_default(app, client):
    db = client.db
    with app.app_context():
        if len(Role.query.all()) < 2:
            if not Role.query.filter_by(name="admin").first():
                admin = Role(
                    name="admin",
                    description="Administrator"
                )
                db.session.add(admin)
            if not Role.query.filter_by(name="user").first():
                user = Role(
                    name="user",
                    description="User"
                )
                db.session.add(user)
            db.session.commit()


# method to create dummy user with role admin
def create_dummy_admin(app, client, name='test'):
    db = client.db
    with app.app_context():
        generate_default(app, client)
        role = Role.query.filter_by(name="admin").first()
        if not role:
            role = Role(name='admin', description='Administrator')
        user = User.query.filter_by(username=name).first()
        if not user:
            user = User(
                username=name,
                password=name,
                email=f'{name}@{name}.com',
                role=role
            )
        user.verified = True
        db.session.add(role)
        db.session.add(user)
        db.session.commit()
        return user.public_id


# method to create dummy user with role admin
def create_dummy_user(app, client, name='test'):
    db = client.db
    with app.app_context():
        generate_default(app, client)
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name='user', description='User')
        user = User.query.filter_by(username=name).first()
        if not user:
            user = User(
                username=name,
                email=f'{name}@{name}.com',
                password=name,
                role=role
            )
        user.verified = True
        db.session.add(role)
        db.session.add(user)
        db.session.commit()
        return user.public_id


# method to get admin access-token
def get_admin_token(app, client):
    with app.app_context():
        generate_default(app, client)
        role = Role.query.filter_by(name="admin").first()
        if not role:
            role = Role(name='admin', description='Administrator')
        user = User.query.filter_by(username='test').first()
        if not user:
            user = User(
                username='test',
                email='test@test.de',
                password='test',
                role=role
            )
        db = client.db
        user.verified = True
        db.session.add(role)
        db.session.add(user)
        db.session.commit()
    resp = client.post('/api/auth', json={'username': 'test', 'password': 'test'})
    data = json.loads(resp.data.decode())
    return data.get('token')


# method to get admin access-token
def get_user_token(app, client):
    with app.app_context():
        generate_default(app, client)
        role = Role.query.filter_by(name="user").first()
        if not role:
            role = Role(name='user', description='User')
        user = User.query.filter_by(username='test').first()
        if not user:
            user = User(
                username='test',
                email='test@test.com',
                password='test',
                role=role
            )
        db = client.db
        user.verified = True
        db.session.add(role)
        db.session.add(user)
        db.session.commit()
    resp = client.post('/api/auth', json={'username': 'test', 'password': 'test'})
    data = json.loads(resp.data.decode())
    return data.get('token')


def create_dummy_role(app, client, name):
    role = Role(name=name, description='test')
    db = client.db
    with app.app_context():
        db.session.add(role)
        db.session.commit()
    return role


# generate a session (token in a cookie) for an non admin user
def generate_user_session(app, client):
    with app.app_context():
        create_dummy_user(app, client)
        resp = client.post('/login', data={'username': 'test', 'password': 'test'})
        assert resp.status_code == 302  # expect redirect to another page
        assert 'session=' in resp.headers['Set-Cookie']
        session_cookie = resp.headers['Set-Cookie'].rsplit("=")[1].rsplit(";")[0]
        return str(session_cookie)

