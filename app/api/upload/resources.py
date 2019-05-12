import os
from flask.views import MethodView
from flask import request, url_for, current_app
from base64 import decodebytes
from marshmallow.exceptions import ValidationError

from ..schemas import ResultSchema, ResultErrorSchema
from ..authentication import require_token
from .schemas import DaoUploadSchema


class UploadResource(MethodView):
    @require_token
    def get(self, uuid, user):
        path = f'/static/img/profile/{user.public_id if uuid == "me" else uuid}.png'
        if not os.path.isfile(f'{current_app.root_path}{path}'):
            return ResultSchema(
                data=f'{request.scheme}://{request.host}/static/img/profile/blank.png'
            ).jsonify()
        return ResultSchema(
            data=f'{request.scheme}://{request.host}{path}'
        ).jsonify()

    @require_token
    def post(self, user):
        schema = DaoUploadSchema()
        data = request.get_json() or {}
        try:
            data = schema.load(data)
        except ValidationError as errors:
            return ResultErrorSchema(
                message='Payload is invalid',
                errors=errors.messages,
                status_code=400
            ).jsonify()

        path = os.path.join(f'/static/img/profile/{user.public_id}.png')

        splitted = data.get('file').split(",")
        if len(splitted) != 2:
            return ResultErrorSchema(
                message='Profile picture is invalid'
            ).jsonify()

        with open(f'{current_app.root_path}{path}', 'wb') as f:
            f.write(decodebytes(splitted[1].encode()))

        return ResultSchema(
            data=f'{request.scheme}://{request.host}{path}',
            status_code=201
        ).jsonify()
