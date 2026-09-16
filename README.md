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
python -m unittest discover -s tests -v
```

## 安全設計

- すべての対象パスは `root_dir` 配下に限定
- 任意コマンド実行はMVPに含めない
- 上書きは既定で禁止
- 秘密情報は扱わない
- AI判断なし
- SQLite接続にbusy timeoutを設定

### 出力先が既に存在する場合

`overwrite=false` で同名ファイルが出力先にある場合は `BLOCKED` として停止します。

- 元ファイルは残す
- processed DBへ記録しない
- 同じファイルを後続ルールへ勝手に流さない
- 衝突を解消した後の次回scanで再試行可能

これにより「何も処理していないのに処理済みになる」状態を防ぎます。

将来、既存のPDF/Excel Privacy系ツールは、専用Adapterとして明示的に追加します。
