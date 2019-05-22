from flask.views import MethodView
from flask import request, current_app
from marshmallow.exceptions import ValidationError
from io import BytesIO
import pyqrcode

from app.utils import db
from ..schemas import ResultSchema, ResultErrorSchema
from ..authentication import require_token
from .schemas import DaoTokenSchema


class TOTPResource(MethodView):
    @require_token
    def get(self, user):
        if user.totp_secret and not user.totp_enabled:
            db.session.commit()
            url = pyqrcode.create(user.get_totp_uri())
            stream = BytesIO()
            url.svg(stream, scale=current_app.config['QR_SCALE'])
            return stream.getvalue(), 200, {
                'Content-Type': 'image/svg+xml',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        return ResultErrorSchema(message='Unable to generate QR Code').jsonify()

    @require_token
    def post(self, user):
        """
        Activate 2FA with a valid token
        """
        schema = DaoTokenSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        if not user.totp_secret:
            return ResultErrorSchema(
                message='2fa is not setted up',
                status_code=400
            ).jsonify()
        if user.verify_totp(data['token']):
            user.totp_enabled = True
            db.session.commit()
            return ResultErrorSchema(
                message='2fa has been enabled',
                status_code=200
            ).jsonify()
        else:
            return ResultErrorSchema(
                message='invalid token, try again',
                status_code=400
            ).jsonify()

    @require_token
    def delete(self, user):
        """
        reset 2fa secret key if it's not enabled, just prepared for setup
        """
        if user.totp_enabled and user.totp_secret:
            return ResultErrorSchema(
                message='2fa is not in setup state, this can\'t be aborted!'
            ).jsonify()

        user.totp_secret = None
        db.session.commit()
        return ResultSchema(
            data='2fa secret has been disabled'
        ).jsonify()
