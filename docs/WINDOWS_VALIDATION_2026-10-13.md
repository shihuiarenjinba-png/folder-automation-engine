# Windows validation record — 2026-10-13

## Confirmed CI result

- Repository: `folder-automation-engine`
- Test-only branch: `validation/windows-20261013`
- Tested commit: `5cddfd4849c8faaf8c7f02f282563f073c7be6f1`
- Windows GitHub Actions run: https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/38386305477
- Runner environment: `windows-latest`, Python 3.11
- Automated unit tests run: **4, passing**
- PyInstaller Windows one-directory executable: **built successfully**
- Generated executable name: `BackupRestoreVerifier.exe`
- EXE SHA-256 (ephemeral CI build): `763E404C43DC4110C1BB7F457F98DBD05E1385F60E249930CB24029CDA8CDE6C`
- Workflow conclusion: **success**

## Restrictions / release gates

- **NOT A SALES RELEASE.** EXE is unsigned and no manual GUI/window interaction tests were run.
- GitHub Actions artifact quota was exceeded. Binary upload was disabled; no downloadable build is preserved by this run. SHA-256 alone is not an EXE download.
- Windows host integration and actual GUI interactions, malware/Defender checks, signing, installer/MSIX, privacy review and Microsoft Store certification remain pending.
- Current automated tests are focused regression fixtures; they do not certify every file format, filesystem edge case, encoding, performance, security behavior, or real user dataset.
- `main` retains manually triggered `windows-validation.yml`; the push trigger exists only on the isolated validation branch.
- A future build from the same sources might not reproduce this hash unless the toolchain and dependencies are pinned.
- Do not merge the validation-only push trigger or claim full release approval.

## Next steps

1. Run the existing PowerShell validation script on a controlled Windows 10/11 test PC.
2. Perform explicit GUI open/import/output/safety tests, including negative and non-ASCII cases.
3. Audit compiled binaries, dependencies, egress, filesystem writes, uninstall, Defender results.
4. Sign release candidates and inspect manifest/AV results before creating an MSIX or selling.

Status: `AUTOMATED_WINDOWS_TEST_AND_BUILD_PASS / RELEASE_BLOCKED`.
