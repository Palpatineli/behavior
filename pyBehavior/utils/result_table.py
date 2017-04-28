"""auto-generate case list for groups"""
import json
from datetime import datetime
from os import listdir
from os.path import join
from typing import List, Tuple, Optional, Callable, Union

import numpy as np
import pandas as pd
from noformat import File

from .cage_table import Animals

_BREATH_FOLDER = "/home/palpatine/Dropbox/data/2016-natural-behavior/emka"
_MOTION_FOLDER = "/home/palpatine/Dropbox/data/2016-natural-behavior/phenomaster"
_MAZE_FOLDER = "/home/palpatine/Dropbox/data/2016-natural-behavior/maze"
_ANIMAL_CONFIG = "/home/palpatine/Dropbox/project/animal-management/Mouse Management.xlsx"
_GROUP_CONFIG = "/home/palpatine/Dropbox/data/2016-mecp2-drugs/animals.json"

Real = Union[int, float]


def read_grouping(grouping: dict) -> List[Tuple[int, int, str]]:
    result = list()
    for key, value in grouping.items():
        for cage_id, mouse_id in value:
            result.append((int(cage_id), int(mouse_id), key))
    return result


def approximate(number: Real, target: List[Real], tolerance: Real) -> Optional[Real]:
    index = np.searchsorted(target, [number])
    if len(index) == 1:
        index = index[0]
    if index > 0 and number - target[index - 1] <= tolerance:
        return target[index - 1]
    elif index < len(target) and target[index] - number <= tolerance:
        return target[index]
    else:
        return None


def _decode_pheno_id(folder_name: str, file_name: str) -> List[Tuple[int, int, datetime, str]]:
    result = list()
    for id_str in File(join(folder_name, file_name)).attrs['id']:
        result.append((id_str // 1000, id_str % 1000, datetime.strptime(file_name, '%Y%m%d'),
                       file_name))
    return result


def _decode_emka_naming(folder_name: str, file_name: str) -> List[Tuple[int, int, datetime, str]]:
    del folder_name
    cage_id, animal_id, exp_date_str, *postfix = file_name.split('-')
    return [(int(cage_id), int(animal_id), datetime.strptime(exp_date_str, '%Y%m%d'), file_name)]


def exp_table(file_path: str, folder: str,
              func: Callable[[str, str], List[Tuple[int, int, datetime, str]]]) -> pd.DataFrame:
    """get a table of experiments done based on folder and animal_id decoder"""
    cage_ids, animal_ids, groupings = zip(*read_grouping(json.load(open(file_path))))
    index = pd.MultiIndex.from_tuples(list(zip(cage_ids, animal_ids)), names=('cage_id', 'animal_id'))
    exp_dates = [28, 36, 42, 56]
    result = pd.DataFrame(columns=['grouping'] + exp_dates, index=index)
    result['grouping'] = groupings
    animals = Animals(_ANIMAL_CONFIG)
    ids = list()
    for file_name in listdir(folder):
        ids.extend(func(folder, file_name))
    for cage_id, animal_id, exp_date, case_path in ids:
        if (cage_id, animal_id) not in index:
            continue
        exp_day = approximate((exp_date - animals[cage_id]['DOB']).days, exp_dates, 4)
        if exp_day is not None:
            result.ix[(cage_id, animal_id), exp_day] = join(folder, case_path)
    return result


def breath_exp() -> pd.DataFrame:
    return exp_table(_GROUP_CONFIG, _BREATH_FOLDER, _decode_emka_naming)


def motion_exp() -> pd.DataFrame:
    return exp_table(_GROUP_CONFIG, _MOTION_FOLDER, _decode_pheno_id)


def filter_by_col(table: pd.DataFrame, cols: List[Union[List, str, int]]) -> pd.DataFrame:
    result = table.copy()  # type: pd.DataFrame
    new_cols = list()
    for col in cols:
        if (isinstance(col, List) or isinstance(col, Tuple)) and len(col) > 1:
            temp = table[col[0]]
            for item_idx in col[1:]:
                open_idx = temp.isnull()
                temp[open_idx] = result[item_idx][open_idx]
                result.drop(item_idx, 1)
            result[col[0]] = temp
            new_cols.append(col[0])
        else:
            new_cols.append(col)
    result = result.loc[:, new_cols]
    return result.dropna()
