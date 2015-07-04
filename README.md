[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/sportarchive/CloudTranscode-Decider/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/sportarchive/CloudTranscode-Decider/?branch=master) [![Build Status](https://travis-ci.org/sportarchive/CloudTranscode-Decider.svg?branch=master)](https://travis-ci.org/sportarchive/CloudTranscode-Decider)

## Cloud Processing Engine (CPE) Decider

### What is it ?

CPE is using AWS SWF cloud service to manage workflows. Workflows are chains of Activities that are processed in the order you decide.

The decider perform this decisions dynamically and initiate the "next step" of your workflows.

### How to use it ?

You workflow is defined in a YAML file called a "plan".

Each plan defines a series of steps. Each step can be handled by a type of activity. Activities are piece of code that listen on a particular queue (Activity TaskList) for incoming job to do.

The Decider reads your plan and based on the SWF decision task (event) that comes in (workflow start, activity completed, etc) will perform the proper step:
   - Start a workflow
   - Initiate an activity
   - End the workflow

### Plan format details

The plan format details can be found here: 
