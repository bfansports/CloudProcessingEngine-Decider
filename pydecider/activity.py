import logging

from .schema import SchemaValidated

import yaql
import yaql.exceptions

_LOGGER = logging.getLogger(__name__)


class Activity(SchemaValidated):

    __slots__ = ('name', 'version', 'description',
                 '_input_validator', 'outputs_spec',
                 '_task_list',
                 'heartbeat_timeout',
                 'schedule_to_start_timeout',
                 'schedule_to_close_timeout',
                 'start_to_close_timeout')

    def __init__(self, name, version, description,
                 input_spec, outputs_spec,
                 task_list,
                 heartbeat_timeout,
                 schedule_to_close_timeout,
                 schedule_to_start_timeout,
                 start_to_close_timeout):

        self.name = name
        self.version = version
        self.description = description
        self._task_list = task_list
        self.heartbeat_timeout = heartbeat_timeout
        self.schedule_to_close_timeout = schedule_to_close_timeout
        self.schedule_to_start_timeout = schedule_to_start_timeout
        self.start_to_close_timeout = start_to_close_timeout

        if input_spec:
            self.init_validator(input_spec)

        if outputs_spec:
            try:
                self.outputs_spec = {key: yaql.parse(expr)
                                     for key, expr in outputs_spec.items()}

            except yaql.exceptions.YaqlGrammarException as err:
                _LOGGER.critical('Invalid YAQL expression in Activity %r: %r',
                                 name, err)
                raise
        else:
            self.outputs_spec = {}

    def __repr__(self):
        return 'Activity(name={name})'.format(name=self.name)

    def render_output(self, output):
        return {
            key: expr.evaluate(output)
            for key, expr in self.outputs_spec.items()
        }

    @property
    def task_list(self):
        if self._task_list is None:
            self._task_list = '{name}-{version}'.format(
                name=self.name,
                version=self.version
            )
        return self._task_list

    @classmethod
    def from_data(cls, activity_data):
        # FIXME: Add JSONSchema validation
        return cls(
            name=activity_data['name'],
            version=activity_data['version'],
            description=activity_data.get(
                'description',
                'Activity %r' % activity_data['name']
            ),
            input_spec=activity_data.get('input_spec', None),
            outputs_spec=activity_data.get('outputs_spec', None),
            task_list=activity_data.get('task_list', None),
            heartbeat_timeout=activity_data.get('heartbeat_timeout', '60'),
            schedule_to_close_timeout=activity_data.get(
                'schedule_to_close_timeout', '300'
            ),
            schedule_to_start_timeout=activity_data.get(
                'schedule_to_start_timeout', '30'
            ),
            start_to_close_timeout=activity_data.get(
                'start_to_close_timeout', '300'
            ),
        )
