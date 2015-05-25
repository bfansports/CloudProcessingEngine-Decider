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

import collections
import mock
import yaml

import ct
import ct.state


TestParent = collections.namedtuple('TestParent', ['name', 'output'])


class StepStateTest(unittest.TestCase):
    def setUp(self):
        self.mock_step = mock.Mock()
        self.step_state = ct.state.StepState(step=self.mock_step,
                                             status='running',
                                             context='__test__')

    def test_step_prepare_no_parents(self):
        """No parents, `step.prepare` called with an empty dict."""
        self.step_state.update('ready', '__test_update__')
        self.mock_step.prepare.assert_called_with({})

    def test_step_prepare_parents(self):
        """Make sure `step.prepare` is called with a dict of all the parents
        attributes.
        """
        self.step_state.parents = [
            TestParent('foo', {'a': 1}),
            TestParent('bar', {'b': 1}),
            TestParent('baz', {'c': 1}),
        ]
        self.step_state.update('ready', '__test_update__')
        self.mock_step.prepare.assert_called_with(
            {
                'foo': {'a': 1},
                'bar': {'b': 1},
                'baz': {'c': 1},
            }
        )

    def test_step_prepare_parents_with_input(self):
        """Make sure `step.prepare` is called with a dict of all the parents
        attributes and that the special input step in properly named.
        """
        self.step_state.parents = [
            TestParent('foo', {'a': 1}),
            TestParent(ct.state.INIT_STEP, {'b': 1}),
            TestParent('baz', {'c': 1}),
        ]
        self.step_state.update('ready', '__test_update__')
        self.mock_step.prepare.assert_called_with(
            {
                'foo': {'a': 1},
                '__input__': {'b': 1},
                'baz': {'c': 1},
            }
        )


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
