# Folder Automation Engine

指定フォルダを監視し、ファイル名・拡張子のルールに一致したファイルへ**決められた処理だけ**実行するローカル自動化エンジンです。AI判断や任意コマンド実行は行いません。

## Windows Desktop / デスクトップ

通常利用ではターミナルを開かず、`desktop_app.py` / 将来のWindows EXEから操作できます。

画面で確認できるもの:
- 設定JSON
- `root_dir` / 入力フォルダ
- 監視間隔
- ルール数
- processed State DB
- Dry Runの結果
- 1回実行 / 監視開始 / 停止
- 実行ログ

```powershell
python desktop_app.py
# または
run_desktop.bat
```

Windows EXEビルド用に `build_windows.ps1` も追加しています。

## Core MVP

- `*.pdf` / `*.csv` 等のglob条件
- copy / move
- Dry Run
- SQLiteで処理済み状態を記録
- 一定間隔の監視
- ローカルのみで動作

## CLI / 開発者向け

```powershell
python folder_automation.py config.example.json --once --dry-run
python folder_automation.py config.example.json --once
python folder_automation.py config.example.json
python -m unittest discover -s tests -v
```

## 安全設計

- すべての対象パスは `root_dir` 配下に限定
- 任意コマンド実行はMVPに含めない
- 上書きは既定で禁止
- 秘密情報は扱わない
- AI判断なし
- SQLite接続にbusy timeoutを設定
- GUIも既存Coreを直接使用し、別実装を持たない

### 出力先が既に存在する場合

`overwrite=false` で同名ファイルが出力先にある場合は `BLOCKED` として停止します。

- 元ファイルは残す
- processed DBへ記録しない
- 同じファイルを後続ルールへ勝手に流さない
- 衝突を解消した後の次回scanで再試行可能

これにより「何も処理していないのに処理済みになる」状態を防ぎます。

将来、既存のPDF/Excel Privacy系ツールは専用Adapterとして明示的に追加します。
