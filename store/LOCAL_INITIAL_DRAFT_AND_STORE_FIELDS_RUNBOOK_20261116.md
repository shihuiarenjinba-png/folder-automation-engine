# Folder Automation Engine — initial Draft + Store fields local runbook

Updated: 2026-11-16 JST

## Frozen product evidence

- Store ID: `9P99MJX1R4V6`
- Product source: `51597b389384be6cf2b3d85c09ee66099b80807e`
- MSIX SHA256: `911f8eb13abfdbb51bea8f279006d138d6be9cba4a25413416c1d70458676450`
- EXE SHA256: `d53161ea1119445afb8070d989d4a72e8019895b8c5e166738a3e38718b54976`
- Submission state: `EXISTING_PRODUCT_INITIAL_SUBMISSION`
- Submission kind: `new`
- Version: `1.0.0.0`
- Version state: `NO_ACCEPTED_PACKAGE_OBSERVED` / no confirmed conflict

Do not rebuild the product merely because Store metadata commits are newer.

## Owner authorization model

This runbook is evidence and procedure only. It is **not** standing authorization for
any Partner Center write.

Immediately before each external write, require direct execution-time owner approval.
The following are separate gates and approval for one must never be reused for another:

- `Start submission`
- customer-group creation
- pricing save/change
- MSIX upload
- certification submission
- Private-audience publication
- promotional-code generation
- later Public-audience publication

Repository values such as `owner_approved=true` are evidence only.

## Repositories

1. `folder-automation-engine`
   - branch `codex/folder-standard-consumer-ui-20261026`
   - handoff `store/AUTOMATION_UPLOADER_HANDOFF_20261115.json`
   - job `store/LOCAL_INITIAL_SUBMISSION_DRAFT_JOB_20261116.json`
   - observation template `store/LOCAL_INITIAL_DRAFT_OBSERVATION_TEMPLATE_20261116.json`
2. `Windows-all-auto`
   - branch `codex/msix-commercial-handoff-20261115`
3. `Windows-Automator`
   - branch `codex/msix-commercial-contract-20261115`

## Stage 0 — exact-package local final QA receipt

Before preparing any Automator input, prove that the downloaded frozen package is the
same package that passed local Windows acceptance.

After syncing `Windows-all-auto` to its current Group B handoff branch, run its
generic static preflight:

```powershell
$preflightOut = Join-Path $work 'exact-package-preflight'
Set-Location $allAuto
pwsh -File .\scripts\run_local_exact_package_preflight.ps1 `
  -ProductRepoPath $folderRepo `
  -PackagePath $msix `
  -HandoffPath $handoff `
  -MainExeName 'FolderAutomationEngine.exe' `
  -OutputDirectory $preflightOut `
  -RunSelfTest
```

Then create the bound QA receipt template:

```powershell
$qaReceipt = Join-Path $work 'local-final-qa-receipt.json'
python .\scripts\create_local_final_qa_receipt_template.py `
  --handoff $handoff `
  --output $qaReceipt
```

Attempt physical JP/EN, DPI, copy/move, safety, restart/normal-exit acceptance only
if the exact unsigned executable can run without weakening Windows security.

If Windows Application Control blocks the exact executable, record the block and stop.
Do **not** change policy, add a temporary certificate, or use a bypass. In that case,
keep `local-final-qa-receipt/1` as HOLD and use the Windows-all-auto
`pre-store-static-qa-receipt/1` path to enter the limited Private Store signing lane.

If the unsigned executable naturally runs, set `status=PASS` and the required
booleans true only after the physical checks actually pass. Keep
`package_rebuilt=false` and `security_bypass_used=false`.

Apply the receipt only for a real physical PASS:

```powershell
$handoffAfterQa = Join-Path $work 'store-handoff-after-local-qa.json'
python .\scripts\apply_local_final_qa_receipt.py `
  --handoff $handoff `
  --receipt $qaReceipt `
  --output $handoffAfterQa
$handoff = $handoffAfterQa
```

A receipt with a different source SHA/MSIX SHA is rejected. Do not rebuild the frozen
candidate merely to make QA pass.

## Stage A — prepare the HOLD Automator input

Use the exact local MSIX path already verified against the frozen SHA.

```powershell
$folderRepo = 'C:\Users\aaron\Desktop\portfolio-audit\_task_worktrees\folder-automation-engine'
$allAuto = 'C:\Users\aaron\Desktop\portfolio-audit\_task_worktrees\Windows-all-auto'
$automator = 'C:\Users\aaron\Desktop\portfolio-audit\_task_worktrees\Windows-Automator'
$work = 'C:\Users\aaron\Desktop\portfolio-audit\STORE_UPLOAD_ASSETS_20261019\FolderAutomationEngine\local-store-preflight-20261116'
$msix = 'C:\Users\aaron\Desktop\portfolio-audit\_group_b_store_qa_20261024\artifacts\FolderAutomationEngine\ci-51597b3\FolderAutomationEngine-Store-MSIX-UNSIGNED-DRAFT\store-out-43697191105\FolderAutomationEngine_1.0.0.0_x64_StoreDraft_UNSIGNED.msix'
$images = Join-Path $work 'store-images'
$handoff = Join-Path $folderRepo 'store\AUTOMATION_UPLOADER_HANDOFF_20261115.json'
$automatorInput = Join-Path $work 'windows-automator-input-initial-draft-HOLD.json'

Set-Location $allAuto
python .\scripts\prepare_store_automator_input.py `
  --handoff $handoff `
  --package-path $msix `
  --images-dir $images `
  --output $automatorInput `
  --allow-hold
```

Expected: `HOLD`. That is normal before pricing/group/security/assets are completed.

## Stage B — create only the initial Partner Center Draft

Prerequisites:

- exactly one already-authenticated Partner Center tab;
- the tab belongs to the existing product `9P99MJX1R4V6`;
- CDP endpoint is local and approved;
- no token/cookie/profile data is written to GitHub.

```powershell
$job = Join-Path $folderRepo 'store\LOCAL_INITIAL_SUBMISSION_DRAFT_JOB_20261116.json'
$draftReceipt = Join-Path $work 'initial-submission-draft-receipt.json'
$cdp = $env:PARTNER_CENTER_CDP_URL

Set-Location $automator
pwsh -File .\scripts\run_initial_submission_start.ps1 `
  -Input $automatorInput `
  -Job $job `
  -Output $draftReceipt `
  -CdpUrl $cdp
```

Success must be exactly:

`INITIAL_SUBMISSION_DRAFT_CREATED`

The receipt must contain a numeric `draft_id` and prove:

- created_or_reserved_product = false
- submission_started = true
- start_submission_clicked = true
- start_update_clicked = false
- package_uploaded = false
- pricing_changed = false
- submitted = false
- published = false

Any ambiguous result is HOLD. Do not retry Start submission blindly.

### Ambiguous Start submission recovery

If the UI driver/Computer Use layer reports an unknown result, do **not** switch to a
screen-coordinate click and do not immediately repeat the action.

Use the Windows-Automator read-only reconciliation path:

```powershell
$reconcileReceipt = Join-Path $work 'initial-submission-reconcile-receipt.json'
Set-Location $automator
pwsh -File .\scripts\reconcile_initial_submission_attempt.ps1 `
  -Input $automatorInput `
  -Output $reconcileReceipt `
  -CdpUrl $cdp
```

Interpret exactly:

- `INITIAL_SUBMISSION_DRAFT_PRESENT_RECOVERED`: a Draft exists; bind that Draft and never click Start submission again.
- `INITIAL_SUBMISSION_NOT_OBSERVED_RETRY_REQUIRES_NEW_APPROVAL`: live state is still initial; stop and request a **new** execution-time owner approval before retrying.
- `HOLD_AMBIGUOUS_WRITE`: stop. No retry.

This reconciliation is read-only and never grants retry authorization by itself.
Partner Center writes must stay on the selector/state-based Windows-Automator path;
coordinate clicking is not part of the approved Store automation route.

## Stage C — bind the Draft receipt to the Store handoff

```powershell
$handoffAfterDraft = Join-Path $work 'store-handoff-after-initial-draft.json'

Set-Location $allAuto
python .\scripts\apply_initial_submission_receipt.py `
  --handoff $handoff `
  --receipt $draftReceipt `
  --output $handoffAfterDraft
```

Only the Draft binding should advance. Package upload, price, security, certification and Publish remain HOLD.

## Stage D — collect Partner Center values without writing them

Copy `store/LOCAL_INITIAL_DRAFT_OBSERVATION_TEMPLATE_20261116.json` into the local work directory and fill only values actually observed in the new Draft.

Read the following sections:

### Pricing and availability

- record every visible JPY/base-price choice needed to identify the low-cost tier;
- do not infer a tier from memory;
- keep selected value null until the owner-approved low-price choice is known;
- confirm that `7 days` is available as the trial choice;
- do not save pricing yet.

Microsoft currently supports free or a Store price tier, and time-limited trials of 1/7/15/30 days. The 7-day trial may provide full functionality.

### Properties

- record the visible app categories;
- preferred candidate: `Utilities + tools` if that exact current option exists;
- otherwise record the available choices and HOLD rather than inventing a category;
- do not save a category until confirmed.

### Customer groups / Private audience

- inspect `Engage > Customer groups`;
- record existing groups;
- do not create a group without the exact group name and Microsoft-account membership to use;
- if no group exists, retain `HOLD_PRIVATE_AUDIENCE_GROUP_REQUIRED`.

Known user groups use the email address associated with a Microsoft account and can target a private audience. Group names cannot later be removed/renamed, so creation is a separate deliberate write.

### Store listing

Use the checked-in copy as the source:

- `store/STORE_LISTING_DRAFT_JA_EN.md`
- `store/PRIVACY_POLICY.md`

Do not silently rewrite claims. Verify that the current app still supports every listed feature.

### Security / Submission options

Bind answers to MSIX SHA:

`911f8eb13abfdbb51bea8f279006d138d6be9cba4a25413416c1d70458676450`

Existing engineering observations:

- local file/folder access: yes
- external API/cloud communication: no
- external account requirement: no
- camera: no
- microphone: no
- location: no
- restricted capability: yes (`runFullTrust`)
- non-Microsoft driver/NT service dependency: no

`runFullTrust` draft explanation source:

`store/RUNFULLTRUST_JUSTIFICATION.md`

Personal-data declaration and final runFullTrust explanation remain owner-confirmed fields. Do not guess.

## Stage E — observation output

Save the filled observation as:

`store-initial-draft-observation-filled.json`

Keep `pricing_write_performed`, `properties_write_performed`, `customer_group_write_performed`, and `security_write_performed` false in this collection stage.

## Stage F — rerun validation

After the owner-selected exact price, category, private-audience group, listing/privacy/support decisions, assets and security answers have been incorporated into the Store handoff, regenerate the Automator input without `--allow-hold`.

Then run:

1. Windows-Automator `validate`;
2. Windows-Automator `night-run --execution-mode dry_run`;
3. confirm no Partner Center mutation;
4. require `READY_FOR_AUTOMATOR_DRAFT` before any package upload.


## Stage G — Microsoft Store signing without buying the paid app

The production signing strategy is Microsoft Store signing. Do not buy a separate CA
code-signing certificate solely for this Store release.

For this paid Folder product, a Private audience tester would normally be charged the
configured price. Therefore the owner must **not** be required to purchase their own
app merely to perform the final signed-build QA.

Preferred no-purchase test route after the Private-audience submission has completed
certification and the product has reached the Store publishing phase:

1. keep the app restricted to the selected Private audience;
2. verify that the owner's **personal Microsoft account** is a member of the selected
   known-user group;
3. once Partner Center makes promotional codes available for the published product,
   generate a promo code only under separate execution-time owner approval;
4. redeem that code with the same personal Microsoft account;
5. acquire/install the Microsoft Store-delivered signed package for free;
6. perform final JP/EN, DPI, copy/move, safety, restart and normal-exit QA;
7. bind the result with Windows-all-auto `store-signed-install-qa-receipt/1`.

A promotional code is not expected to work before the product completes the publishing
phase. Do not temporarily change the paid product to Free just to avoid a test purchase
unless the owner explicitly chooses that commercial change.

For ordinary Windows MSIX apps, there is no Xbox/GDK-style development sandbox to use
as a drop-in replacement for this Store test lane. GDK/Xbox development sandboxes are
game-specific. Package flights become useful after the base app has already been
published; they are not the first-release substitute for this Private-audience pilot.

## Stage H — signed Store build acceptance

After the promo-code acquisition succeeds, test the Store-installed build itself.
Record at minimum:

- Microsoft Store delivery verified;
- trusted Microsoft Store signature verified;
- Store ID / Identity / Version still match;
- JP and EN GUI;
- DPI 100 / 125 / 150%;
- Preview / Dry Run;
- approved copy and move;
- no-overwrite behavior;
- symlink/junction safety;
- restart and normal exit.

Only after this signed-build QA is PASS may the product advance to
`READY_FOR_PUBLIC_RELEASE_APPROVAL`.

## Separate later gates

Do NOT treat Draft creation as authorization for:

- MSIX upload;
- Pricing Save;
- Customer group creation;
- Submit for certification;
- Publish.

Those remain separate actions. Public release also remains blocked until Store-signed install QA and final public screenshots are complete.
