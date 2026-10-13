# Windows installed MSIX GUI launch and LocalState persistence — 2026-10-14

- Existing product: `BackupRestoreVerifier`; repository: `folder-automation-engine`
- Windows CI run: https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/38419688946 (**SUCCESS**)
- Signed synthetic QA MSIX 1.0.0.0 installed; GUI launched by registered AppUserModelID via Windows Shell API, not by running an unpackaged EXE
- Compiled Tk GUI wrote a proof JSON to per-package `LocalState`
- Same-package-family 1.0.1.0 update preserved original proof byte-for-byte, verified with SHA-256, and packaged GUI launched after update
- Test app removed, temporary signing and trust certificate entries removed

**Not validated**: actual end-user configuration/save/data migration, GUI visuals, manual clicks, Windows 10/11 hardware matrix, Defender/security review, Partner Center identity, production signing or certification.

Test runner restrictions prevent accidental installation on a personal PC. Main GitHub Actions is still manual-only. No Store submission or release approval.

**State: INSTALLED_APP_ACTIVATION_AND_SYNTHETIC_STATE_PASS / RELEASE_BLOCKED.**
