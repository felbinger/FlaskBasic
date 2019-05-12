from marshmallow import Schema, fields, validate
from flask import jsonify

from ..schemas import validate_spaces


class AuthSchema(Schema):
    username = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=200), validate_spaces]
    )
    password = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=200)]
    )
    token = fields.Str(
        validate=[validate.Length(max=6), validate_spaces],
        allow_none=True
    )


class TokenRefreshSchema(Schema):
    refreshToken = fields.Str(
        required=True
    )


class AuthResultSchema:
    __slots__ = ['message', 'errors', 'access_token', 'refresh_token', 'status_code']

    def __init__(self, message, errors=None, access_token=None, refresh_token=None, status_code=200):
        self.message = message
        self.errors = errors or []
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.status_code = status_code

    def jsonify(self):
        return jsonify({
            'message': self.message,
            'errors': self.errors,
            'accessToken': self.access_token,
            'refreshToken': self.refresh_token
        }), self.status_code
