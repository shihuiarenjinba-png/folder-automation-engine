# Third-party component inventory — DRAFT

Status: engineering inventory only; final package-byte inventory and legal approval are still required.

The previous Windows artifact (`12552836022`) was a PyInstaller `onedir` payload. Inspection of its extracted runtime identified the following components. A fresh build may update patch versions, so repeat this inventory against the exact package uploaded to Partner Center.

| Component observed in prior payload | Observed version/evidence | Upstream license summary | Final action |
|---|---|---|---|
| CPython runtime | `python312.dll` 3.12.10 | Python Software Foundation License Version 2; Python also contains separately licensed incorporated software | Include the complete Python license/acknowledgements appropriate to the exact runtime |
| Tcl/Tk | `tcl86t.dll` / `tk86t.dll` 8.6.15 | BSD-style Tcl/Tk license; commercial redistribution is allowed subject to its terms | Preserve the applicable Tcl/Tk notices |
| OpenSSL | `libcrypto-3.dll` 3.0.16 | OpenSSL 3.0 and later use Apache License 2.0 | Include Apache 2.0 license and any required notices for the exact binary |
| SQLite | `sqlite3.dll` 3.49.1 | SQLite deliverable code is dedicated to the public domain | Record provenance; legal owner decides whether an informational notice is included |
| libffi | `libffi-8.dll`; precise upstream version not established from the binary | Permissive license requiring the copyright and permission notice in copies/substantial portions | Resolve exact version and include its LICENSE notice |
| zlib | `zlib1.dll` 1.3.1 | zlib license; commercial use and redistribution permitted subject to its restrictions | Preserve the notice appropriate to the exact distributed binary/source obligations |
| PyInstaller bootloader/runtime | build script specifies `pyinstaller>=6.10,<7`; exact prior version not recorded | GPL 2.0 with a bootloader exception plus Apache 2.0 for specified files; generated bundles may use the app's license if dependency licenses are respected | Pin and record exact build-tool version; retain the upstream license audit record |

No bundled component was intentionally modified by this repository; this statement must be rechecked against the reproducible final build process. This draft does not constitute legal advice or a completed `THIRD_PARTY_NOTICES` file.

## Official upstream references reviewed 2026-10-25

- Python: https://docs.python.org/3/license.html
- Tcl/Tk: https://www.tcl-lang.org/software/tcltk/
- OpenSSL: https://openssl-library.org/source/license/index.html
- SQLite: https://www.sqlite.org/copyright.html
- libffi: https://github.com/libffi/libffi/blob/master/LICENSE
- zlib: https://zlib.net/zlib_license.html
- PyInstaller: https://pyinstaller.org/en/stable/license.html

## Release HOLD checklist

- [ ] Pin the exact Python and PyInstaller versions used for the final candidate.
- [ ] Generate a file inventory/SBOM from the final MSIX bytes.
- [ ] Map every bundled binary/package to its exact license text and version.
- [ ] Add approved license and notice files to the distribution where required.
- [ ] Confirm no unexpected packages or build-machine files are bundled.
- [ ] Obtain owner/legal approval before Store upload.
