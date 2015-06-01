"""Schema implementation based on JSONSchema v4 draft
"""
import logging

import jsonschema
from jsonschema import (
    SchemaError,
    ValidationError
)

_LOGGER = logging.getLogger(__name__)


class SchemaValidated(object):

    __slots__ = ('_input_validator')

    def __init__(self):
        self._input_validator = None

    def check_input(self, some_input):
        if self._input_validator is not None:
            try:
                return self._input_validator.validate(some_input)

            except jsonschema.ValidationError:
                raise

        else:
            # No input schema meams we accept everything
            return True

    def init_validator(self, specifications):
        try:
            self._input_validator = jsonschema.Draft4Validator(specifications)

        except jsonschema.SchemaError:
            raise


__all__ = [
    'SchemaError',
    'SchemaValidated',
    'ValidationError',
]
