from __future__ import (
    absolute_import,
    division,
    print_function
)

import logging

from .schema import SchemaValidator

import yaql
import yaql.exceptions

_LOGGER = logging.getLogger(__name__)


class Activity(object):
    """Activity abstraction.

    Attributes:
        name (str): The name of this `Activity`.
        version (str): The version of this `Activity`.
        task_list (str): Name of the  SWF `task_list` to use when submitting
                         activity tasks.
        heartbeat_timeout (str): SWF 'heartbeat_timeout' value.
        schedule_to_close_timeout (str): SWF 'schedule_to_close_timeout' value.
        schedule_to_start_timeout (str): SWF 'schedule_to_start_timeout' value.
        start_to_close_timeout (str): SWF 'start_to_close_timeout' value.

    Examples:
        >>> a = activity.Activity.from_data(
        ...     {
        ...         'name': 'MyActivity',
        ...         'version': '1.0',
        ...         'task_list': 'TranscodeAsset',
        ...         'heartbeat_timeout: '60',
        ...         'schedule_to_close_timeout': '518400',
        ...         'schedule_to_start_timeout': '43200',
        ...         'start_to_close_timeout': '432000'
        ...     }
        ... )
        >>> a
        Activity(name='MyActivity')
        >>> a.name
        'MyActivity'

    """

    _DATA_SCHEMA = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'properties': {
            'name': {
                'type': 'string',
            },
            'version': {
                'type': 'string',
            },
            'input_spec': {
                'oneOf': [
                    {'type': 'null'},
                    {'$ref': '#/definitions/input_spec'},
                ],
            },
            'outputs_spec': {
                'oneOf': [
                    {'type': 'null'},
                    {'$ref': '#/definitions/outputs_spec'},
                ]
            },
            'task_list': {
                'type': 'string',
            },
            'heartbeat_timeout': {
                'type': 'integer',
            },
            'schedule_to_close_timeout': {
                'type': 'integer',
            },
            'schedule_to_start_timeout': {
                'type': 'integer',
            },
            'start_to_close_timeout': {
                'type': 'integer',
            },
        },
        'additionalProperties': False,
        'definitions': {
            'input_spec': {
                '$ref': 'http://json-schema.org/draft-04/schema#',
            },
            'outputs_spec': {
                'type': 'object',
                'patternProperties': {
                    '^[a-zA-Z0-9]+$': {}
                },
                'minProperties': 1,
                'additionalProperties': False,
            },
        },
    }

    __slots__ = ('name', 'version',
                 'task_list',
                 'heartbeat_timeout',
                 'schedule_to_start_timeout',
                 'schedule_to_close_timeout',
                 'start_to_close_timeout',
                 '_input_validator', '_outputs_spec')

    def __init__(self, name, version,
                 input_spec=None, outputs_spec=None,
                 task_list=None,
                 heartbeat_timeout=60,
                 schedule_to_close_timeout=518400,
                 schedule_to_start_timeout=43200,
                 start_to_close_timeout=432000):

        self.name = name
        self.version = version

        if task_list is None:
            task_list = '{name}-{version}'.format(
                name=self.name,
                version=self.version
            )
        self.task_list = task_list

        self.heartbeat_timeout = heartbeat_timeout
        self.schedule_to_close_timeout = schedule_to_close_timeout
        self.schedule_to_start_timeout = schedule_to_start_timeout
        self.start_to_close_timeout = start_to_close_timeout

        self._input_validator = SchemaValidator(input_spec)
        if outputs_spec:
            try:
                self._outputs_spec = {key: yaql.parse(expr)
                                      for key, expr in outputs_spec.items()}

            except yaql.exceptions.YaqlGrammarException as err:
                _LOGGER.critical('Invalid YAQL expression in Activity %r: %r',
                                 name, err)
                raise
        else:
            self._outputs_spec = {}

    def __repr__(self):
        return 'Activity(name={name!r})'.format(name=self.name)

    def render_outputs(self, output):
        """Use the `Activity`'s `outputs_spec` to generate all the defined
        representation of this activity's output.
        """
        return {
            key: expr.evaluate(output)
            for key, expr in self._outputs_spec.items()
        }

    def check_input(self, activity_input):
        return self._input_validator.validate(activity_input)

    @classmethod
    def from_data(cls, data):
        """Define an `Activity` from a dictionary of attributes.
        """
        validator = SchemaValidator(cls._DATA_SCHEMA)
        validator.validate(data)

        activity_data = {
            'name': data['name'],
            'version': data['version'],
            'input_spec': data.get('input_spec', None),
            'outputs_spec': data.get('outputs_spec', None),
            'task_list': data.get('task_list', None),
        }

        # Copy in all SWF activity options.
        for option in ('heartbeat_timeout', 'schedule_to_close_timeout',
                       'schedule_to_start_timeout', 'start_to_close_timeout'):
            if option in data:
                activity_data[option] = data[option]

        return cls(**activity_data)
