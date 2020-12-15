"""auto-generate case list for groups"""
from typing import List, Tuple, Optional, Callable, Union, Dict, Sequence
from pathlib import Path
import json
from collections import defaultdict
from datetime import datetime
from os import listdir, chdir
from os.path import join, isdir

import numpy as np
import pandas as pd
from noformat import File, isFile

from .cage_table import Animals

Real = Union[int, float]
_GENOTYPES = {0: 'unknown', 1: 'wt', 2: 'ko', 3: 'wt', 4: 'ko'}
_EXPERIMENT_DATES = [28, 42, 56]

proj_folder = Path("~/Sync/project/2016-mecp2-bumetanide").expanduser()
grouping = json.load(proj_folder.joinpath("data", "index", "grouping.json").open("r"))
res = list()
for key, value in grouping.items():
    res.append()

def _approximate(number: Real, target: Sequence[Real], tolerance: Real) -> Optional[Real]:
    target = np.asarray(target)
    index = np.searchsorted(target, [number])
    if len(index) == 1:
        index = index[0]
    if index > 0 and number - target[index - 1] <= tolerance:
        return target[index - 1]
    elif index < len(target) and target[index] - number <= tolerance:
        return target[index]
    else:
        return None


IDs = Dict[Tuple[int, int], List[Tuple[datetime, str]]]


def _decode_pheno_id(folder: str) -> IDs:
    result = defaultdict(list)  # type: Dict[Tuple[int, int], List[Tuple[datetime, str]]]
    for file_name in listdir(folder):
        if not isdir(join(folder, file_name)):
            continue
        ids = File(join(folder, file_name)).attrs['id']
        for id_str in ids:
            date = datetime.strptime(file_name, '%Y%m%d')
            result[(id_str // 1000, id_str % 1000)].append((date, join(folder, file_name)))
    return result


def _decode_emka_naming(folder: str) -> IDs:
    result = defaultdict(list)  # type: Dict[Tuple[int, int], List[Tuple[datetime, str]]]
    for file_name in listdir(folder):
        if isFile(join(folder, file_name)):
            cage_id, animal_id, exp_date_str, *postfix = file_name.split('-')
            date = datetime.strptime(exp_date_str, '%Y%m%d')
            result[(int(cage_id), int(animal_id))].append((date, join(folder, file_name)))
    return result


def _find_exp_file(index: pd.MultiIndex, cage_info: Animals, ids: IDs,
                   dates: Sequence[int], tolerance: int = 4) -> pd.DataFrame:
    result = pd.DataFrame(columns=dates, index=index)
    for case_id in ids:
        if case_id not in index:
            continue
        for exp_date, case_path in ids[case_id]:
            exp_day = _approximate((exp_date - cage_info[case_id[0]]['DOB']).days, dates, tolerance)
            if exp_day is not None:
                result.loc[case_id, exp_day] = case_path
    return result


def exp_table(folder: str, func: Callable[[str], IDs], grouping: str = config['group_config'],
              experiment_dates: List[int] = _EXPERIMENT_DATES) -> pd.DataFrame:
    """get a table of experiments done based on folder and animal_id decoder"""
    def read_grouping(struct: Dict[str, Tuple[str, str]]) -> List[Tuple[Tuple[int, int], str]]:
        return [((int(cage), int(mouse)), key) for key, value in struct.items() for cage, mouse in value]
    case_ids, groupings = zip(*read_grouping(json.load(open(grouping))))
    index, permutation = pd.MultiIndex.from_tuples(case_ids, names=('cage_id', 'animal_id')).sortlevel()
    groupings = np.asarray(groupings)[np.asarray(permutation)]
    result = _find_exp_file(index, Animals(config['animal_config']), func(folder), experiment_dates)
    result['grouping'] = groupings
    return result


def find_grouping(data_folder: str, func: Callable[[str], IDs]):
    chdir(data_folder)
    cases = [tuple(map(int, x.split('-')[0: 2])) for x in listdir(data_folder) if isdir(x)]
    cases = sorted(set(cases))
    index = pd.MultiIndex.from_tuples(cases, names=('cage_id', 'animal_id'))
    animals = Animals(config['animal_config'])
    result = _find_exp_file(index, animals, func(data_folder), _EXPERIMENT_DATES)
    genotype = [_GENOTYPES[animals[cage_id][animal_id]] for cage_id, animal_id in cases]
    result['genotype'] = genotype
    return result


def breath_exp(experiment_dates: List[int] = _EXPERIMENT_DATES, grouping: str = config['group_config']) -> pd.DataFrame:
    return exp_table(config['breath_folder'], _decode_emka_naming, grouping, experiment_dates)


def breath_grouping() -> pd.DataFrame:
    return find_grouping(config['breath_folder'], _decode_emka_naming)


def motion_exp(experiment_dates: List[int] = _EXPERIMENT_DATES, grouping: str = config['group_config']) -> pd.DataFrame:
    return exp_table(config['motion_folder'], _decode_pheno_id, grouping, experiment_dates)


def filter_by_col(table: pd.DataFrame, cols: List[Union[List[Union[str, int]], str, int]]) -> pd.DataFrame:
    """Filter a dataframe, only include the data columns listed in cols
    Args:
        table: dataframe to filter
        cols: a list of either str or int, can include a tuple of int or str. When there is a tuple,
            then the column is indexed by either item in the tuple. If multiple columns exist in the tuple,
            the left most one wins.
    Returns:
        filtered dataframe
    """
    result: List[pd.Series] = list()
    for col in cols:
        if isinstance(col, (str, int)):
            result.append(table[col])
        else:
            temp = pd.Series(np.nan, index=table.index, name=col[0])
            for col_item in col:
                if col_item in table:
                    temp[temp.isna()] = table[col_item][temp.isna()]
            result.append(temp)
    return pd.concat(result, axis=1)
