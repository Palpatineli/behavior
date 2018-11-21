# pylint:disable=C0111
from setuptools import setup, find_packages

setup(
    name='behavior',
    version='0.1',
    packages=find_packages(exclude=['test', 'data', 'data.*', '*.test', '*.test.*', 'test.*']),
    entry_points={'gui_scripts': ['emka_conv=behavior.reader.breath:convert',
                                  'emka_save=behavior.utils:emka_save',
                                  'motion_conv=behavior.reader.motion:convert']},
    author='Keji Li',
    author_email='mail@keji.li',
    install_requires=['numpy', 'scipy', 'pandas', 'openpyxl', 'numba', 'noformat', 'uifunc'],
    extra_requires={'plot': ['matplotlib', 'seaborn']},
    description='''
        Analysis natural behaviors of mice. Including: plethysmograph, plus maze, and locomotion.
        Acceptable formats include:
            Plethysmograph: Trace copied from Emka as txt file,
            Plus Maze: I record my own (pyMotion) using opencv3
            Locomotion: 1D from Phenomaster exported csv file
    '''
)
