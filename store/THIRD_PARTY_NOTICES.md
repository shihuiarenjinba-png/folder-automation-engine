# Folder Automation Engine — Third-party notices

This application is packaged with the CPython runtime and components distributed with that runtime.
The build process copies the exact runtime license files from the pinned build environment into the
application's `THIRD_PARTY_NOTICES` directory.

The Store candidate build is pinned to:

- CPython 3.12.10
- PyInstaller 6.22.3
- PyInstaller hooks contrib 2026.10
- altgraph 0.17.5
- packaging 26.3
- pefile 2024.8.26
- pywin32-ctypes 0.2.3
- setuptools 84.2.1

Runtime components observed in the CPython/PyInstaller payload include Tcl/Tk, SQLite, OpenSSL,
libffi and zlib. Their applicable notices are supplied by the corresponding CPython/runtime license
files collected during the exact build. PyInstaller's license/COPYING material is collected from
the installed PyInstaller distribution.

This notice is an engineering distribution record, not a replacement for the full license texts
that are included alongside it in the packaged `THIRD_PARTY_NOTICES` directory.
