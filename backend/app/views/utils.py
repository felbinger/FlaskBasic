from functools import wraps
from flask import session, redirect, url_for, request
import requests


def require_login(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        # check if access token exist
        if session.get('Access-Token'):
            # check if access token is still valid
            resp = requests.get(
                f'{request.scheme}://{request.host}{url_for("auth_api")}',
                headers={'Access-Token': session.get('Access-Token')}
            )
            if resp.status_code != 200:
                # invalid token
                return redirect(url_for('app.views.auth.login'))
            else:
                # token is valid
                return view_func(*args, **kwargs)
        else:
            return redirect(url_for('app.views.auth.login'))
    return wrapper


def require_logout(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if session.get('Access-Token'):
            return redirect(url_for('app.views.default.index'))
        else:
            return view_func(*args, **kwargs)
    return wrapper


def require_admin(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        headers = {'Access-Token': session.get('Access-Token')}
        resp = requests.get(
            f'{request.scheme}://{request.host}{url_for("auth_api")}',
            headers=headers
        ).json().get('data')
        if resp.get('role').get('name') == 'admin':
            return view_func(*args, **kwargs)
        else:
            return 'You\'re not allowed to request this resource!', 403
    return wrapper
