# Folder Automation Engine — Local/MSIX/Store handoff plan

Updated: 2026-11-13 JST

## Distribution strategy

This product stays on the **MSIX Store path**.

- The engineering candidate is an unsigned MSIX intended for Partner Center upload.
- Do **not** sideload the unsigned Store candidate onto the owner's protected Windows machine.
- Local/operator machines may inspect hashes, manifest, package inventory and notices without installation.
- The first real installation test should use a **Microsoft Store-signed MSIX delivered to a Private audience** after certification.
- Keep publishing hold set to **manual**. Private audience testing is not authorization for public release.
- Public release is a later, separate owner approval.

Microsoft Store also accepts EXE/MSI submissions, but this repository intentionally remains on the MSIX path because it gives Store-managed signing, installation/update behavior, private audience and package flight support.

## Local handoff contents

For every frozen candidate, share these exact items together:

1. `FolderAutomationEngine_<version>_x64_StoreDraft_UNSIGNED.msix`
2. `msix.sha256.txt`
3. `msix_validation.json`
4. `package_file_inventory.json`
5. packaged `THIRD_PARTY_NOTICES/`
6. exact Git source commit
7. Windows Artifact ID and MSIX Artifact ID
8. CI run URLs/results
9. human Windows QA report once completed
10. Store upload bundle JSON

Never copy only the MSIX without its provenance.

## Local operator workflow — no install

1. Download the exact MSIX artifact and Windows artifact for the same Git HEAD.
2. Recalculate ZIP, EXE and MSIX SHA256.
3. Run `qa/verify_msix_inventory.py` against the final MSIX and inventory.
4. Confirm manifest Identity/Publisher/Version/architecture and the source commit in `msix_validation.json`.
5. Confirm the EXE inside the MSIX is byte-identical to the Windows artifact EXE.
6. Confirm third-party notices and build component version record are present.
7. Record `LOCAL_STATIC_MSIX_VERIFIED = PASS`.
8. **Do not install the unsigned package.**

## Private audience Store installation workflow

After all submission metadata is complete and the owner separately approves Partner Center writes:

1. Use the existing Folder Automation Engine Store product; never create a duplicate.
2. Re-copy live Store ID, Package Identity Name, Publisher, PFN and accepted version history.
3. Set Audience = **Private audience** and choose/create the owner-approved known-user group.
4. Use a personal Microsoft account for each tester. Do not use an unapproved account.
5. Set publishing hold = **manual / Don't publish until I select Publish now**.
6. Upload only the exact final MSIX that passed the local handoff checks.
7. Save each section and run the automation in VALIDATE_ONLY / DRY_RUN before any final submission click.
8. Certification submission is a separate owner approval.
9. After certification and Store signing, install from Microsoft Store while signed in as an approved private-audience tester.
10. Perform the installed-package acceptance: Start-menu launch, JP/EN, file operations, LocalState, update/uninstall and genuine Store screenshots.
11. Public audience/publication remains HOLD until a later explicit owner approval.

## Package flight

Package flighting is for later updates after a base Store package exists. Do not use a package flight as a substitute for the initial Private audience submission.

## Gate definitions

- `BUILD_READY`: exact-head source/tests/build/MSIX provenance PASS.
- `LOCAL_STATIC_MSIX_VERIFIED`: exact MSIX and all provenance files independently match; no installation implied.
- `PRIVATE_AUDIENCE_SUBMISSION_READY`: all Partner Center fields and private-audience group are complete, upload validator passes and owner approves upload/submission phases.
- `STORE_SIGNED_INSTALL_READY`: private-audience certification succeeds and Microsoft Store offers the signed package to the approved tester.
- `STORE_UPLOAD_READY`: automation bundle passes the fail-closed validator plus owner upload approval.
- `PUBLIC_RELEASE_GO`: separate final approval after Store-signed install QA and certification evidence.

