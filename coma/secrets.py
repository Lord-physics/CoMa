"""Cifrado DPAPI ligado al usuario actual de Windows."""

import base64
import ctypes
from ctypes import wintypes


class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def _blob(data: bytes):
    buffer = ctypes.create_string_buffer(data)
    return _Blob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte))), buffer


def _crypt(data: bytes, *, decrypt: bool) -> bytes:
    source, keep_alive = _blob(data)
    output = _Blob()
    function = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    function.restype = wintypes.BOOL
    function.argtypes = (
        [ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob)]
        if decrypt else
        [ctypes.POINTER(_Blob), wintypes.LPCWSTR, ctypes.POINTER(_Blob), ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_Blob)]
    )
    args = [ctypes.byref(source), ctypes.byref(output)] if decrypt else [ctypes.byref(source), "CoMa", ctypes.byref(output)]
    if decrypt:
        ok = function(args[0], None, None, None, None, 0, args[1])
    else:
        ok = function(args[0], args[1], None, None, None, 0, args[2])
    _ = keep_alive
    if not ok:
        raise OSError(ctypes.get_last_error(), "Windows no pudo proteger o leer el secreto")
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        free = ctypes.windll.kernel32.LocalFree
        free.argtypes = [ctypes.c_void_p]
        free.restype = ctypes.c_void_p
        free(output.pbData)


def protect(secret: str) -> str:
    return base64.b64encode(_crypt(secret.encode("utf-8"), decrypt=False)).decode("ascii")


def unprotect(value: str) -> str:
    return _crypt(base64.b64decode(value), decrypt=True).decode("utf-8")
