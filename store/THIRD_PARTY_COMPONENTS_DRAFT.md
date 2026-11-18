# Third-party component inventory — Store candidate engineering record

Updated: 2026-11-13 JST

The Windows Store candidate build is now pinned to the same toolchain versions proven by the successful Windows build on 2026-11-11:

- CPython 3.12.10
- PyInstaller 6.22.3
- PyInstaller hooks contrib 2026.10
- altgraph 0.17.5
- packaging 26.3
- pefile 2024.8.26
- pywin32-ctypes 0.2.3
- setuptools 84.2.1
- pip 26.3

The exact pins live in `store/build-requirements-win.txt`. The Windows build fails if Python or PyInstaller differs from the recorded production toolchain.

## Runtime license evidence

The build now runs `store/collect_runtime_notices.py` after PyInstaller packaging and before MSIX creation. It fails closed unless the required core evidence is found. The packaged application contains a `THIRD_PARTY_NOTICES` directory with:

- the exact CPython `LICENSE.txt` from the pinned Python installation;
- Tcl/Tk `license.terms` when supplied by the Windows CPython distribution;
- the PyInstaller distribution's LICENSE/COPYING material;
- `THIRD_PARTY_NOTICES.md`;
- `BUILD_COMPONENT_VERSIONS.json` recording the actual installed build component versions.

The MSIX builder refuses to package a payload if the notice directory or its required summary/version files are absent.

## Runtime components expected in the pinned CPython/PyInstaller payload

| Component | Pinned/observed evidence | License family / handling |
|---|---|---|
| CPython runtime | 3.12.10 | Python Software Foundation License; exact runtime license copied into package |
| Tcl/Tk | Windows CPython 3.12.10 payload | Tcl/Tk permissive license terms copied when present |
| OpenSSL | supplied with pinned CPython runtime | covered by exact CPython/runtime licensing evidence; final byte inventory retained |
| SQLite | supplied with pinned CPython runtime | provenance retained in package inventory |
| libffi | supplied with pinned CPython runtime | provenance retained in package inventory |
| zlib | supplied with pinned CPython runtime | provenance retained in package inventory |
| PyInstaller bootloader/runtime | 6.22.3 | exact installed PyInstaller license/COPYING material copied into package |

No external icon or third-party artwork is used by the MSIX builder. The current icon candidate is generated deterministically in repository code from basic geometric shapes.

## Package-byte inventory

`store/build_msix_draft.ps1` now writes `package_file_inventory.json` before packing the MSIX. For every staged file it records:

- relative package path;
- byte size;
- SHA256.

The output also records source commit, MSIX version and total file count. The Store workflow verifies inventory provenance and uploads the inventory beside the unsigned MSIX and validation report.

## Remaining owner/legal gate

Engineering has automated the provenance and notice collection. Before actual Store upload, the owner should review the generated notice bundle and final inventory for unexpected files and approve the commercial distribution record. This approval is represented separately from CI success in the Store upload contract.
