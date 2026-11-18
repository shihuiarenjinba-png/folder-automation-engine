# Folder Automation Engine — Store readiness status

Updated: 2026-11-16 JST

**Current decision: PRODUCT / MSIX ENGINEERING PASS / LOCAL STORE EXECUTION HOLD / CERTIFICATION HOLD / PUBLICATION HOLD**

Repository: `shihuiarenjinba-png/folder-automation-engine`  
Branch: `codex/folder-standard-consumer-ui-20261026`  
Draft PR: #10 (must remain unmerged until owner approval)

## Frozen upload candidate

The Store upload candidate is intentionally frozen to product source
`51597b389384be6cf2b3d85c09ee66099b80807e`.

- Store ID: `9P99MJX1R4V6`
- Identity Name: `OkinawaDesktopTools.FolderAutomationEngine`
- Publisher: `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`
- PFN: `OkinawaDesktopTools.FolderAutomationEngine_j8yefg9jgfh58`
- Technical package version: `1.0.0.0`
- Frozen MSIX SHA256: `911f8eb13abfdbb51bea8f279006d138d6be9cba4a25413416c1d70458676450`
- Frozen EXE SHA256: `d53161ea1119445afb8070d989d4a72e8019895b8c5e166738a3e38718b54976`

PR #10 HEAD `4be9bad467478f66a8a51f18d4a5245e90d69929` is 10 commits ahead of the
frozen product source, and the GitHub compare contains only Store metadata/runbook
files. No application source or packaging implementation changed in that range.
Therefore later metadata-only commits do not invalidate the frozen product package.
Any future application, packaging, runtime-notice, manifest, identity, or packaged
asset change MUST invalidate this exception and require a new frozen package/hash.

## Exact-head CI evidence

At PR #10 HEAD `4be9bad467478f66a8a51f18d4a5245e90d69929`:

- Guided folder GUI and safe copy/move tests — run `43788248647`: SUCCESS
  - Ubuntu: 58 tests, 4 skipped + 4 preference tests, PASS
  - Windows: same workflow matrix, PASS
- Folder automation safety regression — run `43788248665`: SUCCESS
  - 14 tests, 2 skipped, PASS
- Folder desktop and unsigned Store draft — run `43788248654`: SUCCESS
  - 87 tests, PASS
  - frozen EXE self-test: PASS
  - packaged GUI startup evidence: PASS
  - real JP/EN Store listing capture: PASS, minimum 1366×768
  - unsigned MSIX build + MakeAppx pack/unpack: PASS
  - manifest identity/source/hash/EXE roundtrip guards: PASS

This CI evidence is engineering evidence only. It does not authorize Partner Center
writes, certification, or publication.

## Engineering state

Completed or implemented:

- consumer-first JP/EN GUI with guided folder selection, Dry Run, approval-gated copy/move, visible result history, settings reload, advanced rules and optional watcher;
- fail-closed no-overwrite, stale-preview invalidation, staged copy/move safety and safe application close;
- symbolic-link and Windows junction rejection for root/input/output/state paths and GUI folder selection;
- additional rejection of a link/junction hidden in any lexical ancestor of the selected root path;
- pinned Windows packaging toolchain: Python 3.12.10 / PyInstaller 6.22.3 and exact packaging dependencies;
- exact third-party runtime license evidence copied into the packaged payload;
- complete staged package file/SHA256 inventory generated for each MSIX build;
- deterministic repository-generated folder/arrow icon candidate with no external artwork dependency;
- fail-closed Store submission bundle validator;
- initial-submission handoff/runbook for an existing Store product with no accepted package history.

## Live Partner Center state already observed

Repository evidence records:

- existing product identity exact-match reverified;
- submission state: `EXISTING_PRODUCT_INITIAL_SUBMISSION`;
- submission kind: `new`;
- version state: `NO_ACCEPTED_PACKAGE_OBSERVED`;
- no confirmed version conflict for `1.0.0.0`;
- initial Draft receipt does not yet exist.

These observations are evidence, not continuing authorization. Live Partner Center
state must be rechecked immediately before any write.

## Readiness gates

| Gate | State | Close condition |
|---|---|---|
| Source / automated safety | PASS | rerun if product/application/package code changes |
| Windows EXE / unsigned MSIX engineering | PASS | frozen package remains bound to source/SHA above |
| Toolchain reproducibility | PASS | pinned build and recorded versions verified |
| Runtime notices / inventory | PASS FOR FROZEN CANDIDATE | reverify if packaged contents change |
| Pre-Store CI GUI / filesystem safety | PASS | does not substitute for Store-signed human QA |
| Private-audience listing screenshots | CAPTURE PASS / OWNER REVIEW HOLD | owner accepts JP/EN 1366×768+ candidates |
| Partner Center identity / initial-submission state | READ-ONLY REVERIFY PASS | recheck immediately before Draft write |
| Local execution environment | HOLD | sync Folder + Windows-all-auto + Windows-Automator to required heads and run local tests |
| Initial Partner Center Draft | NOT EXECUTED | direct execution-time approval + exact state recheck + one Start submission |
| Price / category / customer group / security fields | HOLD | read from the created Draft; do not infer |
| PRIVATE_AUDIENCE_UPLOAD_READY | HOLD | complete Store fields, VALIDATE_ONLY, DRY_RUN, then separate upload approval |
| Store-signed human Windows QA | HOLD | complete after Private audience certification and Store signing |
| Public-release screenshots | HOLD | confirm/replace from Store-signed installed candidate |
| Final icon visual approval | HOLD | owner accepts generated icon or approved replacement |
| WACK local precheck | OPTIONAL / PENDING | official Store certification remains authoritative |
| Certification submission | HOLD | separate explicit owner approval after upload validation |
| Publication | HOLD | certification success plus separate explicit owner publish approval |

## Next execution order

1. Sync the three local worktrees to the required GitHub heads without merging main/release.
2. Re-run local tests and verify the frozen MSIX SHA256 exactly.
3. Re-read Partner Center and require exactly `EXISTING_PRODUCT_INITIAL_SUBMISSION`.
4. With direct execution-time approval, create exactly one initial Draft using `Start submission`.
5. Bind the Draft receipt to Store ID/source/package SHA.
6. Read price tier, category, customer groups and security/submission options without saving them.
7. Incorporate owner-confirmed values and run `VALIDATE_ONLY`.
8. Run `DRY_RUN` with no Partner Center mutation.
9. Require a separate owner approval before MSIX upload.
10. Keep certification submission and Publish as separate later gates.

## Signing path

The Store route remains MSIX. For Microsoft Store distribution, a CA-trusted signing
certificate is not required before submission; Microsoft signs/re-signs the MSIX
during Store publishing after certification. Do not weaken Windows security controls
or install ad-hoc trust certificates merely to force local execution.
