import os


def isCI():
    res = os.environ(['GITHUB_ACTIONS'])
    if res is not None:
        print("I just did a check and I am indeed in a CI environment.")
    return res
