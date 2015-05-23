from __future__ import absolute_import

import logging
import copy

import yaml

from .state import State
from .step_results import (
    ActivityStepResult,
    TemplatedStepResult,
)

_LOGGER = logging.getLogger(__name__)


class StateMachine(object):
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

        _LOGGER.debug('State replayed from events: %r', self.state)
        return results

    ###########################################################################
    def _run_event(self, event):
        """Process a given event and return a list of results.
        """
        _LOGGER.debug('Processing event %r', event['eventType'])

        handler_fun = getattr(
            self,
            'EVENT_%s' % event['eventType'],
            self.__ev_abort
        )
        handler_fun(event)

        # If there is nothing left to do, stop here
        if self.state.is_in_state('completed'):
            return []

        _LOGGER.debug('Running all "ready" steps')
        ready_steps = self.state.step_next()
        _LOGGER.debug('Next steps: %r', ready_steps)

        results = []
        for step in ready_steps:
            step_result = step.run()
            _LOGGER.debug('step_result: %r', step_result)
            if isinstance(step_result, ActivityStepResult):
                results.append(step_result)

            elif isinstance(step_result, TemplatedStepResult):
                raise Exception('Not implemented')

        _LOGGER.debug('Results: %r', results)
        return results

    ###########################################################################
    # Events and handlers
    def __ev_load(self, event):
        # Create loading time steps from the plan
        with self.state(event):
            # Import all predefined steps from the plan
            for step in self.plan.steps:
                self.state.step_insert(step)

    def __ev_skip(_self, event):
        _LOGGER.info('Skipping event: %r', event['eventType'])

    def __ev_abort(self, event):
        # FIXME: Should abort the workflow
        _LOGGER.error('Unknown event: %r', event)

    def __ev_start(self, event):
        """Import input data"""
        _LOGGER.debug('%r', event)
        # Note that if no input was provided, the 'input' key will not be there
        event_input = event.get('input', '')
        try:
            input_data = yaml.load(event_input) or {}
        except yaml.error.YAMLError:
            _LOGGER.exception('Invalid workflow input: %r', event_input)
            raise

        state_event = copy.copy(event)
        state_event['input'] = input_data

        with self.state(state_event):
            # Set the input
            self.state.set_input(input_data)

    def __ev_scheduled(self, event):
        """Record the eventId associated with activities we scheduled."""
        _LOGGER.debug('%r', event)
        step_name = event['activityTaskScheduledEventAttributes']['activityId']
        event_id = event['eventId']

        with self.state(event):
            self.state.step_update(step_name, 'running')

        _LOGGER.debug('Associating step %r with event_id %r',
                      step_name, event_id)
        self._event_ids[event_id] = step_name

    def __ev_completed(self, event):
        _LOGGER.debug('%r', event)
        output = event['activityTaskCompletedEventAttributes'].get('result')
        sched_event_attr = event['activityTaskCompletedEventAttributes']
        sched_event_id = sched_event_attr['scheduledEventId']
        step_name = self._event_ids[sched_event_id]
        with self.state(event):
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
