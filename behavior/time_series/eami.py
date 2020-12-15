from collections.abc import MutableMapping
from typing import Sequence, Tuple, Union, List

import numpy as np
from scipy.signal import filtfilt, butter
from matplotlib import pyplot as plt
from matplotlib.figure import Figure
import seaborn as sns
sns.set()

from .algorithm import boolean2index

FILTER_ORDER = 1
SAMPLE_FREQ = 2000  # for emka whole body plethysmograph
Rangef = Tuple[float, float]


def _get_filter_cutoff(ratio: Union[float, np.ndarray, List[float]], freq_range: Rangef) -> np.ndarray:
    return np.exp(np.sum(np.log(freq_range) * np.vstack([ratio, np.subtract(1, ratio)]).T, 1))


def _apply(x: np.ndarray, cutoff: Union[Sequence[float], float], filter_type: str) -> np.ndarray:
    return filtfilt(*butter(FILTER_ORDER, np.divide(cutoff, SAMPLE_FREQ), filter_type), x)


def _energy(x: np.ndarray, band: Rangef) -> np.ndarray:
    return np.abs(_apply(_apply(x, band[0], 'highpass') ** 2, band[1], 'lowpass'))


# noinspection PyPep8Naming
def eAMI(trace: np.ndarray, freq_range: Rangef = (2.0, 20.0)) -> np.ndarray:
    CUTOFF_LEVELS = [0.90309, 2.30103, 0.75]
    ENVELOP_CUTOFF, *BAND_CUTOFF = _get_filter_cutoff(CUTOFF_LEVELS, freq_range)
    signal = _apply(trace, freq_range, 'bandpass')
    envelope = _apply(np.abs(signal), ENVELOP_CUTOFF, 'lowpass')
    result = _energy(envelope, BAND_CUTOFF) / _energy(signal, BAND_CUTOFF)  # type: np.ndarray
    return result


def visualize_eami(x, threshold=0.3, duration_threshold=1000) -> Figure:
    result = eAMI(x, freq_range=(2, 20))
    time = np.arange(len(x)) / 2000
    fig, ax = plt.subplots()
    raw = ax.plot(time, x - x.mean(), 'b')[0]
    eami = ax.plot(time, np.minimum(result, 2.0), 'g')[0]
    threshold_line = ax.plot((0, len(x) / 2000), [threshold] * 2, 'r')[0]
    triggered = np.zeros(len(x))
    idx, duration = boolean2index(result > threshold)
    idx = idx[duration > duration_threshold]
    duration = duration[duration > duration_threshold]
    for start, end in zip(idx, idx + duration):
        triggered[start: end] = min(threshold * 1.5, 1.0)
    pauses = ax.plot(time, triggered, 'cyan')[0]
    ax.set_xlabel('time (s)')
    ax.set_ylabel('air flow / eami score (a.u.)')
    ax.legend([raw, eami, threshold_line, pauses], ["raw traces", "eAMI score", "threshold", "detected pauses"])
    fig.show()
    return fig


def pause_count(data: MutableMapping, eami_thresh: int = 0.5, length_thresh: int = 600) -> np.int64:
    """calcualte breath pause frequency with eAMI.
    Args:
        data: a 1-D DataFrame with raw breath trace
        eami_thresh: threshold of eami value for abnormality detection
        length_thresh: threshold in ms for pause, pauses shorter then this are not counted
    Returns:
        integer for pause connt
    """
    _, length = boolean2index(eAMI(data['value']) > eami_thresh)
    return np.count_nonzero(np.greater(length, length_thresh))
