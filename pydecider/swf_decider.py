from __future__ import (
    absolute_import,
    division,
    print_function
)

import json
import logging
import time

import boto.swf.layer2 as swf
import boto.sqs.connection as sqs

from .state_machine import StateMachine

_LOGGER = logging.getLogger(__name__)


class SWFDecider(swf.Decider):

    name = 'generic'
    version = '1.0'

    def __init__(self, domain, task_list, output_queue, plan=None):
        self.domain = domain
        self.task_list = task_list
        super(SWFDecider, self).__init__()

        self.statemachine = StateMachine(plan)
        self.sqs = sqs.SQSConnection()
        self.output_queue = output_queue

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
            decisions = self._run(events, decision_task['workflowExecution'])
            self.complete(decisions=decisions)

        _LOGGER.debug('Tic')
        return True

    def _run(self, events, workflowExecution):
        # Run the statemachine on the events
        results = self.statemachine.eval(events)

        # Now we can do 4 things:
        #  - Complete the workflow
        #  - Fail the workflow
        #  - Schedule more activities
        #  - Nothing
        decisions = swf.Layer1Decisions()

        if self.statemachine.is_succeeded:
            decisions.complete_workflow_execution(result=None)
            return decisions

        elif self.statemachine.is_failed:
            # FIXME: Improve error reporting
            self.sqs.send_message(self.output_queue, json.dumps({
                'time': time.time(),
                'type': 'WORKFLOW_FAILED',
                'data': {
                    'workflow': workflowExecution
                }
            }))
            decisions.fail_workflow_execution(reason='State machine aborted')
            return decisions

        # We are still going, start any ready activity
        for next_step in results:
            activity = next_step.activity
            # FIXME: We are assuming JSON activity input here
            activity_input = (
                json.dumps(next_step.activity_input)
                if next_step.activity_input is not None
                else None
            )

            self.sqs.send_message(self.output_queue, json.dumps({
                'time': time.time(),
                'type': 'ACTIVITY_SCHEDULED',
                'data': {
                    'workflow': workflowExecution,
                    'activity': {
                        'activityId': next_step.name,
                        'activityType': activity.name,
                        'activityVersion': activity.version
                    }
                }
            }))
            decisions.schedule_activity_task(
                activity_id=next_step.name,
                activity_type_name=activity.name,
                activity_type_version=activity.version,
                task_list=activity.task_list,
                control=None,  # FIXME: Do we want to pass context data?
                heartbeat_timeout=activity.heartbeat_timeout,
                schedule_to_close_timeout=activity.schedule_to_close_timeout,
                schedule_to_start_timeout=activity.schedule_to_start_timeout,
                start_to_close_timeout=activity.start_to_close_timeout,
                input=activity_input,
            )

        return decisions
