Getting Started with Plans
==========================

The decider consumes a plan and some input. So the first thing you'll need to do
is to define that plan.

Basic Plan
----------

The most basic plan is as folow:

.. code-block:: yaml

    ---
    name: MyWorkFlow
    version: 1.0

    activities:
    - name: MyAct1
      version: 1.0

    steps:
    - name: MyStep1
      input: |
          Input passed to MyAct1
      activity: MyAct1

This simple plan tells the decider to schedule a single activity, `"MyAct1"`,
and when it completes, mark the workflow as completed.


Plan Attributes
~~~~~~~~~~~~~~~

This plan specification first defines a ``name`` and a ``version`` for the Plan.
These correspond directly the the `"Workflow name"` and `"Workflow version"`
concepts from SWF.

Activities
~~~~~~~~~~

The plan defines a list of `activities`. These are the activities that your
plan is going to use during its execution.

At the minimum, you'll need to provide a ``name`` and ``version`` for each of
your activity (again matching to the `"Activity name"` and `"Activity version"`
of SWF).

You may also want to provide a ``task_list`` attribute as well; without it, the
decider assumes it is ``<name>-<version>``).

.. code-block:: yaml
   :emphasize-lines: 3

    - name: MyAct1
      version: 1.0
      task_list: MyTaskList1

Steps
~~~~~

Your plan will need to contain a list of `steps`. Each step has a unique
name and references an activity that will be used to accomplish it.
You can optionally specify some input to be sent to the Activity.

Here, in the example above, we define `"MyStep1"` which will use `"MyAct1"`.
The decider will send the data ``"Input passed to MyAct1"`` as input to this
activity.


Multiple Steps
--------------

We can make the plan a little more interesting by adding multiple steps.

.. code-block:: yaml

    ---
    name: MyWorkFlow
    version: 1.0

    activities:
    - name: MyAct1
      version: 1.0
    - name: MyAct2
      version: 1.0
    - name: MyAct3
      version: 1.0

    steps:
    - name: MyStep1
      activity: MyAct1
    - name: MyStep2
      activity: MyAct2
    - name: MyStep3
      activity: MyAct3

This extands the plan by defining 2 more steps using 2 new acticities.

Now the decider will schedule all three steps and will terminte the workflow
once they all have been completed.


Step Dependencies
-----------------

Now that we have multiple steps, we may want to define intedependencies between
them.

You can do that by defining the ``requires`` attribute on a step and listing all
the other steps that must complete before that step should be scheduled.

.. code-block:: yaml
   :emphasize-lines: 6,9

    steps:
    - name: MyStep1
      activity: MyAct1
    - name: MyStep2
      activity: MyAct2
      requires: [MyStep1]
    - name: MyStep3
      activity: MyAct3
      requires: [MyStep1]

This tells the decider to only schedule `"MyStep2"` and `"MyStep3"` once
`"MyStep1"` is completed. And once these two have completed, complete the
workflow.


Step Statuses
-------------

Until now, we have talked about steps beein `"completed"` or not. This means
that the step execution finished either successfully or failed.

You can express more control over your steps' execution by specifying exactly
which status a step should wait for before being scheduled.

.. code-block:: yaml
   :emphasize-lines: 6-7,10-11

    steps:
    - name: MyStep1
      activity: MyAct1
    - name: MyStep2
      activity: MyAct2
      requires:
      - [MyStep1, suceeded]
    - name: MyStep3
      activity: MyAct3
      requires:
      - [MyStep1, failed]

If a step's requirements complete but do not satisfy the specified constrains,
the step will be skipped.

In this example, `"MyStep2"` will only be scheduled if `"MyStep1"` succeeds and,
respectively, `"MyStep3"` only if it fails. In each case, the other step will be
skipped.


Templated Inputs
----------------

.. note::
    All of this **requires** that the Workflow itself and all its activities use
    JSON as serialization format for its inputs and outputs.

Using the Worflow's input
~~~~~~~~~~~~~~~~~~~~~~~~~

It is possible construct the input passed to Activities using a templating
language.

Assuming the input of the Worflow is:

.. code-block:: json

    {
        "user": "John",
        "country": "USA"
    }

It then possible to modify our steps definition as follow:

.. code-block:: yaml
   :emphasize-lines: 4-7

    steps:
    - name: MyStep1
      activity: MyAct1
      input: |
        {
            "request-user": {{__input__.user}}
        }

This uses the `__input__` object to reference to the Workflow's own input and,
since it is a hash, accesses the `user` key's value, `"John"`. The value is then
replaced in the temaple and the input to that Step becomes:

.. code-block:: yaml

    steps:
    - name: MyStep1
      activity: MyAct1
      input: |
        {
            "request-user": "John"
        }


Using other step's output
~~~~~~~~~~~~~~~~~~~~~~~~~

It is of course also possible generate input using the output of other steps.

To do this you must first define what the output of an activity looks like. This
is done in the activity defintion.

Assuming the result of `MyAct1` looks like this:

.. code-block:: json

    {
        "user": "John",
        "addresses": {
          "home": {
            "street": "Some street"
          },
          "work": {
            "street": "Some other street"
          }
        }
    }

We can define the following `outputs_spec` for this activity:

.. code-block:: yaml
   :emphasize-lines: 4-6

    activities:
    - name: MyAct1
      version: 1.0
      outputs_spec:
        name: "$.user"
        home-address: "$.addresses.home"

These specs are using the `YAQL language
<https://github.com/ativelkov/yaql/tree/stable/0.2>`_.

The above defines that any step using this activity will "expose" an usable
output to other steps that defines the `"name"` and `"home-address"` keys.

It them becomes possible to construct a workflow as below.

.. code-block:: yaml
   :emphasize-lines: 12,18,26-27,29-34

    activities:
    - name: MyAct1
      version: 1.0
      outputs_spec:
        name: "$.user"
        home-address: "$.addresses.home"
    - name: MyOtherActivity
      version: 1.0

      steps:
      - name: MyStep1
        activity: MyAct1
        input: |
            {
                "get": "sender"
            }
      - name: MyStep2
        activity: MyAct1
        input: |
            {
                "get": "recipient"
            }
      - name: MyStep3
        activity: MyOtherActivity
        requires:
        - [MyStep1, succeeded]
        - [MyStep2, succeeded]
        input: |
            {
                "sender": {{MyStep1.name}},
                "shipping-from": {{MyStep1.home-address}},
                "recipient": {{MyStep2.name}},
                "shipping-from": {{MyStep2.home-address}}
            }

It is important to note that steps that use other steps' output in their
templated input **must** define these steps as required. The decider will refuse
to load any plan that doesn't satisfy this rule.
