import numpy as np


def boolean2index(x):
    start = np.flatnonzero(np.logical_and(x[1:], np.logical_not(x[0: -1]))) + 1
    if x[0]:
        start = np.hstack([0, start])
    end = np.flatnonzero(np.logical_and(np.logical_not(x[1:]), x[0: -1])) + 1
    if x[-1]:
        end = np.hstack([end, len(x)])
    return start, end - start
