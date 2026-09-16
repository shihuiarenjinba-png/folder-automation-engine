# Sales release checklist / 販売直前チェック

## Automated / code gates

- [x] Root confinement and path validation
- [x] Destination collision does not mark the source as processed
- [x] Dry Run has no copy/move/processed side effects
- [x] SQLite busy timeout and processed-state regression tests
- [x] Explicit **`言語 / Language`** selector with persisted `日本語` / `English`
- [x] UI-language source/round-trip tests
- [x] Japanese and English user guides

## Real Windows release gates / 実機確認

- [ ] Windows 10 smoke test
- [ ] Windows 11 smoke test
- [ ] Switch 日本語 → English → 日本語 and verify all ordinary controls/status text remain understandable
- [ ] Restart the app and verify the selected language is retained
- [ ] Check 100%, 125%, and 150% display scaling for clipped controls/text
- [ ] Validate a known-good config and a deliberately invalid config
- [ ] Run Dry Run against a controlled folder and verify there are no file/state changes
- [ ] Run a real copy/move test inside a temporary root
- [ ] Create a destination collision and verify the source remains unprocessed and retryable
- [ ] Run monitoring long enough to cover multiple polling cycles; stop/restart cleanly
- [ ] Verify unexpected shutdown does not corrupt the state DB
- [ ] Build the packaged Windows executable and run it from a path containing spaces/non-ASCII characters
- [ ] Run Windows Defender/AV scan and record release SHA-256
- [ ] Prepare LICENSE/NOTICE/SBOM and lock release versions
- [ ] Sign the final installer/executable if distributed commercially

Do not mark the product sales-ready until every applicable unchecked item has been completed on a controlled Windows machine.

未チェック項目が残っている間は「販売完成」と扱いません。
