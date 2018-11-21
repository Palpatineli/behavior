from typing import Optional
from time import time, sleep
import ctypes
from ctypes import c_size_t, sizeof, c_wchar_p, c_wchar, get_errno
from ctypes.wintypes import (HGLOBAL, LPVOID, DWORD, LPCSTR, INT, HWND,
                             HINSTANCE, HMENU, BOOL, UINT, HANDLE)

windll = ctypes.windll
msvcrt = ctypes.CDLL('msvcrt')

class CheckedCall(object):
    def __init__(self, f):
        super(CheckedCall, self).__setattr__("f", f)

    def __call__(self, *args):
        ret = self.f(*args)
        if not ret and get_errno():
            raise PyperclipWindowsException("Error calling " + self.f.__name__)
        return ret

    def __setattr__(self, key, value):
        setattr(self.f, key, value)

safeCreateWindowExA = CheckedCall(windll.user32.CreateWindowExA)
safeCreateWindowExA.argtypes = [DWORD, LPCSTR, LPCSTR, DWORD, INT, INT, INT, INT, HWND, HMENU, HINSTANCE, LPVOID]
safeCreateWindowExA.restype = HWND

safeDestroyWindow = CheckedCall(windll.user32.DestroyWindow)
safeDestroyWindow.argtypes = [HWND]
safeDestroyWindow.restype = BOOL

OpenClipboard = windll.user32.OpenClipboard
OpenClipboard.argtypes = [HWND]
OpenClipboard.restype = BOOL

GetClipboardSequenceNumber = windll.user32.GetClipboardSequenceNumber
GetClipboardSequenceNumber.argtypes = []
GetClipboardSequenceNumber.restype = DWORD

safeCloseClipboard = CheckedCall(windll.user32.CloseClipboard)
safeCloseClipboard.argtypes = []
safeCloseClipboard.restype = BOOL

safeEmptyClipboard = CheckedCall(windll.user32.EmptyClipboard)
safeEmptyClipboard.argtypes = []
safeEmptyClipboard.restype = BOOL

safeGetClipboardData = CheckedCall(windll.user32.GetClipboardData)
safeGetClipboardData.argtypes = [UINT]
safeGetClipboardData.restype = HANDLE

safeSetClipboardData = CheckedCall(windll.user32.SetClipboardData)
safeSetClipboardData.argtypes = [UINT, HANDLE]
safeSetClipboardData.restype = HANDLE

safeGlobalAlloc = CheckedCall(windll.kernel32.GlobalAlloc)
safeGlobalAlloc.argtypes = [UINT, c_size_t]
safeGlobalAlloc.restype = HGLOBAL

safeGlobalLock = CheckedCall(windll.kernel32.GlobalLock)
safeGlobalLock.argtypes = [HGLOBAL]
safeGlobalLock.restype = LPVOID

safeGlobalUnlock = CheckedCall(windll.kernel32.GlobalUnlock)
safeGlobalUnlock.argtypes = [HGLOBAL]
safeGlobalUnlock.restype = BOOL

wcslen = CheckedCall(msvcrt.wcslen)
wcslen.argtypes = [c_wchar_p]
wcslen.restype = UINT

GMEM_MOVEABLE = 0x0002
CF_UNICODETEXT = 13

class PyperclipException(RuntimeError):
    pass

class PyperclipWindowsException(PyperclipException):
    def __init__(self, message):
        message += " (%s)" % ctypes.WinError()
        super(PyperclipWindowsException, self).__init__(message)

def _stringifyText(text):
    if not isinstance(text, (str, int, float, bool)):
        raise PyperclipException(f'only str, int, float, and bool values can be copied to the '
                                 f'clipboard, not {text.__class__.__name__}')
    return str(text)

class _Window(object):
    def __init__(self):
        pass

    def __enter__(self) -> HWND:
        # we really just need the hwnd, so setting "STATIC"
        # as predefined lpClass is just fine.
        self.hwnd = safeCreateWindowExA(0, b"STATIC", None, 0, 0, 0, 0, 0, None, None, None, None)
        return self.hwnd

    def __exit__(self, _type, _value, _traceback):
        safeDestroyWindow(self.hwnd)

class _ClipBoard(object):
    """ Context manager that opens the clipboard and prevents other applications from modifying
    the clipboard content. We may not get the clipboard handle immediately because some other
    application is accessing it (?) We try for at least 500ms to get the clipboard.
    """
    def __init__(self, window_handle: Optional[HWND]):
        self.window_handle = window_handle

    def __enter__(self):
        end_time = time() + 0.5
        while time() < end_time and not OpenClipboard(self.window_handle):
            sleep(0.01)
        if time() > end_time:
            raise PyperclipWindowsException("Error calling OpenClipboard")

    def __exit__(self, _type, _value, _traceback):
        safeCloseClipboard()

def copy(text):
    text = _stringifyText(text)  # Converts non-str values to str.

    with _Window() as hwnd:
        with _ClipBoard(hwnd):
            safeEmptyClipboard()

            if text:
                # http://msdn.com/ms649051
                # If the hMem parameter identifies a memory object,
                # the object must have been allocated using the
                # function with the GMEM_MOVEABLE flag.
                count = wcslen(text) + 1
                handle = safeGlobalAlloc(GMEM_MOVEABLE,
                                         count * sizeof(c_wchar))
                locked_handle = safeGlobalLock(handle)

                ctypes.memmove(c_wchar_p(locked_handle), c_wchar_p(text), count * sizeof(c_wchar))

                safeGlobalUnlock(handle)
                safeSetClipboardData(CF_UNICODETEXT, handle)

def paste():
    with _ClipBoard(None):
        handle = safeGetClipboardData(CF_UNICODETEXT)
        if not handle:
            # GetClipboardData may return NULL with errno == NO_ERROR
            # if the clipboard is empty.
            # (Also, it may return a handle to an empty buffer,
            # but technically that's not empty)
            return ""
        return c_wchar_p(handle).value

clip_id = 0

def is_new() -> bool:
    global clip_id
    with _ClipBoard(None):
        copy_id = GetClipboardSequenceNumber()
        if clip_id == 0:
            clip_id = copy_id
            return False
        if copy_id != clip_id:
            clip_id = copy_id
            return True
        return False
