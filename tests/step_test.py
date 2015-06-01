"""Unit tests for pydecider.step
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

from pydecider.step import Step, StepDefinitionError
from pydecider.state import StepStateStatus


class StepTest(unittest.TestCase):
    def setUp(self):
        self.activities = {
            'test1': True,
        }

    def test_step_create_bad_data(self):
        step_data = {
            "name": "bad",
        }

        self.assertRaises(
            ValueError,
            Step.from_data,
            step_data,
            self.activities
        )

    def test_step_create_requires(self):
        step_data = {
            "name": "test",
            "activity": "test1",  # Note: Not checking activity here
            "requires": ["foo", ("bar", "succeeded"), ("baz", "failed")],
        }

        step = Step.from_data(step_data, self.activities)

        self.assertEquals(
            step.requires,
            {
                'foo': StepStateStatus.completed,
                'bar': StepStateStatus.succeeded,
                'baz': StepStateStatus.failed,
            }
        )

    def test_activity_step_create(self):
        step_data = {
            "name": "test",
            "activity": "test1",
        }

        step = Step.from_data(step_data, self.activities)

        self.assertEquals(step.name, 'test')
        self.assertTrue(step.activity is self.activities['test1'])
        self.assertTrue(step.input_template is None)

    def test_activity_step_create_no_activity(self):
        step_data = {
            "name": "test",
            "activity": "test2",
        }

        self.assertRaises(
            KeyError,
            Step.from_data,
            step_data,
            self.activities
        )

    def test_activity_step_create_bad_status(self):
        step_data = {
            "name": "test",
            "activity": "test1",
            "requires": [("foo", "blah")],
        }

        self.assertRaises(
            StepDefinitionError,
            Step.from_data,
            step_data,
            self.activities
        )


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
