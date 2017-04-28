"""read pasted plethysmograph trace file from emka"""
import time
from itertools import islice
from os import listdir
from os.path import isdir, join, splitext
from typing import Iterable, Tuple

import noformat
import numpy as np
from plptn.ui import folder_name


def _extract_time(value: str) -> float:
    time_in_s, time_in_ms = value.split('.')
    time_fmt = "%b %d, %Y - %I:%M:%S %p"
    return time.mktime(time.strptime(time_in_s, time_fmt)) + float(time_in_ms) / 1000


class EmkaDecoder(object):
    """decode the pasted emka raw data, assuming a one big paste"""
    freq = 2000.0

    def __init__(self, lines):
        self.start_time = None
        self._data = []
        self.lines = lines
        self.line_reader = self.header_reader
        for line in self.lines:
            self.line_reader(line)

    def header_reader(self, line):
        if line[0:4] == "Date" and line[17:22] == 'first':
            print(line.split('\t')[1].strip())
            self.start_time = _extract_time(line.split('\t')[1].strip())
            self.lines = islice(self.lines, 3, None)
            self.line_reader = self.body_reader

    def body_reader(self, line: str):
        if line.startswith('Date'):  # last sample timestamp, wait for next
            self.line_reader = self.header_reader
        elif line.strip() == '':
            return
        else:
            try:
                self._data.append(float(line[13:21]))
            except ValueError:
                return

    @property
    def data(self):
        return np.array(self._data, dtype='float32')


def find_new_files(data_folder: str, ext: str = '.raw') -> Iterable[Tuple[str, str], None, None]:
    file_list = listdir(data_folder)
    for file_name in file_list:
        file_name_split = splitext(file_name)
        source_name = join(data_folder, file_name)
        target_name = join(data_folder, 'converted', file_name_split[0])
        if file_name_split[-1] == ext and (not isdir(target_name)):
            yield source_name, target_name


def convert():
    data_folder = folder_name()
    for file_name, target_name in find_new_files(data_folder):
        with open(file_name, 'r') as source, noformat.File(target_name, 'w-') as output:
            decoder = EmkaDecoder(source.read().split('\n'))
            output.attrs['start'] = decoder.start_time
            output.attrs['freq'] = decoder.freq
            output['value'] = decoder.data
