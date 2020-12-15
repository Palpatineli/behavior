"""wrap around mouse management table"""
from typing import Dict, Tuple, Union, Callable
from datetime import datetime

import openpyxl
from openpyxl.cell.cell import Cell

FILE_PATH = "/home/palpatine/Sync/project/2016-mecp2-bumetanide/data/Mouse Management.xlsx"

def _date_digest(data_in: Union[datetime, float]) -> datetime:
    if isinstance(data_in, datetime):
        return data_in
    return datetime.utcfromtimestamp((data_in - 25569) * 86400)


def _parent_digest(parent_str: str) -> Union[int, str]:
    try:
        return int(parent_str)
    except ValueError:
        return str(parent_str)


GENDER_DICT = {'♂': 'male', '♀': 'female'}
EXIST_DICT = {'✓': 'yes', '✗': 'no'}
COLUMN_NAME: Dict[str, Tuple[int, Callable]] = {
    'id': (0, int), 'strain': (2, str), 'room': (4, int), 'DOB': (16, _date_digest),
    'parent': (17, _parent_digest), 'number': (18, int), 'gender': (1, GENDER_DICT.get),
    'exist': (5, EXIST_DICT.get)}


class Cage(object):  # pylint: disable=R0903
    """manage one row of the animal table"""
    def __init__(self, mouse_list: Dict[int, int], properties: Dict[str, str]) -> None:
        self.mouse_list = mouse_list
        self.properties = properties
        self.number = properties.get('number', len(mouse_list))

    @classmethod
    def load(cls, row: Tuple[Cell, ...]):
        mouse_list = dict()  # type: Dict[int, int]
        for col_id in range(6, 16, 2):
            animal_id = row[col_id].value
            if animal_id is None:
                continue
            mouse_type = row[col_id + 1].value
            mouse_list[int(animal_id)] = int(mouse_type) if mouse_type else 0
        params = dict()
        for key, (value, processor) in COLUMN_NAME.items():
            value = row[value].value
            if value is not None:
                params[key] = processor(value)
        return cls(mouse_list, params)

    def __getitem__(self, key: Union[str, int]) -> Union[int, str, datetime]:
        if isinstance(key, int) and key in self.mouse_list:
            return self.mouse_list[key]
        elif isinstance(key, str) and key in self.properties:
            return self.properties[key]
        elif key == 'number':
            return self.number
        else:
            raise KeyError("key error in cage {} for {}".format(self.properties['id'], key))

    def __contains__(self, key: Union[str, int]) -> bool:
        return self.mouse_list.__contains__(key) or self.properties.__contains__(key) or key == 'number'

    def __len__(self) -> int:
        return len(self.mouse_list)

    def __iter__(self):
        return self.mouse_list.keys()


class Animals(object):
    """manage the whole non-breeders sheet"""
    animal_index = dict()  # type: Dict[str, str]
    data = dict()  # type: Dict[int, Cage]

    def __init__(self, file_path: str) -> None:
        table_file = openpyxl.load_workbook(file_path)
        sheet = table_file.get_sheet_by_name("nonbreeders")
        rows = sheet.iter_rows()
        next(rows)  # skip table headers
        for row in rows:
            if row[0].value is None:
                continue
            cage = Cage.load(row)
            cage_id = cage['id']
            self.data[cage_id] = cage
            self.animal_index.update({x: cage_id for x in cage.mouse_list})

    def __getitem__(self, case_id: int) -> Cage:
        return self.data[case_id]

    def __iter__(self):
        for cage_id in self.data:
            for animal in self.data[cage_id].mouse_list.items():
                yield animal


def get_case(cage_id: int, animal_id: int) -> Tuple[datetime, int]:
    """
    Args:
        cage_id: 3 digit cage id
        animal_id: may conflict
    Returns:
        (birthday, genotype)
    """
    animals = Animals(FILE_PATH)
    cage = animals[cage_id]
    return cage['DOB'], cage[animal_id]  # type: ignore
