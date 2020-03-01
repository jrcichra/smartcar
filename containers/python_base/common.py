import os
import datetime


def isCI():
    res = os.environ.get('GITHUB_ACTIONS')
    host = os.environ.get('HOSTNAME')
    if (res == None or res == "" or res is None) and host != 'justin-3900x':
        print("We're not in CI")
        return False
    else:
        print("We're in CI")
        return True


def secondsTillMidnight():
    tomorrow = datetime.datetime.now() + datetime.timedelta(1)
    midnight = datetime.datetime(year=tomorrow.year, month=tomorrow.month,
                                 day=tomorrow.day, hour=0, minute=0, second=0)
    return (midnight - datetime.datetime.now()).seconds
