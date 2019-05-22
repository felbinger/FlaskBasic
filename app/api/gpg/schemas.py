from marshmallow import Schema, fields, validate

from ..schemas import validate_spaces


class DaoFingerprintSchema(Schema):
    fingerprint = fields.Str(
        required=True,
        validate=[validate.Length(min=1, max=80), validate_spaces]
    )
