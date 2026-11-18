# Folder Automation Engine — UI quality hold before Store upload

Date: 2026-11-18

## Decision

The current Store screenshots are **not approved** for publication. The existing
consumer UI is functionally improved but still looks too close to a default
Tkinter/ttk utility for a paid Store product.

Status:

`HOLD_UI_QUALITY`

This hold supersedes the previous conditional upload approval for the frozen
MSIX SHA:

`911F8EB13ABFDBB51BEA8F279006D138D6BE9CBA4A25413416C1D70458676450`

Do not upload that package as the final sales candidate.

## UI correction

A visual-only polish change was applied at:

`bb0b1a161308170781088dd899ab0d4b2ddb3e42`

The change preserves the Folder workflow and safety behavior while improving:

- whitespace and overall window size;
- visual hierarchy;
- a Store-ready header/hero area;
- card-like grouping;
- typography;
- primary/secondary action emphasis;
- result/log panel presentation;
- neutral background and consistent surfaces.

No file-operation policy or business logic is intentionally changed by this UI
polish.

## Required next candidate flow

Because product source bytes changed, create a new exact Store candidate:

1. run source/unit/safety/UI tests;
2. build Windows artifact;
3. build unsigned Store MSIX from the polished source;
4. record new source SHA, EXE SHA, MSIX SHA, workflow run and artifact IDs;
5. perform pack/unpack/manifest/EXE binding checks;
6. recapture real JP/EN Store screenshots from the new candidate;
7. perform visual owner review;
8. re-run the deterministic Store pre-upload gate against the same recovered
   Partner Center Draft;
9. only after all checks pass, create a **new** exact-package upload approval.

Start submission must not be repeated. Certification and Publish remain separate
later gates.

## Store screenshot acceptance target

Do not approve screenshots merely because they meet pixel dimensions. They must
show a UI that looks intentionally designed and understandable to a first-time
buyer:

- one clear main action hierarchy;
- no crowded/default-widget appearance;
- consistent spacing;
- readable Japanese/English;
- visible preview-before-run safety flow;
- no debug/internal text;
- no private data;
- screenshots must come from the exact rebuilt candidate.
