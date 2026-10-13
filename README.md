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


## 拡張MVP: バックアップ整合性・復元プローブ（2026-10）

既存の `folder_automation.py` の実行ルールは変更せず、独立した検証アダプターを追加しました。

1. **元の信頼できるデータ**からmanifestを作る:
   `python backup_restore_verifier.py snapshot C:\\Data C:\\Manifest\\baseline.json`
2. 自分のバックアップツール等で `C:\\Data` を `D:\\Backup` にコピーする。
3. バックアップを検査し、一時フォルダで復元コピーを少量テストする:
   `python backup_restore_verifier.py verify D:\\Backup C:\\Manifest\\baseline.json C:\\Reports --restore-test-max-mb 100`

- 追加ライブラリ不要（Python標準ライブラリ）
- ファイルサイズ、SHA-256、欠落ファイル、余分なファイルを照合
- シンボリックリンク／Windowsジャンクション、および危険なmanifestパスは拒否
- 原本やバックアップを変更せず、テンポラリへ限定量を復元してSHA照合
- 出力は `verification.json`、結果は `REVIEW` / `HASH_CHECKED_ONLY` 等で表示
- テスト: `python -m unittest discover -s tests -p "test_backup_restore_verifier.py"`
- **必須前提**: baseline manifestは**バックアップ前の信頼できる元データ**から別の安全な場所へ保存する。破損後のデータから生成したmanifestでは復旧可能性を証明できません。
- **制限**: アプリやDBの整合性、NTFS ACL/ADS、復元先でのアプリ起動は未検査。manfest自体の真正性を保証する電子署名も未実装。
- Windows実機・大容量検査・リンク・権限・大量ファイル検証が販売前に必要です。

### Windows画面
- GUI: `python backup_verifier_gui.py`
- 既存のフォルダ監視GUIとは独立して実行されます。
- 検証前に基準manifestを作る操作と、バックアップを照合する操作を分離しています。


### Windows検証ビルド（未署名）

`powershell -ExecutionPolicy Bypass -File .\\build-windows-validation.ps1`

バックアップ整合性テストを通してから検証用EXEを生成します。生成物は `dist-validation/` 下、署名・販売承認は行いません。
GitHub Actionsは `.github/workflows/windows-validation.yml` から**手動実行**します。
