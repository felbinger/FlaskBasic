from app.api import User, Role
from uuid import UUID


def test_create_models(client):
    assert client.db is not None


def test_create_role(app, client):
    db = client.db
    with app.app_context():
        role = Role(name='admin', description='Administrator')
        db.session.add(role)
        db.session.commit()
        assert len(Role.query.all()) == 1

        queried_role = Role.query.filter_by(name='admin').first()
        assert isinstance(queried_role, Role)
        assert queried_role.description == 'Administrator'


def test_create_user(app, client):
    db = client.db
    with app.app_context():
        role = Role(name='admin', description='Administrator')
        user = User(
            username='test',
            displayName='Testine Test',
            password='password_for_test',
            email='test@test.test',
            verified=True,
            role=role,
            totp_enabled=False
        )

        db.session.add(role)
        db.session.add(user)
        db.session.commit()
        queried_user = User.query.filter_by(username='test').first()

        assert isinstance(queried_user, User)
        assert len(UUID(queried_user.public_id).hex) == 32
        assert queried_user.displayName == 'Testine Test'
        assert queried_user.email == 'test@test.test'
        assert queried_user.verify_password('password_for_test')
