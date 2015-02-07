from __future__ import absolute_import

import enum
import weakref
import logging
import collections

from . import step

_LOGGER = logging.getLogger(__name__)
INIT_STEP = '$init'
END_STEP = '$end'


class DeciderStepResult(object):
    pass


class DeciderStep(step.Step):
    def run(self, _step_input):
        return DeciderStepResult(
            # FIXME
        )

    def prepare(self, _context):
        return {}

    def render(self, output):
        return output


class StateStatus(enum.Enum):
    """Enumeration of the possible :class:`State` statuses."""
    #: Pristin empty status.
    init = 0
    #: Input has been set and Steps are running or ready.
    running = 1
    #: All Steps are in the completed status or one was aborted.
    completed = 2


class State(object):
    __slots__ = ('status',
                 'step_states',
                 '_context',
                 '_orphaned_steps',
                 '_init_step',
                 '_end_step',
                 )

    def __init__(self):
        """Init state"""
        self.status = StateStatus.init
        self.step_states = {}
        self._context = None
        self._orphaned_steps = {}
        # Add an INIT/END fake steps
        self._init_step = StepState(step=DeciderStep(INIT_STEP),
                                    status='running',
                                    context='__init__')
        self._end_step = StepState(step=DeciderStep(END_STEP,
                                   requires=[INIT_STEP]),
                                   context='__init__')
        self._stepstate_insert(self._init_step)
        self._stepstate_insert(self._end_step)

    def __repr__(self):
        return '{ctype}(status={status},steps={steps})'.format(
            ctype=self.__class__.__name__,
            status=self.status.name,
            steps=len(self.step_states)
        )

    #################################################
    @property
    def is_completed(self):
        return self.status is StateStatus.completed

    #################################################
    # Context management
    def __call__(self, context):
        self._context = context
        return self

    def __enter__(self):
        assert(self._context is not None)

    def __exit__(self, exc_type, exc_value, traceback):
        assert(self._context is not None)
        # Only clear the context is we didn't encounter an exception. Otherwise
        # keep it for debug purposes
        if exc_type is None:
            self._context = None

    #################################################
    # State manipulations
    def set_input(self, input_data):
        assert(self._context is not None)
        assert(self.status is StateStatus.init)

        self.step_update(INIT_STEP, 'completed', new_data=input_data)
        self.status = StateStatus.running

    def step_update(self, step_name, new_status, new_data=None):
        """Update a Step with new status and/or output data.
        """
        assert(self._context is not None)
        step_state = self.step_states[step_name]
        step_state.update(new_status,
                          context=self._context,
                          new_output=new_data)

        if self._end_step.status is StepStateStatus.ready:
            self.status = StateStatus.completed

    def step_insert(self, step):
        """Add a step definition to the state.
        """
        assert(self._context is not None)
        step_state = StepState(step, self._context)
        _LOGGER.debug('Defining new step %r in state', step_state)

        if self._stepstate_insert(step_state):
            # All steps are a parent of END_STEP
            # FIXME: Could be optimized so that only steps without children are
            #        parented to END_STEP
            self._end_step.parents.add(step_state)
            step_state.children.add(self._end_step)
            # See if we can re-parents some previously orphaned Step with the
            # one we have just added.
            orphans = self._orphaned_steps.pop(step.name, [])
            for orphan in orphans:
                self._stepstate_insert(orphan)

    #################################################
    def step_next(self, hint=None):
        """Search for steps ready to be ran.

        :param str hint:
            Place to start searching steps that are now ready to be scheduled
            (usually, the last `completed` step).
        """
        ready_steps = set()
        # Were we given a place to start looking?
        if hint:
            hint_step = self.step_states[hint]

            # Check that this is completed
            if not hint_step.status.is_completed:
                # FIXME: This should be an error
                return set()

            for child_step in hint_step.children:
                if child_step.is_ready:
                    ready_steps.add(child_step)

        else:
            # Walk the whole tree collecting ready StepState
            for child in self._init_step.children:
                if child.is_ready:
                    ready_steps.add(child)
                else:
                    child_name = child.step.name
                    ready_steps |= self.step_next(child_name)

        return ready_steps

    def _stepstate_insert(self, step_state):
        if ((not step_state.step.requires) and
                (step_state.step.name is not INIT_STEP)):
            # No requirement, set this step as a child of the root step
            self._init_step.children.add(step_state)
            self.step_states[step_state.name] = step_state
            return True

        elif all([required in self.step_states
                  for (required, _) in step_state.step.requires]):
            # All the required steps are defined, update their children set and
            # record them in this step_state's parents set
            for (required, _) in step_state.step.requires:
                self.step_states[required].children.add(step_state)
                step_state.parents.add(self.step_states[required])

            self.step_states[step_state.name] = step_state
            return True

        else:
            # We failed to insert this step_state
            # Parent steps are missing, set it as orphaned
            for (required, _) in step_state.step.requires:
                if required not in self.step_states:
                    self._orphaned_steps.setdefault(
                        required, set()
                    ).add(step_state)
            return False


class StepStateStatus(enum.Enum):
    """Enumeration of the possible :class:`StepState` statuses."""

    #: Step is not started yet (may be waiting on dependencies).
    pending = 0
    #: Step is ready to be started
    ready = 1
    #: Step is running
    running = 2
    #: Step was either completed (sucess OR failure) or skipped.
    completed = 4
    #: Step resulted in a permanent error.
    aborted = 8
    #: Step completed as successful.
    succeeded = completed | 16
    #: Step completed in failure.
    failed = completed | 32
    #: Step was skipped (will not be run).
    skipped = completed | 64

    @property
    def is_completed(self):
        """`True` if the status is either `succeeded`, `failed` or `skipped`.
        """
        return bool(self.value & self.__class__.completed.value)


class StepState(object):

    __slots__ = ('status',
                 'step',
                 'input',
                 'output',
                 'attrs',
                 'children',
                 'parents',
                 'history',
                 '__weakref__')

    def __init__(self, step, context,
                 status=StepStateStatus.pending):

        if not isinstance(status, StepStateStatus):
            status = getattr(StepStateStatus, status)

        self.step = step
        self.status = status
        self.input = None
        self.output = None
        self.attrs = None
        self.children = weakref.WeakSet()
        self.parents = weakref.WeakSet()
        self.history = collections.deque()
        self.history.append(
            (status, context)
        )

    def __repr__(self):
        return 'StepState({name}:{status})'.format(
            name=self.step.name, status=self.status.name
        )

    @property
    def name(self):
        return self.step.name

    def _prepare(self):
        """Prepare the input from the step input template and the parents data.
        """
        assert(self.status is StepStateStatus.ready)
        context = self._build_context()
        render = self.step.prepare(context)
        return render

    def _build_context(self):
        context = {}
        for parent in self.parents:
            if parent.name is INIT_STEP:
                context.update({'__init__': parent.attrs})
            else:
                context.update({parent.name: parent.attrs})
        return context

    def _record(self, output):
        """Invoke the step rendering of the results."""
        self.output = output
        attrs = self.step.render(output)
        self.attrs = attrs

    @property
    def is_ready(self):
        """`True` if the Step is ready to be evaluated.

        This means the step hasn't ran yet and all its parents are completed.
        """
        if self.status is StepStateStatus.ready:
            return True
        # You cannot be ready if you are already completed/aborted
        if self.status is not StepStateStatus.pending:
            return False
        # Check that all our parents are completed
        return all([parent.status.is_completed for parent in self.parents])

    def update(self, new_status, context, new_output=None):
        if not isinstance(new_status, StepStateStatus):
            new_status = getattr(StepStateStatus, new_status)

        _LOGGER.info('Updating step %r status: %s -> %s',
                     self.name, self.status.name, new_status.name)
        self.status = new_status

        if self.status is StepStateStatus.ready:
            self.input = self._prepare()
        elif self.status is StepStateStatus.running:
            pass
        elif self.status.is_completed:
            self._record(new_output)
            for child in self.children:
                if child.is_ready:
                    child.update(StepStateStatus.ready, context)
        else:
            # FIXME: cleanup
            raise Exception('Invalid update')

        # Record change in history
        self.history.append((self.status, context))

    def run(self):
        return self.step.run(self.input)
