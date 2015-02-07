from __future__ import absolute_import

import logging
import copy

import yaml
import boto.swf.layer2 as swf

from .state import State

_LOGGER = logging.getLogger(__name__)

HANDLED_EVENTS = {
    '_PlanLoad': 'load',

    'WorkflowExecutionStarted': 'start',

    'DecisionTaskScheduled': 'skip',
    'DecisionTaskStarted': 'skip',
    'DecisionTaskCompleted': 'skip',

    'ActivityTaskScheduled': 'scheduled',
    'ActivityTaskStarted': 'skip',
    'ActivityTaskCompleted': 'completed',
}


class Decider(swf.Decider):

    name = 'generic'
    version = '1.0'

    def __init__(self, plan, domain, task_list):
        self.domain = domain
        self.task_list = task_list
        super(Decider, self).__init__()

        self.event_handlers = {
            event: getattr(self, 'event_{handler}'.format(handler=handler))
            for event, handler in HANDLED_EVENTS.items()
        }
        self.plan = plan
        self.state = None
        self.event_ids = {}

    def run(self):
        decision_task = self.poll()
        _LOGGER.debug('Received decision task: %r', decision_task)
        if 'events' in decision_task:
            # Collect the entire history if there are enough events to become
            # paginated
            events = decision_task['events']
            while 'nextPageToken' in decision_task:
                decision_task = self.poll(
                    next_page_token=decision_task['nextPageToken']
                )
                if 'events' in decision_task:
                    events.extend(decision_task['events'])

            # Compute decision based on events
            decisions = self._run(events)

            self.complete(decisions=decisions)

        _LOGGER.debug('Tic')
        return True

    def _run(self, events):
        # First clear the state
        self.state = State()
        self.event_ids.clear()

        # Inject a load plan event
        events.insert(0, {'eventId': 0, 'eventType': '_PlanLoad'})

        # Then, replay the state from the events
        for event in events:
            self._run_event(event)

        _LOGGER.debug('State replayed from events: %r', self.state)
        decisions = swf.Layer1Decisions()

        if self.state.is_completed:
            decisions.complete_workflow_execution()

        else:
            self._run_ready_steps(decisions)

        _LOGGER.debug('Decisions: %r', decisions._data)
        return decisions

    def _run_event(self, event):
        _LOGGER.debug('Processing event %r', event['eventType'])

        handler_fun = self.event_handlers.get(
            event['eventType'],
            self.event_abort
        )
        handler_fun(event)

    def event_load(self, event):
        # Create loading time steps from the plan
        with self.state(event):
            # Import all predefined steps from the plan
            for step in self.plan.steps:
                self.state.step_insert(step)
        # No sideeffects
        return []

    def event_skip(_self, event):
        _LOGGER.info('Skipping event: %r', event['eventType'])
        # No sideeffects
        return []

    def event_abort(_self, event):
        _LOGGER.warning('Unknown event: %r', event)
        # No sideeffects
        # FIXME: Should abort the workflow
        return []

    def event_start(self, event):
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

        return [
            ('new_ready_steps', ()),
        ]

    def event_scheduled(self, event):
        """Record the eventId associated with activities we scheduled."""
        _LOGGER.debug('%r', event)
        step_name = event['activityTaskScheduledEventAttributes']['activityId']
        event_id = event['eventId']

        with self.state(event):
            self.state.step_update(step_name, 'running')

        _LOGGER.debug('Associating step %r with event_id %r',
                      step_name, event_id)
        self.event_ids[event_id] = step_name

        return []

    def event_completed(self, event):
        _LOGGER.debug('%r', event)
        output = event['activityTaskCompletedEventAttributes'].get('result')
        sched_event_attr = event['activityTaskCompletedEventAttributes']
        sched_event_id = sched_event_attr['scheduledEventId']
        step_name = self.event_ids[sched_event_id]
        with self.state(event):
            self.state.step_update(step_name, 'succeeded', output)

        return [
            ('new_ready_steps', ()),
        ]

    def _run_ready_steps(self, decisions):
        _LOGGER.debug('Running all "ready" steps')

        ready_steps = self.state.step_next()
        _LOGGER.debug('Next steps: %r', ready_steps)

        for step in ready_steps:
            step_result = step.run()
            _LOGGER.debug('step_result: %r', step_result)
            # FIXME: Handle StepTemplate
            activity = step_result.activity
            decisions.schedule_activity_task(
                activity_id=step_result.name,
                activity_type_name=activity.name,
                activity_type_version=activity.version,
                task_list=activity.task_list,
                control=None,  # FIXME: Do we want to pass context data?
                heartbeat_timeout=activity.heartbeat_timeout,
                schedule_to_close_timeout=activity.schedule_to_close_timeout,
                schedule_to_start_timeout=activity.schedule_to_start_timeout,
                start_to_close_timeout=activity.start_to_close_timeout,
                input=step_result.activity_input,
            )
