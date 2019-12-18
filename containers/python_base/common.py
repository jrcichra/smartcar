import os
import datetime


def isCI():
    res = os.environ.get('GITHUB_ACTIONS')
    if res == None or res == "" or res is None:
        return False
    else:
        return True


def secondsTillMidnight():
    tomorrow = datetime.datetime.now() + datetime.timedelta(1)
    midnight = datetime.datetime(year=tomorrow.year, month=tomorrow.month,
                                 day=tomorrow.day, hour=0, minute=0, second=0)
    return (midnight - datetime.datetime.now()).seconds
