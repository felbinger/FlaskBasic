from flask.views import MethodView
from flask import request, current_app
import jwt
from datetime import datetime, timedelta

from app.db import db
from app.api.user import User
from ..schemas import ResultSchema
from .utils import require_token
from .schemas import AuthSchema, AuthResultSchema


class AuthResource(MethodView):
    @require_token
    def get(self, user, **_):
        return ResultSchema(
            data=user.jsonify()
        ).jsonify()

    def post(self):
        data = request.get_json() or {}
        schema = AuthSchema()
        # use the schema to validate the submitted data
        error = schema.validate(data)
        if error:
            return AuthResultSchema(
                message='Payload is invalid',
                errors=error,
                status_code=400
            ).jsonify()

        # Get the user object by the submitted username
        user = User.query.filter_by(username=data.get('username')).first()
        # Check if the user exists, if the submitted password is correct
        if not user or not user.verify_password(data.get('password')):
            return AuthResultSchema(
                message='Wrong credentials',
                status_code=401
            ).jsonify()
        # check if the account (email address) is verified
        if not user.verified:
            return AuthResultSchema(
                message='Account not activated',
                status_code=401
            ).jsonify()
        # check if 2fa is enabled, and if so check token
        if user.is_2fa_enabled() and not user.verify_totp(data.get('token')):
            return AuthResultSchema(
                message='Wrong credentials',
                status_code=401
            ).jsonify()

        # set the last_login attribute in the user object to the current time
        user.last_login = datetime.now()
        db.session.commit()

        token_data = {
            "exp": datetime.now() + timedelta(hours=current_app.config['TOKEN_VALIDITY']),
            "username": user.username
        }
        token = jwt.encode(token_data, current_app.config["SECRET_KEY"]).decode()

        return AuthResultSchema(
            message='Authentication was successfully',
            token=token
        ).jsonify()
