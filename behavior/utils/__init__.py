from .cage_table import get_case
try:
    from .main import emka_save
except (ValueError, ImportError):
    emka_save = None

__all__ = ['get_case']
