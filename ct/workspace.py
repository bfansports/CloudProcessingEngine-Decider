from __future__ import absolute_import

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
        self.input_spec = input_spec
        self.steps = list(steps)
        self.activities = dict(activities)

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
            input_spec=None,  # FIXME
            steps=steps,
            activities=activities,
        )

        _LOGGER.debug('Loaded plan %s(steps:%d activities:%d)',
                      plan, len(steps), len(activities))

        return plan

    def __repr__(self):
        return 'Plan(name={name})'.format(name=self.name)
