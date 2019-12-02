import os


def isCI():
    res = os.environ.get('GITHUB_ACTIONS')
    if res == None or res == "":
        return False
    else:
        return True
