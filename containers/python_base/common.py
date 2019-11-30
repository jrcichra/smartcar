import os


def isCI():
    res = os.environ.get('GITHUB_ACTIONS')
    if res == None:
        return False
    else:
        return True
