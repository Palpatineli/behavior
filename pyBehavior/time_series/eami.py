from collections.abc import MutableMapping
from typing import Sequence, Tuple, Union, List

import numpy as np
from scipy.signal import filtfilt, butter

from .algorithm import boolean2index

FILTER_ORDER = 1
SAMPLE_FREQ = 2000  # for emka whole body plethysmograph


def _get_filter_cutoff(ratio: Union[float, np.ndarray, List[float]], freq_range: Tuple[float, float]) -> np.ndarray:
    return np.exp(np.sum(np.log(freq_range) * np.vstack([ratio, np.subtract(1, ratio)]).T, 1))


def _apply(x: np.ndarray, cutoff: Union[Sequence[float], float], filter_type: str) -> np.ndarray:
    return filtfilt(*butter(FILTER_ORDER, np.divide(cutoff, SAMPLE_FREQ), filter_type), x)


def _energy(x: np.ndarray, band: Tuple[float, float]) -> np.ndarray:
    return np.abs(_apply(_apply(x, band[0], 'highpass') ** 2, band[1], 'lowpass'))


# noinspection PyPep8Naming
def eAMI(trace: np.ndarray, freq_range: Tuple[float, float] = (2.0, 20.0)) -> np.ndarray:
    CUTOFF_LEVELS = [0.90309, 2.30103, 0.75]
    ENVELOP_CUTOFF, *BAND_CUTOFF = _get_filter_cutoff(CUTOFF_LEVELS, freq_range)
    signal = _apply(trace, freq_range, 'bandpass')
    envelope = _apply(np.abs(signal), ENVELOP_CUTOFF, 'lowpass')
    result = _energy(envelope, BAND_CUTOFF) / _energy(signal, BAND_CUTOFF)  # type: np.ndarray
    return result


def visualize_eami(x, threshold=0.3, duration_threshold=1000):
    try:
        from matplotlib import pyplot as plt
        import seaborn
        del seaborn
    except ImportError as e:
        plt, seaborn = None, None
        del plt, seaborn
        raise e
    result = eAMI(x, freq_range=(2, 20))
    plt.plot(x - x.mean(), 'b')
    plt.plot(np.minimum(result, 2.0), 'g')
    plt.plot((0, len(x)), [threshold] * 2, 'r')
    triggered = np.zeros(len(x))
    idx, duration = boolean2index(result > threshold)
    idx = idx[duration > duration_threshold]
    duration = duration[duration > duration_threshold]
    for start, end in zip(idx, idx + duration):
        triggered[start: end] = min(threshold * 1.5, 1.0)
    plt.plot(triggered, 'cyan')


def pause_freq(file: MutableMapping, eami_threshold: int = 0.5,
               length_threshold: int = 600) -> np.int64:
    _, length = boolean2index(eAMI(file['value']) > eami_threshold)
    return np.count_nonzero(np.greater(length, length_threshold))
