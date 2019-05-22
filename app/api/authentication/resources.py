from flask.views import MethodView
from flask import request, current_app
import jwt
from datetime import datetime, timedelta
from marshmallow.exceptions import ValidationError

from app.utils import db
from app.api.user import User
from ..schemas import ResultSchema, ResultErrorSchema
from .utils import require_token
from .schemas import AuthSchema, AuthResultSchema, TokenRefreshSchema


class AuthResource(MethodView):
    @require_token
    def get(self, user, **_):
        return ResultSchema(
            data=user.jsonify()
        ).jsonify()

    def post(self):
        """
        Login using username, password (and 2fa token)
        """
        schema = AuthSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return AuthResultSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        # Get the user object by the submitted username
        user = User.query.filter_by(username=data.get('username')).first()
        # Check if the user exists, if the submitted password is correct
        if not user or not user.verify_password(data.get('password')):
            return AuthResultSchema(
                message='Invalid credentials',
                status_code=401
            ).jsonify()
        # check if the account (email address) is verified
        if not user.verified:
            return AuthResultSchema(
                message='Account not activated',
                status_code=401
            ).jsonify()
        # check if 2fa is enabled
        if user.totp_enabled:
            # check if token is in data
            if 'token' in data:
                # check if submitted 2fa token is valid
                if not user.verify_totp(data.get('token')):
                    # @Security: (read next note first): this message could be exchanged through 2fa token invalid
                    return AuthResultSchema(
                        message='Invalid credentials',
                        status_code=401
                    ).jsonify()
            else:
                # @Security: Could an attacker use this error message to validate username and password
                return AuthResultSchema(
                    message='Missing 2fa token',
                    status_code=401
                ).jsonify()

        # set the last_login attribute in the user object to the current time
        user.last_login = datetime.now()
        db.session.commit()

        access_token_data = {
            "exp": datetime.utcnow() + timedelta(minutes=current_app.config['ACCESS_TOKEN_VALIDITY']),
            "username": user.username
        }

        access_token = jwt.encode(access_token_data, current_app.config["SECRET_KEY"]).decode()

        refresh_token_data = {
            "exp": datetime.utcnow() + timedelta(minutes=current_app.config['REFRESH_TOKEN_VALIDITY']),
            "username": user.username
        }

        refresh_token = jwt.encode(refresh_token_data, current_app.config["SECRET_KEY"]).decode()

        return AuthResultSchema(
            message='Authentication was successfully',
            access_token=access_token,
            refresh_token=refresh_token
        ).jsonify()


class RefreshResource(MethodView):
    def post(self):
        """
        Generate a new access token, using a - not blacklisted - refresh token
        """
        schema = TokenRefreshSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return AuthResultSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        try:
            refresh_token = data['refreshToken']

            # check if refresh token has been blacklisted
            if current_app.config.get('BLACKLIST').check(refresh_token):
                return ResultSchema(
                    data='Invalid refresh token',
                    status_code=401
                ).jsonify()

            refresh_token_data = jwt.decode(refresh_token, current_app.config['SECRET_KEY'], algorithms='HS256')

            # check if the user still exists (could have been delete in the meantime)
            if not User.query.filter_by(username=refresh_token_data.get('username')).first():
                return ResultErrorSchema(
                    message='User does not exist!'
                ).jsonify()

            # generate new access token
            access_token_data = {
                "exp": datetime.now() + timedelta(minutes=current_app.config['ACCESS_TOKEN_VALIDITY']),
                "username": refresh_token_data['username']
            }
            new_access_token = jwt.encode(access_token_data, current_app.config["SECRET_KEY"]).decode()

            return AuthResultSchema(
                message='Token refresh was successful',
                access_token=new_access_token
            ).jsonify()
        except (jwt.exceptions.DecodeError, jwt.ExpiredSignatureError, jwt.exceptions.InvalidSignatureError):
            return ResultErrorSchema(
                message='Invalid refresh token',
                status_code=401
            ).jsonify()

    def delete(self, token):
        """
        Add a refresh token to the blacklist
        """
        blacklist = current_app.config.get('BLACKLIST')
        if not blacklist.check(token):
            try:
                # check if the token is valid (could be a way to spam the blacklist)
                jwt.decode(token, current_app.config['SECRET_KEY'], algorithms='HS256')
                blacklist.add(token)
                return ResultSchema(
                    data='Successfully blacklisted token',
                    status_code=200
                ).jsonify()
            except (jwt.exceptions.DecodeError, jwt.ExpiredSignatureError, jwt.exceptions.InvalidSignatureError):
                return ResultErrorSchema(
                    message='Invalid refresh token',
                    status_code=401
                ).jsonify()
        else:
            return ResultErrorSchema(
                message='Invalid refresh token',
                status_code=401
            ).jsonify()
