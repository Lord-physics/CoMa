"""Inicio automático por usuario, sin privilegios administrativos."""

import subprocess
import sys
import winreg
from pathlib import Path


KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
NAME = "CoMa"


def _command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    executable = str(pythonw if pythonw.exists() else sys.executable)
    return subprocess.list2cmdline([executable, str(Path(__file__).resolve().parent.parent / "main.py")])


def enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY) as key:
            value, _ = winreg.QueryValueEx(key, NAME)
        return value == _command()
    except FileNotFoundError:
        return False


def set_enabled(value: bool) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, KEY, 0, winreg.KEY_SET_VALUE) as key:
        if value:
            winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(key, NAME)
            except FileNotFoundError:
                pass
