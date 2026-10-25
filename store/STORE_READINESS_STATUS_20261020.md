# Store readiness status — updated 2026-10-25 JST

**HOLD / NOT READY FOR STORE UPLOAD, CERTIFICATION OR SALE**

Branch: `codex/folder-standard-store-qa-20261024`

Verified parent HEAD before this QA update: `1203d6ac8ef1c56f6f11e6a510ec30dd737a0400`

Draft PR: #9 (must remain unmerged until owner approval)

## Verified evidence

- Existing Windows artifact ID: `12552836022`; recorded EXE SHA256: `1D29688199BA0FE6BD0EAC16351F2244B8AB02D865305F7F23805219613098F0`.
- Existing unsigned MSIX artifact ID: `12552746305`; recorded MSIX SHA256: `782CC7FD6307A2F4BA877D512F240D62A2D9173D2C66AC2162B8419F273AC14C`.
- The above EXE was hash-checked and launched under the separate, limited owner authorization. Windows Code Integrity blocked process creation; no GUI process ran and no test data changed.
- Saved blocker: Code Integrity events 3077/3033, Policy ID `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`. No Windows security setting, policy, registry key or certificate store was changed.
- Source tests on 2026-10-25: 60 run, 57 PASS, 3 SKIP. The three SKIPs are the explicitly retained symbolic-link tests because the current standard-user token cannot create symbolic links.
- PowerShell parsing, Python compilation and repository diff checks: PASS.
- Safe-close repair added after the parent HEAD: when a copy/move worker or watcher is active, window close now signals the watcher and waits for the current operation to reach its safe boundary before destroying the GUI. Three no-window regression tests pass.
- A disposable GitHub-hosted Windows-only GUI-window screenshot smoke is staged. Its JSON explicitly records `human_interactive_qa=false`, `store_listing_eligible=false` and `release_approved=false`.

## Identity and package state

Repository candidate values remain:

- Store ID: `9P99MJX1R4V6`
- Identity Name: `OkinawaDesktopTools.FolderAutomationEngine`
- Publisher: `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`
- Candidate PFN: `OkinawaDesktopTools.FolderAutomationEngine_j8yefg9jgfh58`
- Technical draft version: `1.0.0.0`

These values must be copied again from the live Partner Center product before any upload. The current package builder produces an **unsigned technical draft** and uses unapproved placeholder artwork.

## Readiness gates

| Stage | State | Reason |
|---|---|---|
| Source / static QA | PASS WITH 3 SKIPS | 57/60 pass; symbolic-link cases remain untested on this token |
| Fresh Windows CI artifact | PENDING | Must run from the new exact commit and publish new hashes |
| Automated CI GUI smoke | PENDING | Runner result and screenshot have not yet been produced |
| Human Windows GUI QA | BLOCKED | Owner PC launch blocked by Code Integrity; no bypass is permitted |
| Genuine Store screenshots | NOT TESTED | Must come from an accepted installed candidate, not CI evidence |
| MSIX install / Start launch | NOT TESTED | Existing draft is unsigned; no install approval is implied |
| WACK | NOT TESTED | No report exists for the current candidate |
| Partner Center package upload | HOLD | Fresh identity, final icon, human QA, WACK and owner upload approval are missing |
| Certification submission / publication | HOLD | Separate explicit owner approval required |

## Submission safeguards

- Do not disable or weaken Smart App Control, WDAC, Code Integrity, Defender or SmartScreen.
- Do not install certificates or packages on the owner PC under this document.
- Microsoft Standard Application License Terms remain the proposed default; legal/owner review is still required.
- Privacy text may be entered directly when Partner Center offers that option, but current Store policy may require a public URL when personal information is accessed. Confirm the live form before submission.
- Japan and United States and all price figures remain unapproved proposals. Avoid automatic market expansion.
- Select the Partner Center publishing hold so certification does not cause unintended automatic publication.
- Final icon/logo rights, production package artwork, support contact and privacy-policy destination remain unresolved.
