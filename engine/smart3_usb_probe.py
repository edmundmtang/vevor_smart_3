"""Read-only USBPRINT interface discovery and open test for VEVOR Smart 3.

No data is transmitted. No driver changes. Windows only.
"""
import argparse
import ctypes
from ctypes import wintypes
import sys
import uuid

GUID_USBPRINT = '{28D78FAD-5A12-11D1-AE5B-0000F803A8C2}'
VID_PID = 'vid_045b&pid_5310'
DIGCF_PRESENT = 0x2
DIGCF_DEVICEINTERFACE = 0x10
ERROR_NO_MORE_ITEMS = 259
ERROR_INSUFFICIENT_BUFFER = 122
FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2
OPEN_EXISTING = 3
GENERIC_WRITE = 0x40000000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

class GUID(ctypes.Structure):
    _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD),
                ('Data3', wintypes.WORD), ('Data4', ctypes.c_ubyte * 8)]

class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.DWORD), ('InterfaceClassGuid', GUID),
                ('Flags', wintypes.DWORD), ('Reserved', ctypes.c_void_p)]

def win_guid(s):
    return GUID.from_buffer_copy(uuid.UUID(s).bytes_le)

def enumerate_usbprint():
    setup = ctypes.WinDLL('setupapi', use_last_error=True)
    setup.SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), wintypes.LPCWSTR, wintypes.HWND, wintypes.DWORD]
    setup.SetupDiGetClassDevsW.restype = ctypes.c_void_p
    setup.SetupDiEnumDeviceInterfaces.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(GUID), wintypes.DWORD, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA)]
    setup.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
    setup.SetupDiGetDeviceInterfaceDetailW.argtypes = [ctypes.c_void_p, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA), ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    setup.SetupDiGetDeviceInterfaceDetailW.restype = wintypes.BOOL
    setup.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]
    setup.SetupDiDestroyDeviceInfoList.restype = wintypes.BOOL
    guid = win_guid(GUID_USBPRINT)
    handle = setup.SetupDiGetClassDevsW(ctypes.byref(guid), None, None, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE)
    if handle == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        index = 0
        while True:
            item = SP_DEVICE_INTERFACE_DATA()
            item.cbSize = ctypes.sizeof(item)
            if not setup.SetupDiEnumDeviceInterfaces(handle, None, ctypes.byref(guid), index, ctypes.byref(item)):
                err = ctypes.get_last_error()
                if err == ERROR_NO_MORE_ITEMS:
                    break
                raise ctypes.WinError(err)
            needed = wintypes.DWORD()
            setup.SetupDiGetDeviceInterfaceDetailW(handle, ctypes.byref(item), None, 0, ctypes.byref(needed), None)
            if ctypes.get_last_error() != ERROR_INSUFFICIENT_BUFFER or needed.value < 8:
                raise ctypes.WinError(ctypes.get_last_error())
            buf = ctypes.create_string_buffer(needed.value)
            # SP_DEVICE_INTERFACE_DETAIL_DATA_W.cbSize is 8 on 64-bit, 6 on 32-bit.
            ctypes.cast(buf, ctypes.POINTER(wintypes.DWORD))[0] = 8 if ctypes.sizeof(ctypes.c_void_p) == 8 else 6
            if not setup.SetupDiGetDeviceInterfaceDetailW(handle, ctypes.byref(item), buf, needed.value, ctypes.byref(needed), None):
                raise ctypes.WinError(ctypes.get_last_error())
            # DevicePath starts at byte offset 4 even when cbSize is 8.
            yield ctypes.wstring_at(ctypes.addressof(buf) + 4)
            index += 1
    finally:
        setup.SetupDiDestroyDeviceInfoList(handle)

def open_only(path, write_access=False):
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    kernel.CreateFileW.restype = ctypes.c_void_p
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = wintypes.BOOL
    access = GENERIC_WRITE if write_access else 0
    h = kernel.CreateFileW(path, access, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None)
    if h == INVALID_HANDLE_VALUE:
        raise ctypes.WinError(ctypes.get_last_error())
    kernel.CloseHandle(h)

def main():
    p = argparse.ArgumentParser(description='Discover and open Smart 3 USBPRINT interface; NEVER transmits data')
    p.add_argument('--test-write-open', action='store_true', help='Also try opening with write permission, but DO NOT write data')
    args = p.parse_args()
    if sys.platform != 'win32':
        p.error('Windows only')
    try:
        paths = list(enumerate_usbprint())
        print(f'USBPRINT interfaces found: {len(paths)}')
        matches = [path for path in paths if VID_PID in path.lower()]
        for path in matches:
            print(f'\nSmart 3 interface: {path}')
            for label, write in [('Metadata-only open', False)] + ([('Write-permission open (NO WRITE)', True)] if args.test_write_open else []):
                try:
                    open_only(path, write)
                    print(f'{label}: SUCCESS')
                except OSError as exc:
                    print(f'{label}: FAILED: {exc}')
        if not matches:
            print('No matching VID_045B&PID_5310 interface found.')
    except OSError as exc:
        p.exit(1, f'Windows API error: {exc}\n')
    print('\nNO DATA SENT. NO CUT PERFORMED.')

if __name__ == '__main__':
    main()
