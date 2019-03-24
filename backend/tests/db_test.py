from app.api import User, Role
from uuid import UUID


def test_create_models(client):
    assert client.db is not None


def test_create_role(app, client):
    db = client.db
    role = Role(name='admin', description='Administrator')
    with app.app_context():
        db.session.add(role)
        db.session.commit()
        assert len(Role.query.all()) == 1


def test_create_user(app, client):
    db = client.db
    role = Role(name='admin', description='Administrator')
    user = User(
        username='test',
        password='testineTestHatEinPw',
        role=role
    )
    with app.app_context():
        db.session.add(role)
        db.session.add(user)
        db.session.commit()
        first = User.query.first()

    assert isinstance(first, User)
    assert len(UUID(first.public_id).hex) == 32
    assert first.verify_password('testineTestHatEinPw')
