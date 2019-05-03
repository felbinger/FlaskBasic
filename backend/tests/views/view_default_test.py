from tests.utils import Utils


def test_index_unauthorized(app, client):
    resp = client.get('/')
    assert resp.status_code == 302


def test_index_authorized(app, client):
    # utils = Utils(app, client)
    # resp = client.get('/', headers={'Set-Cookie': utils.generate_session()})
    # assert resp.status_code == 200
    pass


# TODO doesn't work
def test_login(app, client):
    # Utils(app, client)
    # resp = client.post('/login', data={'username': 'test', 'password': 'password_for_test'})
    # assert resp.status_code == 302  # expect redirect to another page
    # assert 'session=' in resp.headers['Set-Cookie']
    pass


def test_login_invalid_credentials(app, client):
    Utils(app, client)
    resp = client.post('/login', data={'username': 'invalid', 'password': 'invalid'})
    assert resp.status_code == 200
    assert 'Invalid Credentials!' in resp.data.decode('utf8')


def test_logout(app, client):
    # utils = Utils(app, client)
    # resp = client.get('/logout', headers={'Set-Cookie': utils.generate_session()})
    # assert resp.status_code == 302
    # todo implement check if session is blacklisted (set/redis)
    pass
