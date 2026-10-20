# Store readiness status — 2026-10-20

**DRAFT / NOT READY FOR SUBMISSION**

Validated source head: `e851bf0a38c96f6481474387b2cf37f49808045e`.

## Verified

- Local code tests: 40 passed, 3 skipped; 19 subtests passed.
- Fresh unsigned MSIX build/round-trip: PASS; SHA256 `427aad4097973f28ad04c18fa0db3d32f6732e9fd7060b75ca63f5dcf37ba054`.
- Local-validation signed copy SHA256 `a6f33ed6ed8daea91a9b36dd1a897ceaba686209611ebec18f359a5f34c0e296`; signer matched thumbprint `60BB363D9BE876439137DFB31247952463106BDD`.
- Windows API calculated PFN `OkinawaDesktopTools.FolderAutomationEngine_j8yefg9jgfh58` from the package Identity, matching the captured draft.

## CI

Current-head runs `39400008612` and `39400008343` are **CI_FAIL_UNDIAGNOSED**. Build and Ubuntu/Windows validation jobs failed before runner assignment; `steps=[]`; no job-log blob exists. The root cause has not been established.

## Not yet verified

MSIX installation, Start-menu launch, installed JP/EN UI, restart, safe copy/move/watcher/collision I/O in a disposable folder, Store screenshots, WACK, and live Partner Center identity are NOT TESTED. No certificate-store change is authorized.

## Submission safeguards

- Microsoft Standard Application License Terms (SALT) are the default when **Additional license terms** is left blank. A custom EULA is not an engineering prerequisite unless the owner chooses different terms.
- Prices and Japan/United States markets remain proposals only. Disable future-market automatic expansion.
- Immediately before certification submission, select **Don't publish this submission until I select Publish now**. The default can publish automatically after certification.
- AI-generated icons remain unapproved concepts and are not package or Store assets.
- Certificate-store changes, Store upload/submission/publication, and main/release merges remain unauthorized.
