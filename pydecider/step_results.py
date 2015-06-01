class ActivityStepResult(object):

    __slots__ = ('name', 'activity', 'activity_input')

    def __init__(self, name, activity, activity_input):
        self.name = name
        self.activity = activity
        self.activity_input = activity_input


class TemplatedStepResult(object):
    pass
