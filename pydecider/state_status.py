from __future__ import absolute_import

import enum


class StateStatus(enum.Enum):
    """Enumeration of the possible :class:`State` statuses."""
    #: Pristin empty status.
    init = 0
    #: Input has been set and Steps are running or ready.
    running = 1
    #: All Steps are in the completed status or one was aborted.
    completed = 2
    #: All steps completed as successful.
    succeeded = completed | 4
    #: Step completed in failure.
    failed = completed | 8

    def means(self, status):
        # E1101: Instance of 'StateStatus' has no 'value' member
        # pylint: disable=E1101
        return (self.value & status.value) == status.value


class StepStateStatus(enum.Enum):
    """Enumeration of the possible :class:`StepState` statuses."""

    #: Step is not started yet (may be waiting on dependencies).
    pending = 0
    #: Step is ready to be started
    ready = 1
    #: Step is running
    running = 2
    #: Step was either completed (sucess OR failure) or skipped.
    completed = 4
    #: Step resulted in a permanent error.
    aborted = 8
    #: Step completed as successful.
    succeeded = completed | 16
    #: Step completed in failure.
    failed = completed | 32
    #: Step was skipped (will not be run).
    skipped = completed | 64

    def means(self, status):
        # E1101: Instance of 'StepStateStatus' has no 'value' member
        # pylint: disable=E1101
        return (self.value & status.value) == status.value
