from flask import request, current_app
import jwt
from typing import Union
from ..user import User
from ..schemas import ResultErrorSchema


def require_token(view_func: callable) -> callable:
    def wrapper(*args: list, **kwargs: dict) -> Union[ResultErrorSchema, callable]:
        access_token = request.headers.get('Authorization')
        if not access_token or not access_token.startswith("Bearer "):
            return ResultErrorSchema(
                message='Missing access token',
                status_code=401
            ).jsonify()
        try:
            access_token = access_token.split(" ")[1]
            token = jwt.decode(access_token, current_app.config['SECRET_KEY'], algorithms='HS256')
            user = User.query.filter_by(username=token.get('username')).first()
            return view_func(*args, **kwargs, user=user)
        except (jwt.exceptions.DecodeError, jwt.ExpiredSignatureError, jwt.exceptions.InvalidSignatureError):
            return ResultErrorSchema(
                message='Invalid access token',
                status_code=401
            ).jsonify()
    return wrapper


def require_admin(view_func: callable) -> callable:
    def wrapper(*args: list, **kwargs: dict) -> Union[ResultErrorSchema, callable]:
        user = kwargs.get('user')
        if not user:
            raise AttributeError('Missing user attribute, please use @require_token before!')
        # check if the user has the role admin
        if user.role.name != 'admin':
            return ResultErrorSchema(message='Access Denied!', status_code=403).jsonify()
        return view_func(*args, **kwargs)
    return wrapper
