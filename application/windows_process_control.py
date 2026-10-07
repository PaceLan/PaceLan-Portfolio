"""Windows-native process suspension helpers."""

from __future__ import annotations

import ctypes
from ctypes import wintypes


TH32CS_SNAPTHREAD = 0x00000004
THREAD_SUSPEND_RESUME = 0x0002
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


def _kernel32():
    if ctypes.sizeof(ctypes.c_void_p) != 8:
        raise RuntimeError("Windows process suspension requires 64-bit Python")
    return ctypes.WinDLL("kernel32", use_last_error=True)


def _thread_ids(process_id: int) -> list[int]:
    kernel32 = _kernel32()
    snapshot = kernel32.CreateToolhelp32Snapshot(
        TH32CS_SNAPTHREAD,
        0,
    )
    if snapshot == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())

    entry = THREADENTRY32()
    entry.dwSize = ctypes.sizeof(THREADENTRY32)
    ids: list[int] = []

    try:
        if not kernel32.Thread32First(snapshot, ctypes.byref(entry)):
            return ids

        while True:
            if entry.th32OwnerProcessID == process_id:
                ids.append(entry.th32ThreadID)

            if not kernel32.Thread32Next(snapshot, ctypes.byref(entry)):
                break
    finally:
        kernel32.CloseHandle(snapshot)

    return ids


def suspend_process(process_id: int) -> None:
    kernel32 = _kernel32()
    suspended = 0

    for thread_id in _thread_ids(process_id):
        handle = kernel32.OpenThread(
            THREAD_SUSPEND_RESUME,
            False,
            thread_id,
        )
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())

        try:
            result = kernel32.SuspendThread(handle)
            if result == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            suspended += 1
        finally:
            kernel32.CloseHandle(handle)

    if suspended == 0:
        raise RuntimeError("process has no suspendable threads")


def resume_process(process_id: int) -> None:
    kernel32 = _kernel32()
    resumed = 0

    for thread_id in _thread_ids(process_id):
        handle = kernel32.OpenThread(
            THREAD_SUSPEND_RESUME,
            False,
            thread_id,
        )
        if not handle:
            continue

        try:
            result = kernel32.ResumeThread(handle)
            if result == 0xFFFFFFFF:
                raise ctypes.WinError(ctypes.get_last_error())
            resumed += 1
        finally:
            kernel32.CloseHandle(handle)

    if resumed == 0:
        raise RuntimeError("process has no resumable threads")


__all__ = ["resume_process", "suspend_process"]
