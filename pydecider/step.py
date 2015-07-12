from __future__ import (
    absolute_import,
    division,
    print_function
)

import abc
import json
import logging

import jinja2
import jinja2.meta

from .state_status import StepStateStatus
from .step_results import (
    ActivityStepResult,
    TemplatedStepResult,
)

_LOGGER = logging.getLogger(__name__)


class StepError(StandardError):
    pass


class StepDefinitionError(StepError):
    pass


class Step(object):
    """Base `Step` in a workflow.

    A `Step` is composed of a name and a collection of its requirements.
    """

    __slots__ = ('name', 'requires')
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, requires=()):
        self.name = name
        self.requires = dict([self._resolve_parent(parent_def)
                              for parent_def in requires])

    @staticmethod
    def _resolve_parent(parent_def):

        if isinstance(parent_def, basestring):
            return (parent_def, StepStateStatus.completed)
        else:
            try:
                parent_name, status_name = parent_def
                return (parent_name, getattr(StepStateStatus, status_name))

            except AttributeError as err:
                raise StepDefinitionError('Invalid Step status name: %r' %
                                          err.args[0])
            except StandardError:
                raise StepDefinitionError('Invalid Step definition: %r' %
                                          parent_def)

    @classmethod
    def from_data(cls, step_data, activities):
        """Create a new Step object from a step definition"""
        if 'activity' in step_data:
            activity_name = step_data['activity']
            activity = activities[activity_name]

            step = ActivityStep(
                name=step_data['name'],
                requires=step_data.get('requires', ()),
                activity=activity,
                input_template=step_data.get('input', None),
            )

        elif 'eval' in step_data:
            step = TemplatedStep(
                name=step_data['name'],
                requires=step_data.get('requires', ()),
                eval_block=step_data['eval'],
            )

        else:
            raise ValueError('Invalid Step data: %r' % step_data)

        return step

    @abc.abstractmethod
    def prepare(self, _context):
        """Prepare step's input from context.

        :returns:
            Step's input
        """
        pass

    @abc.abstractmethod
    def run(self, _step_input):
        """Run the step from its input.

        :returns:
            A StepResult object
        """
        pass

    @abc.abstractmethod
    def render(self, _output):
        """Renders the Step's output for usage by other steps.

        :returns:
            A dictionary of 'key: value' pairs.
        """
        pass

    def __repr__(self):
        return '{ctype}(name={name})'.format(ctype=self.__class__.__name__,
                                             name=self.name)


class ActivityStep(Step):

    __slots__ = ('activity', 'input_template', '__env')

    def __init__(self, name, activity, input_template, requires=()):
        super(ActivityStep, self).__init__(name, requires)
        self.activity = activity
        self.input_template = None

        # Define the Jinga2 environment
        self.__env = jinja2.Environment(finalize=self.__jsonify)

        if input_template is not None:
            tp_required = self._check_template_dependencies(input_template)
            for tp_var in tp_required:
                # `__input__` is a "magic" step referencing the workflow input
                if tp_var == '__input__':
                    continue
                if tp_var not in self.requires:
                    raise StepDefinitionError(
                        'Invalid step %r: Template used %r is not required' %
                        (self.name, tp_var,)
                    )

            self.input_template = self.__env.from_string(input_template)

    def __jsonify(self, obj):
        # Note: This method is called by Jinja2 to "finalize" its variables.
        #       Jinja2 also calls it to "finalize" the non-variable chunks
        #       of a template's string when compiling the template, so we have
        #       to be careful of extra quoting.
        if self.input_template is not None:
            # Now that the templates are defined, we can define the "finalize"
            # function to JSON dump all template variables.
            return json.dumps(obj, indent=4, sort_keys=True)
        else:
            return obj

    def prepare(self, context):
        if self.input_template is not None:
            activity_input_json = self.input_template.render(context)
            # FIXME: We are assuming JSON activity input here
            try:
                activity_input = json.loads(activity_input_json)
            except ValueError:
                _LOGGER.exception('Invalid template result: %r',
                                  activity_input_json)
                raise
        else:
            activity_input = None

        self.activity.check_input(activity_input)
        return activity_input

    def run(self, step_input):
        return ActivityStepResult(
            name=self.name,
            activity=self.activity,
            activity_input=step_input,
        )

    def render(self, output):
        return self.activity.render_output(output)

    def _check_template_dependencies(self, input_template):
        """Return the list of used external variable in the template.
        """
        parsed_template = self.__env.parse(input_template)
        return jinja2.meta.find_undeclared_variables(parsed_template)


class TemplatedStep(Step):

    __slots__ = ('eval_block')

    def __init__(self, name, eval_block, requires=()):
        super(TemplatedStep, self).__init__(name, requires)
        self.eval_block = jinja2.Template(eval_block)

    def prepare(self, context):
        return self.eval_block.render(context)

    def run(self, _step_input):
        return TemplatedStepResult()

    def render(self, _output):
        # NOTE: Templated steps do not have any usable attributes
        return {}
