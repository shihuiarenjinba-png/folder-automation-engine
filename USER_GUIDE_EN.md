# Folder Automation Engine — User Guide

## First use

Use **`言語 / Language`** in the upper-right corner to choose `日本語` or `English`. The selection is saved and reused on the next launch.

This app only processes folders and rules explicitly allowed by its JSON configuration. The normal workflow is:

1. Choose a configuration JSON.
2. Use `Validate` to check it.
3. Use `Dry Run Once` to inspect the result without copying/moving files.
4. If the preview is correct, use `Run Once` or `Start Monitor`.

## Safety behavior

- Dry Run does not copy/move files and does not mark them as processed.
- If a destination already exists and overwrite=false, the source is not marked processed.
- The source can be retried after the collision is resolved.
- Output is confined to the configured root.
- The app does not provide arbitrary shell or command execution.

## Before sale

Use `SALES_RELEASE_CHECKLIST.md` for final release checks. Run real Windows 10/11 smoke tests, 100/125/150% display scaling, Japanese↔English switching, long-running monitoring, collision recovery, packaged EXE validation, and AV scanning.
