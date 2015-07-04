[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/sportarchive/CloudTranscode-Decider/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/sportarchive/CloudTranscode-Decider/?branch=master) [![Build Status](https://travis-ci.org/sportarchive/CloudTranscode-Decider.svg?branch=master)](https://travis-ci.org/sportarchive/CloudTranscode-Decider)

## Cloud Processing Engine (CPE) Decider

### What is it ?

The CPE project (https://github.com/sportarchive/CloudProcessingEngine) is using the AWS SWF cloud service to manage workflows. Workflows are chains of Activities that are processed in the order you decide.

The decider perform this decisions dynamically and initiate the "next step" of your workflows.

### How to use it ?

See the decider documentation here: http://sportarchive.github.io/CloudTranscode-Decider/

You need to define your Decider plan so the decider knows how to run your workflow.
