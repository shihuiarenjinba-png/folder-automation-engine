# Folder Automation Engine — guided desktop prototype

**Status: DRAFT / HOLD.** This is not a Microsoft Store-ready installer.

## 何をするアプリ？
指定したメインフォルダー内の「inbox」などの取り込み用フォルダーから、
`*.pdf` のようなファイル名条件で、別の「processed」フォルダーなどへ
**コピーまたは移動**するWindows用オフラインアプリです。

### 最初の操作
1. `python folder_desktop_app.py` で画面を開きます。
2. 「基準フォルダーを選ぶ」で自分の空のテストフォルダーを選びます。
3. 入力・出力フォルダー名、`*.pdf` などの条件と `copy` / `move` を確認。
4. **試運転（変更なし）**を押す。対象ファイルが画面に表示されます。
5. 内容に問題がなければ**確認して1回実行**を押して承認します。

**初期設定では copy が選択され、既存ファイルへの上書きは禁止**です。
別のルールへ変更した場合、または一度実行した場合、再度試運転が必要です。

保存先が既に存在する場合は安全停止し、元ファイルを残します。
途中でファイルが書き換えられた場合や出力先に競合が起きた場合も
データ喪失回避を優先します。

「設定JSONを新規保存」は既存ファイルを上書きしません。画面内での
常時監視・複数ルールの管理・ファイルバックアップの復元検証は**非対応**です。
既存 `backup_verifier_gui.py` は独立したバックアップ検証画面であり、
このファイル整理GUIから実行・復元されません。

## What this app does
Copy or move local files from a named input subfolder into a different
output subfolder based on a filename pattern. Start `python folder_desktop_app.py`,
select an existing main directory, confirm the rule, use **Dry Run**, then
explicitly authorize a one-time copy or move. The default is **copy**, and
overwriting existing files is forbidden.

A successful preview is valid only for the unchanged rule. Any live execution
consumes that preview. Dry Run does not change files or create the job database.
Saving a JSON configuration never overwrites an existing file.

This is a guided **one-shot** interface, not a continuous monitoring service
or backup restoration app. The separate backup verifier retains its own GUI.

## Tests for code operator
```powershell
python -m compileall -q folder_automation.py folder_desktop_flow.py folder_desktop_app.py
python -m unittest discover -s tests -p "test_folder_gui_flow.py" -v
python -m unittest discover -s tests -p "test_folder_automation_safety.py" -v
python folder_desktop_app.py
```

## Acceptance still required
- [ ] CI must run actual job steps and return green (currently blocked with
      **zero steps and unavailable job logs**, suspected repository-level runner
      or plan/policy issue; not proven to be a code failure).
- [ ] Real Windows 10/11 GUI at 100%, 125%, 150%; keyboard navigation,
      text clipping, error dialogs and accessible names
- [ ] Test no-overwrite collisions, source changing during read, USB,
      OneDrive/network shares, large files, Windows security permissions
- [ ] Verify a cancelled prompt never writes, and double-clicking Run
      never triggers two concurrent filesystem operations
- [ ] Decide whether the backup verifier is a separate paid product rather
      than advertising it as integrated with this app
- [ ] Complete third-party notices, approved assets, license, MSIX identity,
      signing/Store validation, formal code-operator release QA

Do not edit existing main or publish from this prototype branch.

## Additional non-device QA and product understanding (2026-10-18)

The first screen explains that the product **copies or moves files by a
filename rule** and shows `Main folder → Input/Output folders → Dry Run →
Confirm once`. The form does not silently overwrite customer files.
A successful preview now snapshots input file names, inode/file IDs,
sizes and modification timestamps. The worker requires the same set just
before live processing; a change refuses live action and demands another
preview. This is best-effort detection, not atomic locking against external
filesystem writers. Race-free destination creation remains the engine's duty.

Tests added in `tests/test_folder_gui_flow.py`: files added after preview,
file content/size changed, input file deleted, linked input folder refused,
live worker stops before writes on mismatched inputs. Previous coverage
remains for no-overwrite rules, approval, and JSON preservation.

Owner-selected Store identity is in
`store/PARTNER_CENTER_IDENTITY_HANDOFF_20261018.md`.
**Desktop entrypoint is `folder_desktop_app.py`, not the independent
`backup_verifier_gui.py`.** Build operator must choose the product scope
before packaging and must verify real GUI size/DPI and long paths on Windows.
