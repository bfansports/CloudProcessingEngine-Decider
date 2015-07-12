"""Schema implementation based on JSONSchema v4 draft
"""

from __future__ import absolute_import


import logging

import jsonschema
from jsonschema import (
    SchemaError,
    ValidationError
)

_LOGGER = logging.getLogger(__name__)


class SchemaValidator(object):

    __slots__ = ('_input_validator')

    def __init__(self, input_spec):
        if input_spec:
            try:
                self._input_validator = jsonschema.Draft4Validator(input_spec)

            except jsonschema.SchemaError:
                raise

        else:
            self._input_validator = None

    def validate(self, some_input):
        if self._input_validator is not None:
            try:
                return self._input_validator.validate(some_input)

            except jsonschema.ValidationError:
                raise

        else:
            # No input schema meams we accept everything
            return True


__all__ = [
    'SchemaError',
    'SchemaValidator',
    'ValidationError',
]
