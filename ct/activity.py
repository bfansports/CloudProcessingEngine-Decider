import logging

import yaql
import yaql.exceptions

_LOGGER = logging.getLogger(__name__)


class Activity(object):

    __slots__ = ('name', 'version', 'description',
                 'input_spec', 'outputs_spec',
                 'heartbeat_timeout',
                 'schedule_to_start_timeout',
                 'schedule_to_close_timeout',
                 'start_to_close_timeout')

    def __init__(self, name, version, description,
                 input_spec, outputs_spec,
                 heartbeat_timeout='60',
                 schedule_to_close_timeout='300',
                 schedule_to_start_timeout='30',
                 start_to_close_timeout='300'):

        self.name = name
        self.version = version
        self.description = description
        self.heartbeat_timeout = heartbeat_timeout
        self.schedule_to_close_timeout = schedule_to_close_timeout
        self.schedule_to_start_timeout = schedule_to_start_timeout
        self.start_to_close_timeout = start_to_close_timeout

        self.input_spec = None  # FIXME: Compile a JSONSchema
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
        return '{name}-{version}'.format(name=self.name, version=self.version)

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
            input_spec=activity_data['input_spec'],
            outputs_spec=activity_data['outputs_spec'],
            # FIXME: Timeout attributes
        )
