from functools import wraps
from flask import session, redirect, url_for, request
import requests


def require_login(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # check if access token is in session
        if 'access_token' in session and session.get('access_token'):
            # check if access token is still valid
            resp = requests.get(
                f'{request.scheme}://{request.host}{url_for("auth_api")}',
                headers={'Authorization': f'Bearer {session.get("access_token")}'}
            )
            if resp.status_code != 200:
                # check if refresh token is in session (will be deleted on logout)
                if 'refresh_token' in session and session.get('refresh_token'):
                    # get new access token (using the refresh token)
                    resp = requests.post(
                        f'{request.scheme}://{request.host}{url_for("refresh_api")}',
                        json={'refreshToken': session.get("refresh_token")}
                    )
                    if resp.status_code != 200:
                        return redirect(url_for('app.views.auth.login'))

                    session["access_token"] = resp.json().get("accessToken")
            return view_func(*args, **kwargs)
        else:
            return redirect(url_for('app.views.auth.login'))
    return wrapper


def require_logout(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'access_token' in session and session.get('access_token') and \
                session.get('access_token').startswith('Bearer '):
            return redirect(url_for('app.views.default.index'))
        else:
            return view_func(*args, **kwargs)
    return wrapper


def require_admin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        headers = {'Authorization': f'Bearer {session.get("access_token")}'}
        resp = requests.get(
            f'{request.scheme}://{request.host}{url_for("auth_api")}',
            headers=headers
        ).json().get('data')
        if resp.get('role').get('name') == 'admin':
            return view_func(*args, **kwargs)
        else:
            return 'You\'re not allowed to request this resource!', 403
    return wrapper
