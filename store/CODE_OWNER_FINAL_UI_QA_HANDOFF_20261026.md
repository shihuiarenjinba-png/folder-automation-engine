# Folder Automation Engine 通常版 — 最終Windows QA・コード担当引継ぎ（2026-10-26）

> **現判定: FINAL_QA_PENDING / STORE_UPLOAD_HOLD / STORE_SUBMISSION_HOLD。** この資料は、EXEの新規実行・MSIXインストール・Storeへの実アップロード・認定提出・公開を許可するものではありません。

## 0. 製品と厳守事項

- 対象: **Folder Automation Engine 通常版**。一般向け「-2」系列は一切変更しない。
- Repository: https://github.com/shihuiarenjinba-png/folder-automation-engine
- UI作業ブランチ: `codex/folder-standard-consumer-ui-20261026` / Draft PR #10: https://github.com/shihuiarenjinba-png/folder-automation-engine/pull/10
- UI PRのbase: `codex/folder-standard-store-qa-20261024` / Draft PR #9: https://github.com/shihuiarenjinba-png/folder-automation-engine/pull/9
- PR #9のQA基点: `1a98a6e725f21c248dfd230e03bf4811fbf2dcf2`。UI修正開始時点のHEAD: `8af33170a13595e9efd9c2410d012cf097ce841a`。
- 最新UIコピー修正コミット: `ded652375bb44426e6e282770188666cc5214b00`（以後この引継ぎファイルを加えたコミットが生じるため、**最終候補の正確なHEADはGitHubで再取得すること**）。
- 書込みはUI作業ブランチ上のみ。main/release直接変更・PRマージ不可。ローカルに不明な変更がある場合は確認して止めること。-2への反映はしない。
- **未署名ダウンロードEXEの実行はコード担当の従来の「実行直前承認」が必須。** 旧EXEの承認を新しいSHA256へ流用しない。
- Windows Smart App Control / WDAC / Code Integrity / Defender / SmartScreenの変更・バイパス禁止。証明書ストアの無断変更、自己署名証明書への無断信頼付与は禁止。
- Storeアップロード、提出、公開、価格、対象国・地域、Google等の外部接続はそれぞれ別途オーナー承認までHOLD。
- ZIPの一括ダウンロード・配布は不要。GitHub ActionsのEXE/MSIX個別成果物を証拠付きで扱う。

## 1. 今回までに実装した「購入者が使えるUI」

最新 `folder_desktop_app.py` に反映済みの点:

1. 親フォルダー・整理元・整理先を日本語/英語で明瞭に表示。整理元/先は選択ダイアログで**既存の親フォルダー直下の通常サブフォルダー**だけ選べる（パス逸脱・symlink/junctionでの迂回は禁止）。
2. フォルダーとファイル形式（PDF/CSV/TXT/JPG/PNG等の候補、手入力も可）を指定 → **Dry Run** → 対象一覧を確認 → 明示承認してコピー/移動、という基本導線。
3. 試運転・実行ボタンを視覚的に区別。実行ボタンは成功したDry Runまではdisabled。親・元・先・パターン・copy/move変更時に旧プレビュー承認を無効化。
4. コピー/移動のUI表記をJP/ENでローカライズ。内部コンフィグの`copy`/`move`は互換性維持。
5. プレビュー・件数・ログ・監視状態を、スクロールする設定領域の外に置いて**常時見える結果パネル**にした。
6. 設定の保存/読込をメイン操作エリアに配置。詳細ルール・任意監視を折りたたみ、利用者が必要になった時に開く。監視中/停止は画面上で確認。
7. 元のフェイルクローズ・上書き防止・設定JSON検証・日本語/英語言語保存・safe-close worker/watcher終了処理を維持。
8. **画面では実際に利用できる操作だけを説明**する。旧UIの「バックアップ復元検証は別画面です」など、購入者が操作できない機能への言及は削除し、機能の積極的な説明へ置換。必要な安全上の警告・選択制限は隠さない。
9. 独立したバックアップ復元GUIはこの商品UIへ組み込まれていない。これは**内部QA/Storeの機能整合性メモ**であり、アプリの通常画面に記載しない。

## 2. 既に完了した技術QA（UIコピー修正前の実績）

- 修正前のUIコード `8af33170a13595e9efd9c2410d012cf097ce841a` は Windows/Ubuntu GUI・安全性回帰テスト PASS、Windows `67 tests OK`。
- Windows build / unsigned Store-MSIX / GUI smoke: https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/40249983779 （PASS）。
- GUI・安全性検証: https://github.com/shihuiarenjinba-png/folder-automation-engine/actions/runs/40249983790 （Windows/Ubuntu PASS）。
- 旧（UIコピ－修正前）成果物ID: Windows `12619794594` / MSIX `12620108762`。
- 旧EXE SHA256: `3dc04eb82c65796be9243371b16e9044a1b241f3b03f8cb1b3592df00eb9e296`。
- 旧未署名MSIX SHA256: `7fb060bd49df7b2759c3ac12672925461284dbd8e33d720341d585396907f34c`。
- 旧GUI実画面のCI captureは**人の操作試験やStore画像とは別扱い**。
- **上記旧SHA256は今回の最終コミットの販売バイナリではない。** 新しいEXEとMSIX、run ID、hashesの再取得必須。

### 以前のローカル実機ブロック

- Smart App Control / Code Integrity Events 3077・3033; Policy ID `{0283ac0f-fff1-49ae-ada1-8a933130cad6}`。
- 未署名EXEが `ShellExecuteW returned 5` で拒否。Windowsセキュリティを変えず安全停止。入力ファイル3件SHA256不変・出力0件。
- 現在のUIコードは**別の未署名EXE**。元PCでの実行が保証されたわけではない。認可された独立Windows 11実機または適切に構成したWindowsテスト環境が必要。

## 3. コード担当が今から実施する「最終テスト」

必ず**同じ最終HEAD・同じ成果物SHA256**で一連のQAを行う。ソース修正した場合はビルドと該当テストをやり直す。PASS、FAIL、BLOCKED、NOT_TESTED、SKIPを区別する。

### Step A — GitHub exact-head / package provenance

1. branch / HEAD / working tree / unexplained changes / PR #10 HEAD確認。PR #9と-2、main/releaseは変更しない。
2. Windows/Ubuntu自動テスト（結果・件数・skips）、Windows build、GUI smoke、EXE `--self-test`、MSIX pack/unpack・manifest・sha256台帳・EXE一致を再確認。
3. GUI画像は`CI_GUI_ONLY`として区分。マーケティング画像には使わない。
4. 最新MSIXの署名は`NotSigned`のままでよいが、`SIGNED`・`STORE_APPROVED`を誤表示しない。

### Step B — Windows 11 GUI/UX（実行時の新規承認必須）

原本ファイルではなく隔離された`QA_Folder_Test`と合成データだけで実施。

- 起動、初回導線、1024×768 / 1280×720および本来のWindows画面DPI 100/125/150%。
- 日本語/English→終了→再起動の言語保存。設定JSON保存/読み込み、旧Dry Run無効化。
- 親フォルダーを選び、整理元/先サブフォルダー選択。外部・入れ子・シンボリックリンク・ジャンクションによる不正選択を拒否。正当なパスが使えること。
- `*.csv`でpreview→件数・対象/宛先表示→キャンセル→0 writes。実行承認→入力出力SHA256一致。copyは元保持、moveは内容一致と安全な移動、既存宛先への上書き不可。
- 試運転成功後のファイル追加/変更/削除、条件変更、二度押し、再実行、長い名前・Unicode・0-byte・競合・複数ルール。エラーダイアログ/結果欄確認。
- 詳細設定の開閉、監視の明示承認/ON/OFF表示/停止、データ書き込み途中の回避、終了時に処理が安全に終わること。
- キーボードフォーカス・表示切れ・スケーリングによるボタン欠け。実UIスクリーンショット、テストケース別の証拠。
- symlink/junction関連の過去3件SKIPを安全な試験機で検証。不可ならNOT_TESTEDを残し、Store GOの安全上の影響を明示。

### Step C — MSIX / 商用

- 最新Partner Center製品情報とPackage Identity/Publisher/PFN/Version historyの照合。**資料値だけで確定しない**。
- 既存の候補: Store ID `9P99MJX1R4V6`, Identity `OkinawaDesktopTools.FolderAutomationEngine`, Publisher `CN=46263F21-A700-41DB-8C9B-114C22FB82FC`, technical Version `1.0.0.0` — すべて現在値の照合待ち。
- Store向けMSIXは正式アイコン/素材を確認して作成し、全同梱バイナリの第三者ライセンス/NOTICE・SBOM・署名/バージョン・プライバシー文書・サポート情報の整合を点検。
- MSIX install/Startメニュー起動/update/uninstall/LocalState永続化、WACKは別途承認済み/適法な署名検証環境で行う。Store配布版は認定後に署名されるため、入手前の検証と認定後のStore配布端末QAを混同しない。
- Store日本語/英語掲載文は**確認済み機能のみ記載**。未搭載機能や「何ができないか」の宣伝は書かない。必要な制約・権利・対応範囲・安全情報は申請資料/ヘルプ内で正確に説明。
- 実際のStore画像を使用。少なくともデスクトップ1366×768以上の本物のGUIを取得し、必要枚数/比率/容量は現在の提出画面・Microsoft公式要件を再確認。
- 価格・国・公開・提出操作はオーナー明示承認まで行わない。

## 4. オーナーの自動アップロードスクリプトへ渡す基準

**この商品をスクリプトのテスターとして使うのは、製品が`STORE_UPLOAD_READY`になってから。**

- `BUILD_READY`: exact HEAD/テスト/未署名MSIX/検証台帳PASS（CI画像はQA証拠のみ）。
- `WINDOWS_QA_READY`: 実機でGUI操作・コピー/移動・安全性・DPI/言語/設定の承認範囲内テストを完了。重大FAIL 0。
- `STORE_UPLOAD_READY`: Windows QA、Identityの現行照合、ライセンス・正式アイコン・掲載画像・プライバシー/価格/提出情報、必要なMSIX/WACK等がそろい、オーナーによる**アップロード行為への別承認を取得**。
- `STORE_CERTIFICATION_SUBMITTED`: アップロード後、別途オーナーが認定提出を承認し、実際に提出できたときだけ。
- `STORE_RELEASE_GO`: 認定成功・実配布の確認およびオーナー公開許可を得た後だけ。

### スクリプト実装者へのインターフェース要件

- 型: `app`。既存Store製品の検索・確認を優先し、新規製品を勝手に作らない。
- テスト順: `VALIDATE_ONLY`（JSON/MSIXの静的検証・UI項目の可用性確認）→ `DRY_RUN`（実際の送信、編集、確定クリック無し）→ 承認済み実行。**テスト成功≠Store承認**。
- 入力は最終MSIXの絶対パス/SHA256/commit/Package Identity/Version、日英掲載文、正式画像、価格/市場/年齢/プライバシー、選択式回答と証拠。未確定は`null`/HOLD。例示値を自動入力しない。
- 選択式質問の選択肢は原文どおり使い、画面に存在しない選択肢を創作しない。AIによる提案を直接確定回答へ転記しない。
- 各操作は成功/失敗理由とUI要素の証拠を残す。失敗した項目だけをHOLDにし、他の承認済み整備作業は続行。ただしパッケージ誤指定・Identity不一致・権限異常・認定提出の重要条件はfail-closed。
- **申請画面の送信・審査申請・Publishは、別々の明示承認ゲート**。認定後の自動公開を避ける公開保留設定を確認する。
- 申請に用いるデータは機密情報・認証トークン等をログへ記録しない。

**現在の状態は`BUILD_READY`まで。自動アップロードの実送信テスターとしては未適格。**

## 5. 報告の必須項目

最後に、`Repository URL/source HEAD/work branch/work HEAD/commit diff/PR/Windows・Ubuntu runs/jobs/steps/artifact IDs/ZIP SHA256/EXE SHA256/MSIX SHA256/Store manifest`を記載。

各テストの`PASS/FAIL/BLOCKED/SKIP/NOT_TESTED`と、データSHA256/テストPC情報/画像を保存。特に意図しないファイル移動、上書き、同期フォルダー損傷、署名警告を曖昧にしない。

`UI_QUALITY`、`FUNCTIONAL_SAFETY`、`PACKAGE_VALIDATED`、`PARTNER_CENTER_VERIFIED`、`STORE_UPLOAD_APPROVED`を独立判定し、最後に`GO/HOLD`と理由を報告。

**コード担当は、承認済み範囲の最終テスト・必要な最小修正・最新EXE/MSIX再生成・証拠整備まで完遂し、完成結果をチャットに返してください。Storeの実操作は別途承認があるまで実施しないでください。**
