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
        my_act = pydecider.activity.Activity.from_data(
            {
                'name': 'MyActivity',
                'version': '1.0',
                'input_spec': None,
                'outputs_spec': None,
            }
        )

        self.assertEquals(my_act.name, 'MyActivity')
        self.assertEquals(my_act.version, '1.0')
        self.assertTrue(my_act.check_input({'anything': 'goes'}))
        self.assertEquals(my_act.render_outputs({'anything': 'goes'}), {})

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
