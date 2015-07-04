import logging

from .schema import SchemaValidated

import yaql
import yaql.exceptions

_LOGGER = logging.getLogger(__name__)


class Activity(SchemaValidated):
    """Activity abstraction.

    Attributes:
        name (str): The name of this `Activity`.
        version (str): The version of this `Activity`.
        task_list (str): Name of the  SWF `task_list` to use when submitting
                         activity tasks.
        heartbeat_timeout (str): SWF 'heartbeat_timeout' value.
        schedule_to_start_timeout (str): SWF 'schedule_to_start_timeout' value.
        schedule_to_close_timeout (str): SWF 'schedule_to_close_timeout' value.
        start_to_close_timeout (str): SWF 'start_to_close_timeout' value.

    Examples:
        >>> a = activity.Activity.from_data(
        ...     {
        ...         'name': 'MyActivity',
        ...         'version': '1.0'
        ...     }
        ... )
        >>> a
        Activity(name='MyActivity')
        >>> a.name
        'MyActivity'

    """

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
                 heartbeat_timeout=None,
                 schedule_to_close_timeout=None,
                 schedule_to_start_timeout=None,
                 start_to_close_timeout=None):

        self.name = name
        self.version = version

        if task_list is None:
            task_list = '{name}-{version}'.format(
                name=self.name,
                version=self.version
            )
        self.task_list = task_list

        if heartbeat_timeout is None:
            heartbeat_timeout = '60'
        self.heartbeat_timeout = heartbeat_timeout

        if schedule_to_close_timeout is None:
            schedule_to_close_timeout = '300'
        self.schedule_to_close_timeout = schedule_to_close_timeout

        if schedule_to_start_timeout is None:
            schedule_to_start_timeout = '30'
        self.schedule_to_start_timeout = schedule_to_start_timeout

        if start_to_close_timeout is None:
            start_to_close_timeout = '300'
        self.start_to_close_timeout = start_to_close_timeout

        if input_spec:
            self.init_validator(input_spec)

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

    def render_output(self, output):
        """Use the `Activity`'s `outputs_spec` to generate all the defined
        representation of this activity's output.
        """
        return {
            key: expr.evaluate(output)
            for key, expr in self._outputs_spec.items()
        }

    @classmethod
    def from_data(cls, activity_data):
        """Define an `Activity` from a dictionary of attributes.
        """
        # TODO: Add JSONSchema validation of activity_data
        return cls(
            name=activity_data['name'],
            version=activity_data['version'],
            input_spec=activity_data.get('input_spec', None),
            outputs_spec=activity_data.get('outputs_spec', None),
            task_list=activity_data.get('task_list', None),
            heartbeat_timeout=activity_data.get(
                'heartbeat_timeout', None
            ),
            schedule_to_close_timeout=activity_data.get(
                'schedule_to_close_timeout', None
            ),
            schedule_to_start_timeout=activity_data.get(
                'schedule_to_start_timeout', None
            ),
            start_to_close_timeout=activity_data.get(
                'start_to_close_timeout', None
            ),
        )
