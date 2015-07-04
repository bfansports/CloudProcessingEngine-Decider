from __future__ import absolute_import

import logging

from .step import Step
from .activity import Activity
from .schema import SchemaValidated

_LOGGER = logging.getLogger(__name__)


class Plan(SchemaValidated):
    """Workflow plan.
    """

    __slots__ = ('name',
                 'version',
                 'steps',
                 'activities',
                 '__weakref__')

    def __init__(self, name, version,
                 input_spec=None, steps=(), activities=()):
        self.name = name
        self.version = version
        self.steps = list(steps)
        self.activities = dict(activities)

        if input_spec:
            self.init_validator(input_spec)

    @classmethod
    def from_data(cls, plan_data):
        # FIXME: pass data through JSONSchema
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
            input_spec=plan_data.get('input_spec', None),
            steps=steps,
            activities=activities,
        )

        _LOGGER.debug('Loaded plan %s(steps:%d activities:%d)',
                      plan, len(steps), len(activities))

        return plan

    def __repr__(self):
        return 'Plan(name={name})'.format(name=self.name)
