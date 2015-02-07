#!/usr/bin/env python

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

from ct.register import register
from ct.decider import Decider
from ct.workspace import Plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--domain', required=True)
    parser.add_argument('--task_list', required=True)
    parser.add_argument('--workflow', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--plan', required=True)
    args = parser.parse_args()

    with open(args.plan) as f:
        p = Plan.load(yaml.load(f))

    logging.info('Loaded plan %r', p)

    register(domain=args.domain,
             workflows=((args.workflow, args.version),))

    d = Decider(p, domain=args.domain, task_list=args.task_list)
    while d.run(): pass


if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    main()