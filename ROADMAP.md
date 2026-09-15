# Roadmap

## Phase 1 — Safe Folder Core（現在）

- folder polling
- glob rules
- copy / move
- SQLite processed-state
- `root_dir` path boundary
- Dry Run
- default no-overwrite

## Phase 2 — Robust File Handling

- file-size stability check before processing
- rename templates
- archive / date-folder rules
- quarantine folder
- failure log / retry

## Phase 3 — Existing Tool Adapters

- PDF Privacy Toolkit Adapter
- Excel/CSV Privacy Cleaner Adapter
- Image Privacy Cleaner Adapter
- Document Extractor Adapter
- Local Report Maker Adapter

Adapters are explicit and deterministic; arbitrary shell-command execution is not part of the default design.

## Phase 4 — Windows Product

- tray/service mode
- folder picker GUI
- rule editor
- start-with-Windows option
- signed portable/installer build

## Release Gate

Representative fixtures, duplicate-processing tests, crash/restart tests, path-boundary tests, egress audit, Windows 10/11 smoke tests.
