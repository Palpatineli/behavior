"""read and analyze PhenoMaster file"""
from os import listdir, makedirs, chdir, rename
from os.path import join, isfile, splitext
from collections import defaultdict
from typing import Iterable, Tuple, Sequence, Generator
import csv

import noformat
import numpy as np
import pandas as pd
from uifunc import FolderSelector


def read_time(time_str: str) -> pd.DateOffset:
    hour, minute = time_str.split(':')
    return pd.DateOffset(hours=int(hour), minutes=int(minute))


def read_header(table: Iterable) -> list:
    animal_ids = []
    for row in table:
        if row:
            animal_ids.append(int(row[1]))
    return animal_ids


def read_main_table(table: Iterable, animal_ids: list) -> pd.DataFrame:
    """read exported phenomaster table and convert it to pandas DataFrame with mice in columns and
    per minute readings in rows"""
    header = pd.MultiIndex(levels=[animal_ids, ['XT', 'XA', 'XF']],
                           labels=[np.repeat(range(len(animal_ids)), 3),
                                   np.tile(range(3), [len(animal_ids)])])
    data = []
    current_date = None
    timestamps = []
    row_length = 2 + len(animal_ids) * 3
    for row in table:
        if row[0]:
            current_date = pd.to_datetime(row[0], dayfirst=True)
        timestamps.append(current_date + read_time(row[1]))
        data.append(list(map(int, row[2:row_length])))
    time_idx = pd.Index(data=timestamps, name='time')
    return pd.DataFrame(data=np.array(data, dtype='uint16'), index=time_idx, columns=header)


def read(lines: Sequence[str]) -> pd.DataFrame:
    start_idx = 2  # find the start of main table
    for start_idx in range(2, 20):
        if len(lines[start_idx]) < 1:
            break
    animal_ids = read_header(csv.reader(lines[3: start_idx], delimiter=';'))
    return read_main_table(csv.reader(lines[start_idx + 4: -2], delimiter=';'), animal_ids)


def find_new_file(data_folder: str, ext: str = '.CSV') -> Generator[Tuple[str, str], None, None]:
    chdir(data_folder)
    for case_name in listdir(data_folder):
        if isfile(join(case_name, case_name + ext)) and not isfile(join(case_name, 'value.msg')):
            yield join(data_folder, case_name, case_name + ext), case_name


def rearrange(data_folder: str) -> None:
    chdir(data_folder)
    files = defaultdict(list)
    for file_name in listdir(data_folder):
        if splitext(file_name)[-1][1:].lower() not in ('csv', 'alyset', 'dat', 'par', 'raw'):
            continue
        if isfile(file_name):
            files[splitext(file_name)[0]].append(file_name)
    for folder, file_names in files.items():
        makedirs(join(data_folder, folder), exist_ok=True)
        for file_name in file_names:
            rename(file_name, join(folder, file_name))


@FolderSelector
def convert(folder_name: str) -> None:
    rearrange(folder_name)
    for source_name, target_name in find_new_file(folder_name):
        with open(source_name, 'r') as source_file, noformat.File(target_name, 'w+') as outfile:
            data = read(source_file.read().split('\n'))
            outfile.attrs['id'] = [int(identity) for identity in data.columns.levels[0]]
            outfile.attrs['date'] = str(data.index[0]).split()[0]
            outfile['value'] = data


def rename_col(x: noformat.File, old_name: int, new_name: int) -> noformat.File:
    ids = x.attrs['id']
    ids[ids.index(old_name)] = new_name
    x.attrs['id'] = ids
    data = x['value']
    id_level, type_level = data.columns.levels
    id_level = list(id_level)
    id_level[id_level.index(old_name)] = new_name
    data.columns.set_levels([id_level, type_level], inplace=True)
    x['value'] = data
    return x
