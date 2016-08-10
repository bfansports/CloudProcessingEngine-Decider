from __future__ import (
    absolute_import,
    division,
    print_function
)

import logging

import boto.swf.layer2 as swf
from boto.swf.exceptions import (
    SWFTypeAlreadyExistsError,
    SWFDomainAlreadyExistsError,
)

_LOGGER = logging.getLogger(__name__)


def register(domain='test', workflows=(), activities=()):
    registerables = []
    registerables.append(swf.Domain(name=domain))

    for (workflow_name, workflow_version,
         default_execution_start_to_close_timeout,
         default_task_start_to_close_timeout) in workflows:
        registerables.append(
            swf.WorkflowType(domain=domain,
                             name=workflow_name,
                             default_execution_start_to_close_timeout=default_execution_start_to_close_timeout,
                             default_task_start_to_close_timeout=default_task_start_to_close_timeout,
                             version=workflow_version,
                             task_list='default')
        )

    for (activity_name, activity_version) in activities:
        registerables.append(
            swf.ActivityType(domain=domain,
                             name=activity_name,
                             version=activity_version,
                             task_list='default')
        )

    for swf_entity in registerables:
        try:
            swf_entity.register()
            _LOGGER.debug('%r registered successfully', swf_entity.name)
        except (SWFDomainAlreadyExistsError, SWFTypeAlreadyExistsError):
            _LOGGER.warning('%s %r already exists',
                            swf_entity.__class__.__name__,
                            swf_entity.name)
