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
                role=role
            )
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
                password=name,
                role=role
            )
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
                password='test',
                role=role
            )
        db = client.db
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
                password='test',
                role=role
            )
        db = client.db
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
