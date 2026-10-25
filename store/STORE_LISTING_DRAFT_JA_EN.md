# Microsoft Store listing copy — Folder Automation Engine

**DRAFT / Commercial HOLD.** The existing Partner Center product has Store ID `9P99MJX1R4V6`. Do not create a duplicate product or upload an unapproved package.

## 日本語

**製品名（記録上の予約名）:** Folder Automation Engine

**短い説明:**
条件に合うローカルファイルを、試運転で確認してから安全にコピー・移動するWindowsアプリです。

**説明:**
Folder Automation Engineは、選択したフォルダー内のファイルを、ファイル名パターン（例：`*.pdf`）に従って別のフォルダーへコピーまたは移動するオフラインツールです。

メインフォルダー、入力先、保存先、条件を設定し、書き込みを行わない「試運転」で対象を確認してから、明示的な確認操作で1回実行します。最大10件の規則を設定でき、設定JSONを任意の場所へ新規保存して、後から読み込めます。読み込み後や対象ファイルの変更後は、再度試運転が必要です。

既存の保存先ファイルは上書きしません。任意の監視機能は、承認済みの規則と安定した入力だけを処理し、停止操作またはアプリ終了で停止します。アプリは外部サービスへデータを送信せず、広告・分析・アカウントログインも使用しません。

**注意事項:**
処理前に必ず試運転結果と保存先を確認してください。クラウド同期フォルダー、ネットワークドライブ、特殊なアクセス権、シンボリックリンク／ジャンクション、非常に長いパスは、利用環境ごとの確認が必要です。バックアップ復元検証は別製品・別画面であり、この製品の機能ではありません。

**機能候補（各200文字以内）:**

- 書き込みを行わない試運転
- 明示確認後の1回コピー／移動
- 最大10件のファイル名規則
- 既存ファイルを上書きしない安全設計
- 設定JSONの保存と安全な再読み込み
- 任意のフォルダー監視と停止
- 日本語／英語UIとローカル言語設定保存
- 外部通信・広告・分析なし

## English

**Short description:**
Preview, then safely copy or move local files by filename rules—fully offline on Windows.

**Description:**
Folder Automation Engine is an offline Windows tool for copying or moving files from a selected folder according to deterministic filename patterns such as `*.pdf`.

Choose a root folder, input and destination folders, and rules. Review a no-write Dry Run, then explicitly confirm a one-time operation. Up to 10 rules are supported. You can save a new configuration JSON file in a location you choose and safely load it later. Loading a configuration or changing the input files invalidates the previous preview and requires a new Dry Run.

Existing destination files are never overwritten. Optional watching uses the approved rules and processes stable input only; it stops when requested or when the app closes. The app has no external data transmission, ads, analytics or account sign-in.

**Important:**
Always review the Dry Run and destination before processing. Cloud-synchronized folders, network drives, unusual permissions, symbolic links/junctions and very long paths require environment-specific validation. Backup restore verification is a separate product and is not included in this app.

**Feature candidates (200 characters maximum each):**

- No-write Dry Run before processing
- Explicitly confirmed one-time copy or move
- Up to 10 filename rules
- No overwrite of existing destination files
- Save and safely reload configuration JSON
- Optional folder watching with a clear stop action
- Japanese and English UI with local language preference
- No external network communication, ads or analytics

## Store screenshots still required

For each listing language, collect genuine installed-candidate screenshots at 1366×768 or larger:

1. First-run three-step workflow
2. Completed rules and selected disposable test folder
3. No-write Dry Run results
4. Confirmed copy/move result with non-sensitive synthetic filenames
5. Optional: safe validation error or watch status

CI runner captures and Explorer comparison images are QA evidence only, not Store listing images. Do not show user names, credentials, private paths or customer data.

## Partner Center HOLD items

- Re-copy title, Identity Name, Publisher, PFN and version history from the live product.
- Approve final production icon/logo and verify artwork rights.
- Approve the Japanese/English copy after human Windows QA.
- Decide price, Japan/United States availability, age rating, privacy policy, support contact and legal terms.
- Upload only the final Store package after separate owner approval.
- Enable publishing hold; certification must not automatically publish the product.
