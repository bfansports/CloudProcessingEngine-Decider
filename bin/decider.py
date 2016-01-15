#!/usr/bin/env python

from __future__ import (
    absolute_import,
    division,
    print_function
)

import argparse
import logging
import os
import sys

import yaml

sys.path.append(
    os.path.realpath(
        os.path.join(
            os.path.dirname(__file__),
            '..'
        )
    )
)

from pydecider.register import register
from pydecider.plan import Plan
from pydecider.swf_decider import SWFDecider as Decider

def main():
    parser = argparse.ArgumentParser(description='Generic SWF Decider daemon. Read you Plan.yaml and process your workflow accordingly.')
    parser.add_argument('-d', '--domain', required=True, help='The SWF domain for your workflow')
    parser.add_argument('-t', '--task_list', required=True, help='The Decision TaskList your decider will listen to')
    parser.add_argument('--plan', required=True, help='The location of your Plan file')
    parser.add_argument('--output_queue', required=False, help='SQS queue to output updates to')
    parser.add_argument('--plan_name', required=False, help='If you want to override the plan name in your Plan file')
    parser.add_argument('--plan_version', required=False, help='If you want to override the plan version in your Plan file')
    parser.add_argument('--log_file', required=False, help='Location of the log file')
    args = parser.parse_args()

    log_file = "/var/tmp/logs/cpe/decider.log"
    if args.log_file:
        log_file = args.log_file
    logging.basicConfig(level=logging.DEBUG,
                        filename=log_file)

    # Load the main plan data
    with open(args.plan) as f:
        plan_data = yaml.load(f)

    if args.plan_name:
        plan_data['name'] = args.plan_name
    if args.plan_version:
        plan_data['version'] = args.plan_version

    # Construct the plan
    p = Plan.from_data(plan_data)
    logging.info('Loaded plan %r', p)

    # Make sure the plan is registered in SWF
    register(domain=args.domain,
             workflows=((p.name, p.version),))

    if 'OUTPUT_QUEUE' in os.environ:
        output_queue = os.environ['OUTPUT_QUEUE']
    elif (args.output_queue is not None and
          args.output_queue != ""):
        output_queue = args.output_queue
    else:
        raise Exception("No 'OUTPUT_QUEUE' provided!");
        
    d = Decider(domain=args.domain, task_list=args.task_list, plan=p, output_queue=args.output_queue)

    while d.run():
        pass

if __name__ == '__main__':
    main()
