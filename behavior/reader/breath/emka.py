"""read pasted plethysmograph trace file from emka"""
from typing import Tuple, Generator, List
import time
from itertools import islice
from os import scandir, chdir
from os.path import splitext

import noformat
import numpy as np
from uifunc import FolderSelector


def _extract_time(value: str) -> float:
    time_in_s, time_in_ms = value.split('.')
    time_fmt = "%b %d, %Y - %I:%M:%S %p"
    return time.mktime(time.strptime(time_in_s, time_fmt)) + float(time_in_ms) / 1000


class EmkaDecoder(object):
    """decode the pasted emka raw data, assuming a one big paste"""
    freq = 2000.0

    def __init__(self, lines):
        self.start_time = None
        self._data: List[float] = list()
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


def find_new_files(data_folder: str, ext: List[str] = ['.raw', '.txt']) -> Generator[Tuple[str, str], None, None]:
    file_list = scandir(data_folder)
    chdir(data_folder)
    for file_entry in file_list:
        file_base, file_ext = splitext(file_entry.path)
        source_name = file_entry.path
        target_name = file_base
        if file_ext in ext and file_entry.is_file() and ((file_entry.stat().st_size >> 20) > 25):
            yield source_name, target_name


@FolderSelector
def convert(folder_name: str):
    for file_name, target_name in find_new_files(folder_name):
        try:
            with open(file_name, 'r') as source, noformat.File(target_name, 'w-') as output:
                decoder = EmkaDecoder(source.read().split('\n'))
                output.attrs['start'] = decoder.start_time
                output.attrs['freq'] = decoder.freq
                output['value'] = decoder.data
        except IOError as e:
            print(e)
