[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/sportarchive/CloudProcessingEngine-Decider/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/sportarchive/CloudProcessingEngine-Decider/?branch=master) [![Build Status](https://travis-ci.org/sportarchive/CloudProcessingEngine-Decider.svg?branch=master)](https://travis-ci.org/sportarchive/CloudProcessingEngine-Decider)

## Cloud Processing Engine (CPE) Decider

### What is it ?

This is a Python implementation of a Decider for AWS SWF. SWF is an Amazon workflow service. To use SWF you need to implement a decider which makes the decisions of "what's next" in your workflow.

This daemon makes these decisions based on a Plan that you write in YAML. This plan defines your workflow and the Decider will follow your plan and will initiate the proper steps in your workflow.

### How can I use it?

You can use it for your own implementation of SWF. However this Decider is part of a broader project called CPE.

The CPE project (https://github.com/sportarchive/CloudProcessingEngine) allows you to process tasks at scale in the Cloud with the use of SWF and SQS.

### How to use it ?

You must write your plan. so head to the Decider documentation here for more info: http://sportarchive.github.io/CloudProcessingEngine-Decider

#### Install

You will need python installed on your machine.

Then you need to install the dependencies:

```
sudo ./setup.py install
```

Then you can run the script:

```
$> ./decider.py -d SADomain -t sa_validate 
usage: decider.py [-h] -d DOMAIN -t TASK_LIST [--plan_name PLAN_NAME]
                  [--plan_version PLAN_VERSION] --plan PLAN
decider.py: error: argument --plan is required
```


