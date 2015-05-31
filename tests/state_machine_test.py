"""Unit tests for ct.state_machine
"""

import os
import sys
import unittest

sys.path.append(
    os.path.realpath(
        os.path.join(
            os.path.dirname(__file__),
            '..'
        )
    )
)

import copy
import mock
import yaml

import ct
import ct.plan
import ct.state_machine


class StateMachineTest(unittest.TestCase):
    MY_DIR = os.path.realpath(os.path.dirname(__file__))

    def setUp(self):
        # Load reference plan
        with open(os.path.join(self.MY_DIR, 'plan_hello.yml')) as f:
            plan_data = yaml.load(f)
        self.plan = ct.plan.Plan.from_data(plan_data)
        # Load reference events
        with open(os.path.join(self.MY_DIR, 'plan_hello_events.yml')) as f:
            events_data = yaml.load(f)
        self.events = events_data['events']
        # Create a state machine
        self.statemachine = ct.state_machine.StateMachine(self.plan)

    def test_workflow_start(self):
        results = self.statemachine.eval(self.events[:3])
        self.assertTrue(self.statemachine.state.is_in_state('running'))
        self.assertEquals(
            [
                (result.name, result.activity, result.activity_input)
                 for result in results
            ],
            [
                ('saying_hi', self.plan.activities['HelloWorld'], None)
            ]
        )

    def test_workflow_unknown_abort(self):
        myevents = copy.deepcopy(self.events[:3])
        myevents[-1]['eventType'] = 'Foo'
        results = self.statemachine.eval(myevents[:3])
        self.assertTrue(self.statemachine.state.is_in_state('failed'))
        self.assertEquals([], results)

    def test_workflow_invalid_input_abort(self):
        myevents = copy.deepcopy(self.events[:3])
        myevents[0]['eventType'] = 'Foo'
        results = self.statemachine.eval(myevents[:3])
        self.assertTrue(self.statemachine.state.is_in_state('failed'))
        self.assertEquals([], results)

    def test_workflow_first_completed(self):
        results = self.statemachine.eval(self.events[:13])
        self.assertTrue(self.statemachine.state.is_in_state('running'))
        self.assertEquals(
            [
                (result.name, result.activity, result.activity_input)
                 for result in results
            ],
            [
                ('saying_hi_again', self.plan.activities['HelloWorld'], None)
            ]
        )


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
