from flask import jsonify
from marshmallow import ValidationError
from typing import Union


def validate_spaces(text: str):
    if ' ' in text:
        raise ValidationError("Text shouldn't contain any space")


class ResultErrorSchema:
    __slots__ = ['message', 'errors', 'data', 'status_code']

    def __init__(self, message, errors=None, status_code=400):
        self.message = message
        self.errors = errors
        self.status_code = status_code

    def jsonify(self):
        if self.errors:
            ret = {
                'errors': self.errors,
                'message': self.message
            }
        else:
            ret = {
                'message': self.message
            }
        return jsonify(ret), self.status_code


class ResultSchema:
    __slots__ = ['data', 'status_code']

    def __init__(self, data: Union[str, list, dict] = None, status_code: int = 200):
        self.data = data
        self.status_code = status_code

    def jsonify(self):
        return jsonify({
            'data': self.data
        }), self.status_code
