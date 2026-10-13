# Real GUI preferences and installed MSIX update — 2026-10-14

- Product: `BackupRestoreVerifier`
- Passing Windows CI: https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/38477451887
- Regression tests: 8 passed
- Saved GUI preferences: 検証レポート先（reports）、一時復元サイズ上限（maxmb）.

The GUI now has a **設定を保存** button. UTF-8 JSON `schema_version=1`, allowlisted strings, atomic replacement and non-destructive handling of damaged/newer files. Packaged app stores `%LOCALAPPDATA%\Packages\<ActualPackageFamilyName>\LocalState\BackupRestoreVerifier\preferences.json`; unpackaged app uses `%LOCALAPPDATA%\BackupRestoreVerifier\preferences.json`. User document contents are NOT saved.

Windows CI verified actual GUI settings save, package update from 1.0.0.0 to 1.0.1.0, SHA-256 matching JSON, and fresh installed GUI settings reload. CI-only synthetic data; temporary signing certificates removed.

Not verified: historical released-version config migration, original business documents, human GUI operation, real Windows 10/11 hardware, Defender/security review, production Microsoft Store identity/licensing, or data retention after uninstall.

**RELEASE_BLOCKED / REAL_GUI_SETTINGS_CI_PASS.**
