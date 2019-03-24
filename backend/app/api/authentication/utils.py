from flask import request, current_app
import jwt

from ..user import User
from ..schemas import ResultErrorSchema


def require_token(view_func):
    def wrapper(*args, **kwargs):
        access_token = request.headers.get('Access-Token')
        if not access_token:
            return ResultErrorSchema(
                message='Missing Access-Token',
                status_code=401
            ).jsonify()
        try:
            token = jwt.decode(access_token, current_app.config['SECRET_KEY'])
            user = User.query.filter_by(username=token.get('username')).first()
            return view_func(*args, **kwargs, user=user)
        except (jwt.exceptions.DecodeError, jwt.ExpiredSignatureError, jwt.exceptions.InvalidSignatureError):
            return ResultErrorSchema(
                message='Invalid Access-Token',
                status_code=401
            ).jsonify()
    return wrapper


def require_admin(view_func):
    def wrapper(*args, **kwargs):
        user = kwargs.get('user')
        if not user:
            raise AttributeError('Missing user attribute, please use @require_token before!')
        # check if the user has the role admin
        if user.role.name != 'admin':
            return ResultErrorSchema(message='Access Denied!', status_code=403).jsonify()
        return view_func(*args, **kwargs)
    return wrapper
