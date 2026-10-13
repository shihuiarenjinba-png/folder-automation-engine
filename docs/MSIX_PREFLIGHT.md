# Microsoft Store MSIX preflight — Backup Restore Verifier

**Current status: QA PROTOTYPE; NOT signed, installed, certified or approved for sale.**

## What the automated check does

1. Check the existing PyInstaller onedir validation build and its EXE SHA-256.
2. Create a temporary MSIX file layout from the validated binaries, not from customer files.
3. Generate neutral test-only placeholder logos. They are not final product branding.
4. Create an AppxManifest with a synthetic QA identity, desktop full-trust declaration and Windows.Desktop dependency.
5. Use Windows SDK `makeappx.exe pack`, then `makeappx.exe unpack`.
6. Compare the extracted EXE's SHA-256 with the original validated EXE.
7. Write `msix-preflight-report.json` with `signed=false`, `installed_or_launched=false`, `release_approved=false`.

This test exercises the **packaging mechanism** only. It does NOT prove installability, correctness of filesystem virtualization, Start Menu display, accessibility, enterprise trust, or Microsoft Store acceptance.

## Run on the Windows development machine

Prerequisites: Python 3 launcher (`py -3`), Windows SDK's `makeappx.exe`, sufficient disk space, and the existing repo's build prerequisites. All commands run locally.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\build-windows-validation.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\qa\build-msix-preflight.ps1 -TestIdentity
```

When more than one validation build exists, specify the exact `-ManifestPath "C:\path\to\validation-manifest.json"` in the second command. The package appears in a new `dist-validation\...\msix-preflight-<GUID>` folder.

**Never upload a test-identity package to Partner Center.** The test identity and publisher values are intentionally fake, and no signing or install has been performed.

## Before preparing a real Store package

- [ ] Complete Windows 10/11 human acceptance under `docs/WINDOWS_MANUAL_ACCEPTANCE.md`.
- [ ] Resolve errors and security findings; inspect Defender history and independent scanner feedback.
- [ ] Confirm which **Partner Center product** this product belongs to. The existing Store submissions for unrelated products are not reusable identities.
- [ ] Get the exact `Identity Name`, `Publisher` and approved app title from **Partner Center > Product management > App identity**. No placeholder values.
- [ ] Replace QA branding with reviewed, original product artwork and accurate package metadata.
- [ ] Define and test an MSIX version sequence, update path, data storage location, uninstall behavior and target architectures.
- [ ] Make an installable candidate using the documented Store/enterprise signing route; do not silently install an untrusted test package.
- [ ] Execute the **Windows App Certification Kit** and actual install/launch/upgrade/uninstall tests.
- [ ] Verify Store commerce and licensing behavior, screenshots, category, privacy policy and certification notes.
- [ ] Explicitly authorize an actual Partner Center submission only after all release gates pass.

Microsoft documentation:
- https://learn.microsoft.com/en-us/windows/apps/distribute-through-store/how-to-distribute-your-win32-app-through-microsoft-store
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements
- https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-manual-conversion

**Release gate: BLOCKED until manual, security, identity, distribution and Store requirements are satisfied.**
