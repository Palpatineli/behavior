"""algorithms for processing 1d time series data"""
from typing import Tuple

import numpy as np
from algorithm.filter.gaussian import apply_gaussian
from scipy.signal import argrelextrema

_EXTREMA_ORDER = 100
_LOW_FILTER = 1.0
_HIGH_FILTER = 0.025
_PADDING = 5.0


def old_peak_valley(trace):
    """extract unique peaks. If there are multiple peaks between two valleys only keep the
    highest"""
    max_index = next(iter(argrelextrema(trace, np.greater_equal, order=_EXTREMA_ORDER)))
    argmin = next(iter(argrelextrema(trace, np.less_equal, order=_EXTREMA_ORDER)))
    correspondence = np.searchsorted(max_index, argmin)
    extra_peaks = next(iter(correspondence[np.nonzero(np.diff(correspondence) > 1)]))
    bigger_peak = np.greater(trace[max_index[extra_peaks]], trace[max_index[extra_peaks + 1]]).astype(int)
    max_index = np.delete(max_index, extra_peaks + bigger_peak)
    max_index = max_index[np.searchsorted(max_index, argmin[0]): np.searchsorted(max_index, argmin[-1])]
    onset = np.searchsorted(argmin, max_index) - 1
    height = trace[max_index] - (trace[argmin[onset + 1]] + trace[argmin[onset]]) / 2.0
    max_index = max_index[height > 0.2]
    return max_index, argmin


def get_t_in_out(trace: np.ndarray, freq: float = 2000.0,
                 tails: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """get t_in and t_out as the time of inspiration and expiration in seconds. t_in is the time
    between dropping below baseline and rising above baseline. t_out is the time between rising
    above baseline and dropping again below the baseline.
    Args:
        trace: full respiration trace
        freq: sampling frequency of the plethysmograph
        tails: the proportion of extreme values to discard at each tail
    Returns:
        t_in, t_out
    """
    padding = int(_PADDING * freq)
    slow = apply_gaussian(trace, int(freq * _LOW_FILTER))
    fast = apply_gaussian(trace, int(freq * _HIGH_FILTER))
    # trace = trace[padding: -padding]
    normalized = (fast - slow)[padding: -padding]
    rising = next(iter(np.nonzero(np.logical_and(normalized[1:] > 0, normalized[0:-1] <= 0))))
    falling = next(iter(np.nonzero(np.logical_and(normalized[1:] <= 0, normalized[0:-1] > 0))))
    rising = rising[0: np.searchsorted(rising, falling[-1])]
    falling = falling[np.searchsorted(falling, rising[0]):]
    t_in = np.sort(rising[1:] - falling[0:-1])
    t_out = np.sort(falling - rising)
    t_in = t_in[int(len(t_in) * tails): int(len(t_in) * (1 - tails))]
    """:type: np.ndarray"""
    t_out = t_out[int(len(t_out) * tails): int(len(t_out) * (1 - tails))]
    """:type: np.ndarray"""
    return t_in / freq, t_out / freq


def get_log_ratio(a, b, x):
    return (np.log(x) - np.log(b)) / (np.log(a) - np.log(b))
