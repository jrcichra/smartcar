import os


def isCI():
    res = os.environ.get('GITHUB_ACTIONS')
    print("isCI = {}".format(res))
    if res is None:
        return False
    else:
        return True
