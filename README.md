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


## Windows QA evidence and manual acceptance (2026-10-13)

See [Windows QA Runbook](docs/WINDOWS_QA_RUNBOOK.md) for unsigned build verification, manual checks and local evidence. **This is not a sales release.**

## 初回画面から分かる商品内容 / Guided GUI (draft 2026-10-18)

`python folder_desktop_app.py` で、初心者向けのファイル整理画面を開けます。
画面冒頭に「この商品は条件に合ったローカルファイルをコピー・移動する」と明示し、
**基準フォルダーを選択 → 入力先・出力先・条件を指定 → Dry Run → 確認して1回実行**
という順序で操作できます。初期設定は `copy`、**既存ファイルは上書き禁止**です。

試運転時の入力ファイル一覧・ファイルサイズ・更新時刻のスナップショットを
本実行直前に再確認します。途中で増減・変更があれば、予期しないファイルの
処理を避けるため、再度Dry Runが必要です。厳密な同時書き込みトランザクション
ではないため、エンジン側の排他的な保存処理も併用します。

新しく保存する設定JSONも上書きせず、既存の顧客データを変更しません。

**商品上の区別:** この画面はコピー・移動の単発実行です。
常時監視と独立したバックアップ復元検証GUIは、同じ画面から操作できる
機能として宣伝しません。実機テストと販売パッケージ制作はコード担当へ
引き継ぐ項目です。GitHub Actionsの最新実行がPASSしない限り、
商用完成とは判定しません。詳細は `docs/FOLDER_GUIDED_GUI_DRAFT.md`。
