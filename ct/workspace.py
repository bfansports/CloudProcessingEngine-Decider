from __future__ import absolute_import

import jsonschema
import logging

from .step import Step
from .activity import Activity

_LOGGER = logging.getLogger(__name__)


class Plan(object):

    __slots__ = ('name',
                 'input_spec',
                 'steps',
                 'activities',
                 '__weakref__')

    def __init__(self, name, input_spec='', steps=(), activities=()):
        self.name = name
        self.steps = list(steps)
        self.activities = dict(activities)

        if input_spec:
            try:
                self.input_spec = jsonschema.Draft4Validator(input_spec)
            except jsonschema.SchemaError as err:
                _LOGGER.critical('Invalid JSONSchema in plan %r: %r',
                                 name, err)
                raise

        else:
            self.input_spec = None

    def check_input(self, plan_input):
        if self.input_spec is not None:
            return self.input_spec.validate(plan_input)
        else:
            # No input schema meams we accept everything
            return True

    @classmethod
    def load(cls, data):
        # FIXME: pass data through JSONSchema
        activities = {
            activity_data['name']: Activity.from_data(activity_data)
            for activity_data in data['activities']
        }

        steps = []
        for step_data in data['steps']:
            step = Step.make_step(step_data, activities)
            steps.append(step)

        plan = cls(
            name=data['name'],
            input_spec=data['input_spec'],
            steps=steps,
            activities=activities,
        )

        _LOGGER.debug('Loaded plan %s(steps:%d activities:%d)',
                      plan, len(steps), len(activities))

        return plan

    def __repr__(self):
        return 'Plan(name={name})'.format(name=self.name)
