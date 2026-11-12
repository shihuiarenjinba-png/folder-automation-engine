# Folder Automation Engine — Store readiness status

Updated: 2026-11-13 JST

**Current decision: ENGINEERING PREP IN PROGRESS / STORE UPLOAD HOLD / CERTIFICATION HOLD / PUBLICATION HOLD**

Repository: `shihuiarenjinba-png/folder-automation-engine`  
Branch: `codex/folder-standard-consumer-ui-20261026`  
Draft PR: #10 (must remain unmerged until owner approval)

Exact final candidate evidence must always be read from the latest successful PR #10 workflow run and its artifacts. Do not reuse older EXE/MSIX hashes after a source or documentation commit.

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
- fail-closed Store submission bundle validator for the future automatic upload pipeline.

## Store package identity record

Repository record (must be re-copied from the live existing Partner Center product before upload):

- Store ID: `9P99MJX1R4V6`
- Identity Name: `OkinawaDesktopTools.FolderAutomationEngine`
- Publisher: `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`
- Candidate PFN: `OkinawaDesktopTools.FolderAutomationEngine_j8yefg9jgfh58`
- Technical package version: `1.0.0.0`

The repository record is evidence, not authorization. Previous accepted Store version/history remains a live Partner Center check.

## Readiness gates

| Gate | State | Close condition |
|---|---|---|
| Source / automated safety | PENDING EXACT-HEAD RERUN | latest branch HEAD passes Windows + Ubuntu + safety tests |
| Windows EXE / unsigned MSIX build | PENDING EXACT-HEAD RERUN | latest HEAD build, GUI smoke, self-test, pack/unpack, inventory and hashes all PASS |
| Toolchain reproducibility | IMPLEMENTED | pinned build completes with recorded versions |
| Runtime notices / inventory | IMPLEMENTED, VERIFY ON FINAL ARTIFACT | final package contains notices and inventory matches exact HEAD |
| Human Windows GUI / filesystem QA | HOLD | approved exact EXE passes JP/EN, Dry Run, synthetic copy/move, watcher, keyboard and DPI checks |
| Genuine Store screenshots | HOLD | real installed/accepted candidate screenshots captured at current Store-compliant dimensions |
| Final icon visual approval | HOLD | owner accepts generated original icon or supplies an approved replacement |
| Partner Center identity/version history | HOLD | copied from the live existing product and reconciled with package |
| Privacy / support / price / markets / age rating | HOLD | owner-approved final commercial values entered into submission bundle |
| WACK local precheck | OPTIONAL / PENDING | recommended pre-submission check if available; official Store certification remains authoritative |
| STORE_UPLOAD_READY | HOLD | all mandatory bundle fields pass `qa/validate_store_submission_bundle.py --require-ready` and owner separately approves upload |
| Certification submission | HOLD | separate explicit owner approval after upload validation |
| Publication | HOLD | certification success plus separate explicit owner publish approval |

## Signing path

The Store route remains MSIX. For Microsoft Store distribution, a CA-trusted signing certificate is not required before submission; Microsoft signs/re-signs the MSIX during Store publishing after certification. Do not weaken Windows security controls or install ad-hoc trust certificates merely to force local execution.

## Automation safeguard

The upload automation must consume `folder-standard-store-submission-smoke-v2`. It must run:

1. static package/hash/identity validation;
2. `VALIDATE_ONLY`;
3. `DRY_RUN` without Partner Center mutation;
4. owner upload approval;
5. package upload only.

Certification submission and Publish are separate approval phases and must never be implied by upload success.
