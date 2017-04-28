"""wrap around mouse management table"""
from typing import Sequence

import openpyxl

FILE_PATH = "/home/palpatine/Dropbox/project/animal-management/Mouse Management.xlsx"


def is_non_str_sequence(x):
    return isinstance(x, Sequence) and not isinstance(x, str)


class Animals(object):
    """manage the whole non-breeders sheet"""
    col_name = {'id': 0, 'strain': 2, 'room': 4, 'DOB': 16, 'parent': 17}
    GENDER_DICT = {'♂': 'male', '♀': 'female'}
    EXIST_DICT = {'✓': 'yes', '✗': 'no'}

    def __init__(self, file_path):
        table_file = openpyxl.load_workbook(file_path)
        sheet = table_file.get_sheet_by_name("nonbreeders")
        self.data = dict()
        rows = sheet.iter_rows()
        next(rows)
        for row in rows:
            if row[0].value is None:
                continue
            cage = Cage(Animals.process_mouse_ids(row), Animals.process_line(row))
            self.data[cage['id']] = cage

    @staticmethod
    def process_mouse_ids(row):
        mouse_list = dict()
        for col_id in range(6, 16, 2):
            animal_id = row[col_id].value
            if animal_id is None:
                continue
            mouse_type = row[col_id + 1].value
            if mouse_type is None:
                mouse_list[int(animal_id)] = 0
            else:
                mouse_list[int(animal_id)] = int(mouse_type)
        return mouse_list

    @staticmethod
    def process_line(row):
        result = dict()
        for key, value in Animals.col_name.items():
            result[key] = row[value].value
        result['gender'] = Animals.GENDER_DICT[row[1].value]
        result['exist'] = Animals.EXIST_DICT[row[5].value]
        if row[18].value is not None:
            result['number'] = int(row[18].value)
        return result

    def __getitem__(self, animal_id):
        if is_non_str_sequence(animal_id):
            if is_non_str_sequence(animal_id[0]):
                return [self.data[animal[0]][animal[1]] for animal in animal_id]
            else:
                return [self.data[animal] for animal in animal_id]
        else:
            return self.data[animal_id]


class Cage(object):  # pylint: disable=R0903
    """manage one row of the animal table"""

    def __init__(self, mouse_list, properties):
        self.mouse_list = mouse_list
        self.properties = properties
        self.number = properties.get('number', len(mouse_list))

    def __getitem__(self, key):
        if key in self.mouse_list:
            new_dict = self.properties.copy()
            new_dict['type'] = self.mouse_list[key]
            return new_dict
        elif key in self.properties:
            return self.properties[key]
        elif key == 'number':
            return self.number
        else:
            raise KeyError("key error in cage {} for {}".format(self.properties['id'], key))

    def __contains__(self, key):
        return self.mouse_list.__contains__[key] or self.properties.__contains__[key] \
               or key == 'number'

    def __len__(self):
        return len(self.mouse_list)

    def __iter__(self):
        return self.mouse_list.keys()
