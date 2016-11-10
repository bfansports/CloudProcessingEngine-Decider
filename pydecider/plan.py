from __future__ import (
    absolute_import,
    division,
    print_function
)

import logging

from .step import Step
from .activity import Activity
from .schema import SchemaValidator

_LOGGER = logging.getLogger(__name__)


class Plan(object):
    """Workflow plan.
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
            'default_execution_start_to_close_timeout': {
                'type': 'string',
            },
            'default_task_start_to_close_timeout': {
                'type': 'string',
            },
            'input_spec': {
                'oneOf': [
                    {'type': 'null'},
                    {'$ref': '#/definitions/input_spec'},
                ],
            },
            'activities': {
                'type': 'array',
                'minItem': 1,
                'items': {
                    'type': 'object'
                }
            },
            'steps': {
                'type': 'array',
                'minItem': 1,
                'items': {
                    'type': 'object'
                }
            }
        },
        'additionalProperties': False,
        'definitions': {
            'input_spec': {
                '$ref': 'http://json-schema.org/draft-04/schema#',
            },
        },
    }

    __slots__ = ('name',
                 'version',
                 'default_execution_start_to_close_timeout',
                 'default_task_start_to_close_timeout',
                 'steps',
                 'activities',
                 '_input_validator',
                 '__weakref__')

    def __init__(self, name, version,
                 default_execution_start_to_close_timeout,
                 default_task_start_to_close_timeout,
                 input_spec=None, steps=(), activities=()):
        
        self.name = name
        self.version = version
        self.default_execution_start_to_close_timeout = default_execution_start_to_close_timeout
        self.default_task_start_to_close_timeout = default_task_start_to_close_timeout
        self.steps = list(steps)
        self.activities = dict(activities)
        self._input_validator = SchemaValidator(input_spec=input_spec)

    def check_input(self, plan_input):
        return self._input_validator.validate(plan_input)

    @classmethod
    def from_data(cls, plan_data):
        """Define a plan from a dictionary of attributes.
        """
        validator = SchemaValidator(cls._DATA_SCHEMA)
        validator.validate(plan_data)
        
        activities = {
            activity_data['name']: Activity.from_data(activity_data)
            for activity_data in plan_data['activities']
        }

        steps = []
        for step_data in plan_data['steps']:
            step = Step.from_data(step_data, activities)
            steps.append(step)

        plan = cls(
            name=plan_data['name'],
            version=plan_data['version'],
            default_execution_start_to_close_timeout=plan_data['default_execution_start_to_close_timeout'],
            default_task_start_to_close_timeout=plan_data['default_task_start_to_close_timeout'],
            input_spec=plan_data.get('input_spec', None),
            steps=steps,
            activities=activities,
        )

        _LOGGER.info('Loaded plan %s(steps:%d activities:%d)',
                      plan, len(steps), len(activities))

        return plan

    def __repr__(self):
        return 'Plan(name={name})'.format(name=self.name)
