# Windows 10/11 manual acceptance checklist (OPEN)

**Status: NOT EXECUTED. Not a sales release approval.**

## Safe setup

Run only with disposable synthetic data, never on the only copy of work files. Use a normal Windows user account (avoid running as Administrator). Clone the repository, open PowerShell from the repository folder, then run:

```powershell
powershell -ExecutionPolicy Bypass -File .\build-windows-validation.ps1
```

Find the generated executable under `dist-validation\<Product>-<GUID>\<Product>\<Product>.exe`. The script produces an unsigned **validation** build, not a store package. If GitHub Actions shows Success, that does NOT mean human GUI operation has been tested.

## Human test scenarios

1. [ ] Create an isolated source and backup folder. Snapshot trustworthy source BEFORE backup; store manifest outside both trees.
2. [ ] Verify a clean backup, corrupt one backup file, remove one file and add an unexpected file; require REVIEW for all deviations.
3. [ ] Exercise GUI source/backup/manifest selectors and inspect output JSON, always checking source and backup are not modified by verification.
4. [ ] Test symlink/junction paths, long paths, Unicode filenames and read-only files safely in a disposable directory.
5. [ ] Perform a human recovery of one test file and open it in its target application; hash checks alone do not prove application-level recoverability.
## Evidence required before approval

- Record Windows edition/build (10 or 11), language, screen scaling, user mode, EXE path and SHA-256.
- Record pass/fail and sanitized screenshot for each manual case; ensure no personal/customer information is visible.
- Save before/after hashes of source test files and attach synthetic input, output and report examples to the local QA record.
- Check Defender/security scan output and packaging dependencies; validate offline operation and absence of unexpected network calls.
- Test exit, relaunch and cleanup; do not claim installer/MSIX/uninstall success before separately testing them.
- Verify both Windows 10 and 11 (or explicitly record whichever is unavailable).
- Any crash, data overwrite, false clean result, unsigned binary reputation warning, unreadable Japanese PDF glyph or unreviewed security concern blocks release.

**Gate:** `MANUAL_WINDOWS_ACCEPTANCE_PENDING` / `RELEASE_BLOCKED`. Never promote to sales approval based only on CI-generated EXE and automated GUI fixtures.
