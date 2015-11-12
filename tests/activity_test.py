"""Unit tests for pydecider.activity
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

import pydecider
import pydecider.activity


class StepStateTest(unittest.TestCase):

    def test_basic_activity(self):
        """Test basic definition of activities.
        """
        my_act = pydecider.activity.Activity.from_data(
            {
                'name': 'MyActivity',
                'version': '1.0',
                'input_spec': None,
                'outputs_spec': None,
            }
        )

        self.assertEqual(my_act.name, 'MyActivity')
        self.assertEqual(my_act.version, '1.0')
        self.assertTrue(my_act.check_input({'anything': 'goes'}))
        self.assertEqual(my_act.render_outputs({'anything': 'goes'}), {})
        # Test default values
        self.assertEqual(my_act.heartbeat_timeout, '60')
        self.assertEqual(my_act.schedule_to_start_timeout, '43200')
        self.assertEqual(my_act.schedule_to_close_timeout, '518400')
        self.assertEqual(my_act.start_to_close_timeout, '432000')

    def test_basic_activity_advanced(self):
        """Test advanced definition of activities.
        """
        my_act = pydecider.activity.Activity.from_data(
            {
                'name': 'MyActivity2',
                'version': '2.0',
                'task_list': 'foobar',
                'heartbeat_timeout': '42',
                'schedule_to_start_timeout': '43',
                'schedule_to_close_timeout': '44',
                'start_to_close_timeout': '45',
            }
        )

        self.assertEqual(my_act.name, 'MyActivity2')
        self.assertEqual(my_act.version, '2.0')
        self.assertTrue(my_act.check_input({'anything': 'goes'}))
        self.assertEqual(my_act.render_outputs({'anything': 'goes'}), {})
        self.assertEqual(my_act.heartbeat_timeout, '42')
        self.assertEqual(my_act.schedule_to_start_timeout, '43')
        self.assertEqual(my_act.schedule_to_close_timeout, '44')
        self.assertEqual(my_act.start_to_close_timeout, '45')

    def test_input_spec(self):
        my_act = pydecider.activity.Activity.from_data(
            {
                'name': 'MyActivity',
                'version': '1.0',
                'input_spec': {
                    'type': 'object',
                    'properties': {
                        'a': {
                            'type': 'string'
                        }
                    },
                    'required': ['a']
                }
            }
        )

        self.assertTrue(my_act.check_input({'a': 'hello'}))
        self.assertRaises(
            pydecider.schema.ValidationError,
            my_act.check_input,
            {'anything': 'goes'},
        )

    def test_outputs_spec(self):
        my_act = pydecider.activity.Activity.from_data(
            {
                'name': 'MyActivity',
                'version': '1.0',
                'outputs_spec': {
                    'a': '$',
                    'b': '$.hello',
                }
            }
        )

        self.assertEquals(
            my_act.render_outputs({'hello': 'world'}),
            {
                'a': {'hello': 'world'},
                'b': 'world'
            }
        )

    def test_invalid_outputs_spec(self):
        self.assertRaises(
            pydecider.schema.ValidationError,
            pydecider.activity.Activity.from_data,
            {
                'name': 'MyActivity',
                'version': '1.0',
                'outputs_spec': {
                    '__bad_name__': 'bad',
                }
            }
        )


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
