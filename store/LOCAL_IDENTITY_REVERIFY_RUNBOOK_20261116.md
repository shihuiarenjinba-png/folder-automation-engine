# Folder Automation Engine — local Partner Center Identity re-verification

Purpose: re-read the existing Microsoft Store product Identity and prove that
the already-recorded values still exactly match. This is NOT a new product
reservation and does not upload MSIX, change pricing, submit certification, or publish.

## Existing product

- Store ID: `9P99MJX1R4V6`
- Identity Name: `OkinawaDesktopTools.FolderAutomationEngine`
- Publisher: `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`
- PFN: `OkinawaDesktopTools.FolderAutomationEngine_j8yefg9jgfh58`
- Package SID: `S-1-15-2-795676864-310991790-2802347502-2718627192-2651328981-310414558-459028798`

These values are historical recorded evidence. The local task must open the
existing Partner Center product and exact-match them. Any difference is HOLD.

## Required local repositories

1. `folder-automation-engine`
   - branch: `codex/folder-standard-consumer-ui-20261026`
   - job: `store/LOCAL_EXISTING_IDENTITY_REVERIFY_JOB_20261116.json`
2. `Windows-Automator`
   - branch: `codex/msix-commercial-contract-20261115`
   - command: `store_manager.cli verify-existing-identity`
3. `Windows-all-auto`
   - branch: `codex/msix-commercial-handoff-20261115`
   - receipt binder: `scripts/apply_identity_reverify_receipt.py`

## Local execution

Use one already-authenticated Partner Center browser tab exposed only to the
approved local CDP endpoint. Do not put cookies, tokens, passwords or browser
profile files in GitHub.

From the Windows-Automator checkout:

```powershell
$job = 'C:\src\folder-automation-engine\store\LOCAL_EXISTING_IDENTITY_REVERIFY_JOB_20261116.json'
$receipt = 'C:\qa\folder-engine\identity-reverify\existing-identity-reverify-receipt.json'
$cdp = $env:PARTNER_CENTER_CDP_URL
pwsh -File .\scripts\run_existing_identity_reverify.ps1 -Job $job -Output $receipt -CdpUrl $cdp
```

Success must be exactly:

`EXISTING_IDENTITY_EXACT_MATCH`

The receipt must prove all write actions remained false.

## Bind the receipt to the Store handoff

From the Windows-all-auto checkout:

```powershell
python .\scripts\apply_identity_reverify_receipt.py `
  --handoff 'C:\src\folder-automation-engine\store\AUTOMATION_UPLOADER_HANDOFF_20261115.json' `
  --receipt 'C:\qa\folder-engine\identity-reverify\existing-identity-reverify-receipt.json' `
  --output 'C:\qa\folder-engine\identity-reverify\store-handoff-after-identity.json'
```

This only advances `identity.live_partner_center_reverified=true`. It does NOT
advance version-history, price, assets, security, draft approval, certification
or publish gates.

## After Identity exact match

Next local/Partner Center work is separate:

1. verify accepted package/version history;
2. choose the current low-price JPY tier and record exact Partner Center value;
3. confirm the Private audience Known User Group;
4. finish asset/security approvals;
5. only then prepare Windows-Automator Draft input.

Certification submission and Publish remain separate owner approvals.
