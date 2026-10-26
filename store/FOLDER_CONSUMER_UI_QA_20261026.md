# Folder Automation Engine — Consumer UI acceptance (2026-10-26)

**DRAFT / SALE HOLD.** Regular Folder Automation Engine only, not `-2`.
Base (exact latest existing QA HEAD): `1a98a6e725f21c248dfd230e03bf4811fbf2dcf2`.

## Implemented on isolated UI branch

- The preview/result history is docked beneath a scrolling settings panel, so scrolling and optional advanced rules cannot hide the result area.
- First-run steps and field names explain the required parent and source/destination subfolders. Source and destination now have browse buttons.
- Browsing only accepts existing real **direct child** directories of the selected parent. Nested folders, symlinks/junctions and unrelated locations are refused; no directories are created automatically.
- Main execution button has a clear visual distinction and is **disabled until a successful Dry Run**. Changing source/destination/pattern/action revokes the existing approval immediately.
- Copy/move are displayed as localized Japanese/English choices while the engine keeps literal `copy`/`move` configuration data.
- Common file patterns are dropdown suggestions; filename patterns remain editable for experienced users.
- Optional watcher and multi-rule editor are collapsed under **Advanced rules and watching** on first launch. Watch indicator remains visible outside that section.
- No change to underlying copy/move/write/overwrite/symlink safety or filesystem path model.

## What these changes do NOT establish

- Actual Windows 11 human-interactive JP/EN usability acceptance, DPI 100/125/150% layout, keyboard accessibility, and full file copy/move through the GUI remain **NOT TESTED**.
- CI screenshots must not be passed off as genuine Store listing screenshots. Final desktop images must be captured from installed app on suitable environment.
- `main` and release branches stay unchanged; existing QA Draft PR #9 stays unmerged. New UI Draft PR targets only the isolated QA branch.
- Previous Code Integrity policy on owner PC remains untouched; no EXE/MSIX was launched or installed locally under this UI task.
- Current Store Identity/Version, signed MSIX install/update/uninstall, WACK, icons, third-party notices and Partner Center remain **HOLD**.

## Manual acceptance scenarios for code operator

1. Clean launch in Japanese. Result box remains visible while scrolling main options at 1024×768 and 1280×720.
2. Select parent; use **Choose** to pick `inbox` and `processed` direct child folders. Attempt selection outside parent or nested folder and require clear refusal.
3. Choose `*.csv`, copy. Run button disabled before Dry Run, enabled after safe preview, and disabled again when changing any field.
4. Review matched count and list; reject live confirmation, ensure zero writes; approve with synthetic data and verify hashes; no overwrite.
5. Switch language English/Japanese and confirm readable labels and persisted language. Saved rules still reload safely.
6. Expand advanced controls: up to 10 ordered rules and opt-in watcher work with prior approval requirements, watcher state remains visible.
7. Watch safe close during a file operation, normal exit, and 100%, 125%, 150% DPI. Collect genuine screenshots and all error cases.
8. Rebuild MSIX from exact candidate SHA. Do not reuse SHA256 or Store approval flags from earlier package.

**Technical QA and Store sale readiness are distinct; do not mark sale GO based on CI.**
