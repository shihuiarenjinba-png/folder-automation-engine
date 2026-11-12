# Folder Automation Engine — path to STORE_UPLOAD_READY

Updated: 2026-11-13 JST

Use this order. A later step cannot turn an earlier FAIL into PASS.

1. **Freeze exact candidate** — PR #10 HEAD, clean tree, successful Windows/Ubuntu/safety workflows.
2. **Rebuild exact artifacts** — Windows EXE + unsigned Store MSIX from the same HEAD; verify EXE hash equals MSIX-unpacked EXE; preserve ZIP hashes, package inventory and third-party notices.
3. **Human Windows acceptance** — with action-time approval for that exact EXE SHA256: JP/EN, saved language/config, Dry Run, cancel=0 writes, copy/move hashes, collisions, stale preview, watcher, safe close, keyboard, 1024×768 / 1280×720, DPI 100/125/150%.
4. **Capture Store artwork** — genuine product screenshots from the accepted GUI; no CI runner desktop, secrets or private paths. Owner visually approves the repository-generated icon or an approved replacement.
5. **Partner Center re-copy** — use the existing product; re-copy Store ID, Identity Name, Publisher, PFN and accepted version history. Do not create a duplicate product.
6. **Commercial metadata** — owner approves JP/EN listing, price, markets, age rating answers, privacy text/URL as required by the live form, support contact and legal terms.
7. **Optional WACK precheck** — run on the exact candidate when a valid environment is available. Record result. Official Store certification remains the authoritative certification step.
8. **Build submission bundle** — fill `store/SUBMISSION_AUTOMATION_TEST_INPUT_DRAFT_20261026.json` with exact final paths/hashes/evidence. Never invent missing answers.
9. **Fail-closed validation** — run `python qa/validate_store_submission_bundle.py <bundle.json> --require-ready`. It must output `STORE_UPLOAD_READY` with an empty missing list.
10. **Automatic uploader test** — `VALIDATE_ONLY` then non-mutating `DRY_RUN`.
11. **Owner upload approval** — only after the above evidence is reviewed.
12. **Upload package** — upload only; keep certification submission and publication disabled/held.
13. **Certification approval** — separate owner approval.
14. **Publish approval** — only after certification success and final Store-side inspection.

**The product is a completed engineering candidate only when steps 1–8 are materially complete. It becomes STORE_UPLOAD_READY only at step 9 plus owner upload approval.**
