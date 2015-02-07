#!/usr/bin/env python

import argparse
import logging
import os
import sys

import boto.swf.layer2 as swf
from boto.swf.exceptions import SWFTypeAlreadyExistsError, SWFDomainAlreadyExistsError

sys.path.append(
    os.path.realpath(
        os.path.join(
            os.path.dirname(__file__),
            '..'
        )
    )
)

from ct.register import register

class Worker(swf.ActivityWorker):

    version = 1.0

    def __init__(self, domain, task_list):
        self.domain = domain
        self.task_list = task_list
        super(Worker, self).__init__()

    def run(self):
        activity_task = self.poll()
        if 'activityId' in activity_task:
            print '%s: %r' % (self.task_list, activity_task)
            self.complete()
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain', required=True)
    parser.add_argument('--task_list', required=True)
    parser.add_argument('--activity', required=True)
    parser.add_argument('--version', required=True)
    args = parser.parse_args()

    register(activities=[(args.activity, args.version)])

    worker = Worker(args.domain, args.task_list)
    while worker.run(): pass


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)

    main()