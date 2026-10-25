# Group B standard edition — Folder Automation Engine Store QA (2026-10-24 JST)

**Current verdict: HOLD / NOT APPROVED FOR INSTALLATION, SUBMISSION OR SALE.**
Scope: the regular Folder Automation Engine ONLY. No `-2` repository/branch, `main`, release branch or unrelated product is changed.

## 1. Provenance verified from GitHub and archive bytes

- Baseline source branch: `codex/store-draft-validation-20261019`
- Baseline source commit: `6848d3c337aa71a36115951dc796241faf9b78c4`
- Baseline draft PR: #7, unmerged
- Successful Windows CI: `40049815221` (12 recorded steps success)
- Windows artifact ID: `12543101783`
- Unsigned Store draft MSIX artifact ID: `12543151273`
- Artifact ZIP SHA256 (Windows): `56368da9c27eb78786971307816c02b220d768a0f3869c89b648d14128d17f9f`
- Artifact ZIP SHA256 (MSIX): `ac2fd7832dabb50b71dabfbdad8339a50adec5954a00756cebbfcbb8486caa1c`
- Baseline unsigned MSIX: `FolderAutomationEngine_1.0.0.0_x64_StoreDraft_UNSIGNED.msix`
- MSIX SHA256: `da0377996b76f243e7dc3eba6af61e8ce89a05cac94fc3a783e95d3b23327da7`
- Standalone EXE and unpacked MSIX EXE identical SHA256:
  `246801a2b6825370217331b3bfe46f584233fea9a33e9d0a08ec26a453239d17`
- Independently opened both archives as data; checked ZIP CRCs, nested MSIX manifest, its version/x64/name/publisher, source commit, sidecar hash, EXE hash, PyInstaller `_internal`, and absence of `AppxSignature.p7x`. **PASS (static only).**
- No EXE/MSIX was executed or installed by ChatGPT. No Windows system policy/security setting/certificate store was changed.

## 2. Identity is a recorded candidate, not a fresh Partner Center verification

Existing repository evidence from an owner screenshot records:
- Store ID: `9P99MJX1R4V6`
- Identity: `OkinawaDesktopTools.FolderAutomationEngine`
- Publisher: `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`
- Version: `1.0.0.0` technical draft, not approved public-version selection
- Previous accepted Store version: UNKNOWN
- Package history and current Partner Center identity **must be independently re-checked before submission**.

## 3. Specific QA findings

1. The Folder GUI `folder_desktop_app.py` defaulted to Japanese on each launch and never wired the existing local preference helper into the locale selector. **Repair staged on separate QA branch** with no-new-feature persistence limited to `locale` and fail-closed behavior when preferences cannot be saved. New no-window tests added. This repair is **not present in the baseline ZIP/MSIX** above. Build fresh binaries from the revised commit and verify all SHA256 again before evaluating this repair.
2. The older `docs/WINDOWS_QA_RUNBOOK.md`, `docs/WINDOWS_MANUAL_ACCEPTANCE.md`, and `qa/windows-acceptance.ps1` primarily validate the independently launched Backup Restore Verifier, not this Folder GUI. Its legacy validation-manifest fields differ from `build-folder-desktop-validation.ps1`. **Do not apply the Backup Restore Verifier PASS to this product or pass the Folder GUI manifest to that collector.** The correct Folder GUI builder is `build-folder-desktop-validation.ps1`; the correct store builder is `store/build_msix_draft.ps1`.
3. The baseline Folder GUI offered **save new config JSON** without a corresponding UI import/reopen path. A safe **Load saved JSON config** action is now staged on this separate QA branch: it validates against the exact no-overwrite schema, rejects modified/unsupported fields and revokes old Dry Run approval. **Fresh exact-head Windows CI and real restart acceptance remain HOLD**; do not claim observed restoration yet.
4. `approved_logo=false`, `symlink_safety_tests_complete=false`, `manual_windows_acceptance=false`, `signed=false`, `sale_approved=false` in MSIX validation.
5. Backup restore verification is a separate GUI; it must not be shown as a tab/integrated feature in this SKU's Store listing.

## 4. Code operator: controlled Windows 11 acceptance

**Do not treat this note as permission to launch any downloaded EXE.** Use the original code-operator action-time approval method and independently verify its exact SHA256 before running. Normal user privileges; disposable test folders only; no security-setting or certificate-store changes.

After the QA branch build passes GitHub CI, capture its *new exact* commit and *new hashes*. In a disposable workspace, test:

| Gate | Scenario | Status |
|---|---|---|
| W01 | Verify exact executable hash, provenance, no unexpected sign claim | PENDING |
| W02 | First launch, clear user instructions, no hidden primary controls | PENDING |
| W03 | Japanese → English → Japanese; restart and confirm saved language | PENDING |
| W04 | Save a rule/config, close and reload via GUI; reject unsafe JSON; new Dry Run mandatory | PENDING (fix staged) |
| W05 | 1024x768 and 1280x720, with 100/125/150% real Windows display scaling | PENDING |
| W06 | Keyboard traversal, scrollable results, errors visible in both languages | PENDING |
| W07 | Use synthetic *.csv and *.txt: Dry Run creates no output / audit changes | PENDING |
| W08 | Explicit approval and cancelled confirmation: cancelled run changes nothing | PENDING |
| W09 | Copy preserves original and matches SHA256; move has exact destination content | PENDING |
| W10 | Existing destination collision and two overlapping rules never overwrite | PENDING |
| W11 | After Dry Run: add/modify/delete input; stale preview refuses live | PENDING |
| W12 | Failed/staged/interrupted move retains original; changed source safe stop | PENDING |
| W13 | Symlink/junction, long/Unicode filenames, 0-byte data; separate filesystem coverage | PENDING |
| W14 | Opt-in watch: stable input only; stop; no processing after application closes | PENDING |
| W15 | Exit/restart, retained preferences and user-visible config behavior | PENDING |
| W16 | Scan actual tested bits with existing Windows Defender; review any detections | PENDING |
| W17 | True Store screenshots: JA/EN genuine Windows screenshots, no secrets | PENDING |
| W18 | MSIX install/launch/update/uninstall; WACK; Partner Center draft/history/identity | BLOCKED by authorizations |
| W19 | License, third-party notices, rights of artwork, accurate Store listing | PENDING |

Proof per case: PASS/FAIL/BLOCKED/SKIP, tested commit, executable hash, Windows build/DPI/resolution, synthetic input/output SHA256, redacted evidence paths. A test merely described in code is NOT an observed Windows PASS.

## 5. Forbidden until separate approvals

- Running candidate EXE or installing unsigned MSIX on owner's Windows PC without required action-time authorization
- Registry trust bypasses, certificate store or Windows Security changes
- Any actual customer files / real synced folders as initial test data
- Merging to main/release, promoting this draft binary to release, using `-2` branches
- Store upload/certification submission/publication and paid Actions/certificates

**Commercial GO requires complete manual GUI/safety gates, final images/assets/notices and Partner Center validation.**

## 6. 2026-10-25 continuation record

- Current branch and remote baseline were rechecked at `1203d6ac8ef1c56f6f11e6a510ec30dd737a0400` before changes.
- The owner-authorized executable had already been re-hashed and launch-attempted. Code Integrity blocked process creation (events 3077/3033; Policy ID `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`). No warning was bypassed, no Windows security setting changed, and no disposable input changed.
- A source review found that closing the Tk window during an active worker/watcher did not explicitly wait for a safe processing boundary. The staged repair registers `WM_DELETE_WINDOW`, signals watcher stop, disables further controls and polls active worker/watcher threads before destroying the window.
- Three safe-close unit tests were added. The complete source suite ran 60 tests: 57 PASS and the previously identified 3 symbolic-link cases SKIP under the standard-user token.
- A packaged-EXE GUI-window smoke and real window screenshot collector is staged for disposable GitHub-hosted Windows only. It cannot run locally and cannot be reported as human QA or Store artwork.
- Store listing and privacy drafts were aligned with the implemented settings/config/state paths. A prior-payload third-party inventory was added; exact final-build notices and owner/legal approval remain HOLD.

Fresh exact-commit Windows artifacts, their SHA256 values and CI GUI evidence are PENDING until this update is committed and the workflows complete. W01–W19 remain governed by the table above; no pending human or MSIX gate became PASS through source tests.
