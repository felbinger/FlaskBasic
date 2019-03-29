from .utils import create_dummy_user, generate_user_session


def test_login(app, client):
    create_dummy_user(app, client, name='max')
    resp = client.post('/login', data={'username': 'max', 'password': 'max'})
    assert resp.status_code == 302  # expect redirect to another page
    assert 'session=' in resp.headers['Set-Cookie']


def test_logout(app, client):
    resp = client.get('/logout', headers={'Set-Cookie': generate_user_session(app, client)})
    assert resp.status_code == 302
    # todo implement check if session is blacklisted (redis) - this feature haven't been implemented yet
