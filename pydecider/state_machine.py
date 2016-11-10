from __future__ import (
    absolute_import,
    division,
    print_function
)

import json
import logging

from .schema import ValidationError
from .state import State
from .step_results import (
    ActivityStepResult,
    TemplatedStepResult,
)

_LOGGER = logging.getLogger(__name__)


class StateMachine(object):

    __slots__ = ('plan', 'state', '_event_ids')

    def __init__(self, plan):
        self.plan = plan
        self.state = None
        self._event_ids = {}

    ###########################################################################
    # Accessors
    @property
    def is_failed(self):
        return self.state.is_in_state('failed')

    @property
    def is_succeeded(self):
        return self.state.is_in_state('succeeded')

    ###########################################################################
    def eval(self, events):
        # First clear the state
        self.state = State()
        self._event_ids.clear()

        # Inject a load plan event
        self._run_event({'eventId': 0, 'eventType': 'PlanLoad'})

        # Then, replay the state from the events
        for event in events:
            results = self._run_event(event)

        _LOGGER.info('State replayed from events: %r', self.state)
        return results

    ###########################################################################
    def _run_event(self, event):
        """Process a given event and return a list of results.
        """
        _LOGGER.info('Processing event %r', event['eventType'])

        handler_fun = getattr(
            self,
            'EVENT_%s' % event['eventType'],
            self.__ev_abort
        )
        handler_fun(event)

        # If there is nothing left to do, stop here
        if self.state.is_in_state('completed'):
            return []

        _LOGGER.info('Running all "ready" steps')
        ready_steps = self.state.step_next()
        _LOGGER.info('Next steps: %r', ready_steps)

        results = []
        for step in ready_steps:
            step_result = step.run()
            _LOGGER.info('step_result: %r', step_result)
            if isinstance(step_result, ActivityStepResult):
                results.append(step_result)

            elif isinstance(step_result, TemplatedStepResult):
                #results.append(step_result)
                raise Exception('Not implemented')

        _LOGGER.info('Results: %r', results)
        return results

    ###########################################################################
    # Events and handlers
    def __ev_load(self, event):
        # Create loading time steps from the plan
        with self.state(event['eventId']):
            # Import all predefined steps from the plan
            for step in self.plan.steps:
                self.state.step_insert(step)

    def __ev_skip(self, event):
        _LOGGER.info('Skipping event: %r', event['eventType'])

    def __ev_abort(self, event):
        _LOGGER.error('Unknown event: %r', event)
        with self.state(event['eventId']):
            # Set the input
            self.state.set_abort()

    def __ev_start(self, event):
        """Import input data"""
        _LOGGER.info('%r', event)
        start_attrs = event['workflowExecutionStartedEventAttributes']
        # Note that if no input was provided, the 'input' key will not be there
        wf_input = start_attrs.get('input', 'null')
        try:
            input_data = json.loads(wf_input)
            self.plan.check_input(input_data)

        except (ValueError, ValidationError):
            _LOGGER.exception('Invalid workflow input: %r', wf_input)
            # We cannot do anything, just abort
            with self.state(event['eventId']):
                self.state.set_abort()
            return

        with self.state(event['eventId']):
            # Set the input
            self.state.set_input(input_data)

    def __ev_scheduled(self, event):
        """Record the eventId associated with activities we scheduled."""
        _LOGGER.info('%r', event)
        step_name = event['activityTaskScheduledEventAttributes']['activityId']
        event_id = event['eventId']

        with self.state(event['eventId']):
            self.state.step_update(step_name, 'running')

        _LOGGER.info('Associating step %r with event_id %r',
                      step_name, event_id)
        self._event_ids[event_id] = step_name

    def __ev_completed(self, event):
        _LOGGER.info('%r', event)
        completed_event = event['activityTaskCompletedEventAttributes']
        output_json = completed_event.get('result', 'null')
        output = json.loads(output_json)
        sched_event_id = completed_event['scheduledEventId']
        step_name = self._event_ids[sched_event_id]
        with self.state(event['eventId']):
            self.state.step_update(step_name, 'succeeded', output)

    EVENT_PlanLoad = __ev_load
    EVENT_WorkflowExecutionStarted = __ev_start
    EVENT_DecisionTaskScheduled = __ev_skip
    EVENT_DecisionTaskStarted = __ev_skip
    EVENT_DecisionTaskCompleted = __ev_skip
    EVENT_DecisionTaskTimedOut = __ev_skip
    EVENT_ActivityTaskScheduled = __ev_scheduled
    EVENT_ActivityTaskStarted = __ev_skip
    EVENT_ActivityTaskCompleted = __ev_completed
