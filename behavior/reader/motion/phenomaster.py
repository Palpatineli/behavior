from typing import List, Dict, Sequence, Iterable
from os import makedirs, scandir, DirEntry
from os.path import splitext, join, dirname
import numpy as np

from uifunc import FolderSelector

@FolderSelector  # only public interface
def convert(folder_name: str) -> None:
    for file in scandir(folder_name):
        if file.is_file() and splitext(file.name)[-1][1:].lower() in ("csv", "raw"):
            convert_data(file)
        elif file.is_file() and splitext(file.name)[-1].lower().startswith('.txt'):
            if file.stat().st_size > 1E7:
                convert_data(file)

def convert_data(file_entry: DirEntry) -> None:
    """convert csv data to pandas msgpack"""
    with open(file_entry.path, 'r') as fp:
        try:
            data = read(fp.read())
        except IndexError as e:
            print(file_entry.name)
            raise e
    for animal_id, animal_data in data.items():
        base_folder = dirname(dirname(file_entry.path))
        makedirs(join(base_folder, animal_id), exist_ok=True)
        np.savez_compressed(join(base_folder, animal_id, splitext(file_entry.name)[0]), **animal_data)

def read(csv_file: str) -> Dict[str, Dict[str, np.ndarray]]:
    lines = csv_file.split('\n')
    animal_ids: List[str] = list()
    cage_ids: List[int] = list()
    for line in lines[3: 8]:
        if len(line) < 1:
            break
        cage_id, animal_id = line.split(';')[0: 2]
        cage_ids.append(int(cage_id))
        animal_ids.append(animal_id)
    animal_no = len(animal_ids)
    if lines[4 + animal_no].split(';')[2].startswith("Animal No"):  # saved as long form
        return dict(zip(animal_ids, _read_long_form(lines[4 + animal_no:], cage_ids)))
    else:  # saved as wide form
        try:
            return dict(zip(animal_ids, _read_wide_form(lines[4 + animal_no:], cage_ids)))
        except ValueError as e:
            print("animals: ", animal_ids)
            print("cages: ", cage_ids)
            raise e

def _read_long_form(lines: Sequence[str], cage_ids: List[int]) -> Iterable[Dict[str, np.ndarray]]:
    results: List[List[List[int]]] = [list() for _ in range(max(cage_ids))]
    time_list: List[int] = list()
    starting_cage = min(cage_ids) - 1
    for line_str in lines[2:]:
        line = line_str.split(';')
        if not any(line):
            continue
        cage_id = int(line[3]) - 1
        if cage_id == starting_cage:
            time_list.append(_read_time(line[1]))
        try:
            results[cage_id].append([int(x) for x in line[4: 7]])
        except IndexError as e:
            print(line, len(results), cage_id)
            raise e
    time = np.array(time_list)
    time[time < time[0]] += 1440
    for result in results:
        if len(result) > 0:
            result = np.asarray(result).T
            yield {'XT': result[0], 'XA': result[1], 'XF': result[2], 'time': time}

def _read_wide_form(lines: Sequence[str], cage_ids: List[int]) -> Iterable[Dict[str, np.ndarray]]:
    time_list: List[int] = list()
    result: List[List[int]] = list()
    animal_no = len(cage_ids)
    for line_str in lines[3:]:
        line = line_str.split(';')
        if all([not x for x in line]):
            continue
        time_list.append(_read_time(line[1]))
        result.append([int(x) for x in line[2: animal_no * 3 + 2]])
    results = iter(np.array(result).T)
    time = np.array(time_list)
    time[time < time[0]] += 1440
    for _ in range(animal_no):
        yield {'XT': next(results), 'XA': next(results), 'XF': next(results), 'time': time}

def _read_time(time_str: str) -> int:
    hour, minute = time_str.split(':')
    return int(hour) * 60 + int(minute)
