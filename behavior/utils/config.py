import json
from typing import Callable, Union, TypeVar
from pkg_resources import resource_stream, Requirement
from os.path import expanduser
T = TypeVar('T')


def walk_dict(in_data: Union[dict, list], func: Callable[[T], T]) -> dict:
    if isinstance(in_data, dict):
        for key, value in in_data.items():
            in_data[key] = walk_dict(value, func)
    elif isinstance(in_data, list):
        for idx, value in enumerate(in_data):
            in_data[idx] = walk_dict(value, func)
    else:
        in_data = func(in_data)
    return in_data


_FILTERS = {str: expanduser, bytes: expanduser}


# noinspection PyTypeChecker
def item_filter(in_data: T) -> T:
    if type(in_data) in _FILTERS:
        return _FILTERS[type(in_data)](in_data)


config_stream = resource_stream(Requirement.parse('behavior'), 'behavior/utils/behavior.json')
config = walk_dict(json.loads(config_stream.read().decode('utf-8')), item_filter)
