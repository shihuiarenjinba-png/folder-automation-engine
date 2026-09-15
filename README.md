# Folder Automation Engine

指定フォルダを監視し、ファイル名・拡張子のルールに一致したファイルを**決められた処理だけ**実行するローカル自動化エンジンです。

## MVP

- `*.pdf` / `*.csv` 等のglob条件
- copy / move
- Dry Run
- SQLiteで処理済み状態を記録
- 一定間隔の監視
- ローカルのみで動作

## 実行

```powershell
python folder_automation.py config.example.json --once --dry-run
python folder_automation.py config.example.json --once
python folder_automation.py config.example.json
```

## 安全設計

- すべての対象パスは `root_dir` 配下に限定
- 任意コマンド実行はMVPに含めない
- 上書きは既定で禁止
- 秘密情報は扱わない
- AI判断なし

将来、既存のPDF/Excel Privacy系ツールは、専用Adapterとして明示的に追加します。
