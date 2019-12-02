import os


def isCI():
    res = os.environ.get('GITHUB_ACTIONS')
    if res == None or res == "" or res is None:
        return False
    else:
        return True
