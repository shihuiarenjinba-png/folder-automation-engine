# Folder Automation Engine — safe file operations QA handoff

**Status: HOLD.** The safety draft branch is not ready for Microsoft Store submission.

## Changes (2026-10-18)
- File operations now stage content in the destination folder before publishing.
- For default `overwrite=false`, publication uses an atomic exclusive link. If a
  competing program creates the destination after the initial check, the existing
  file is preserved and the source remains retryable.
- `overwrite=true` performs an atomic replacement after copying to a temporary
  file; the old file is not removed before copying is complete.
- Copy/move source metadata are rechecked, and the source is not removed if
  it changed during staging or publication.
- New tests simulate a racing writer, staging failure, and changing source.

### Operator commands (isolated Windows checkout)
```powershell
python -m compileall -q folder_automation.py tests/test_folder_automation_safety.py
python -m unittest discover -s tests -v
python folder_automation.py config.example.json --once --dry-run
```

Manual tests: nonempty conflicting destination; same-directory move; interrupted
staging; 0-byte files; Unicode/long paths; network drives and OneDrive sync;
NTFS and FAT/exFAT (unsupported atomic hard links must fail closed);
filesystem permissions; symlinks/junctions; restoration of files after failure.
Use throwaway directories only.

**GitHub CI blocker:** workflow runs on this branch fail before any job steps
are exposed (jobs show steps null/empty and logs unavailable). Treat as
unverified CI/infrastructure until repository Actions settings/usage,
permissions and runner scheduling are inspected by the code operator.
Do not mark tests PASS based on these runs.

This repository mixes a file automation engine with an independently launched
backup verifier GUI. Decide actual product scope and customer onboarding
before booking any Microsoft Store name; avoid promising an integrated GUI.
No main/release modifications or actual customer file tests.
