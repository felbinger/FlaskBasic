from .utils import create_dummy_user


def test_unauthorized_index(app, client):
    resp = client.get('/')
    assert resp.status_code == 302


def test_login(app, client):
    create_dummy_user(app, client, name='max')
    resp = client.post('/login', data={'username': 'max', 'password': 'max'})
    assert resp.status_code == 302  # expect redirect to another page
    assert 'session=' in resp.headers['Set-Cookie']
