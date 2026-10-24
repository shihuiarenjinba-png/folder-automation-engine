# Microsoft Store スクリーンショット・実入出力証拠収集指示 — 2026-10-19

## 目的と完了条件

この文書は Microsoft Store への提出素材収集を担当する Windows コード担当向けです。
商品コードの機能拡張や全面改修ではなく、**Windowsで動く完成候補を実際に起動し、ユーザーに商品の用途が伝わるPNGと実入出力を取得**します。

- 画像は実際に起動したアプリのキャプチャであること。見本画像、AI生成画像、HTMLモック、合成画像を「実行証拠」や「Storeスクリーンショット」と偽って提出しない。
- 日本語商品ページに日本語GUI、英語商品ページに英語GUI。**日本語4～5枚・英語4～5枚**を目標にする。
- Desktop向けPNGは **1366x768ピクセル以上、1ファイル50MB以内、最大10枚**。最低1枚必要。元画像を拡大して数値だけ合わせない。
- 主役は**アプリの機能を示す実GUI**。ExcelやExplorerだけを写したファイル比較は「入出力実証」の別素材として保存し、Store商品ページではアプリ自身の画面を中心にする。
- サンプルの入力ファイルと**実際に実行して生成された結果ファイル**を別フォルダーで保存し、入出力の差異をSHA256/内容で確認。
- 画像へ別ロゴ・販促キャッチコピーを後付けしない。設定前の秘密値、認証済みアカウント、トークン、個人・顧客情報、プライベートURLなどを表示させない。
- Storeへ画像とパッケージをアップロードする作業はオーナー承認のもとで進める。画像収集だけで正式提出・公開しない。

Microsoft公式:
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/screenshots-and-images
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/upload-app-packages
- https://learn.microsoft.com/en-us/windows/apps/publish/publish-your-app/msix/app-package-requirements

## Windows PC内の出力先

`%USERPROFILE%\Desktop\portfolio-audit\STORE_UPLOAD_ASSETS_20261019\<Product>\`

この下に下記を用意する。

- `screenshots/ja-JP/01_home.png ...`
- `screenshots/en-US/01_home.png ...`
- `actual_inputs/` — 本当に使用したデモ入力のみ（公開可能・個人情報なし）
- `actual_outputs/` — 実行してアプリが生成したファイル
- `evidence/` — リダクト済み実行ログ、比較ハッシュ、GUI・OS環境、commit SHA、EXE/MSIXハッシュ、スクリーンショット寸法記録
- `README_UPLOAD.txt` — 各言語の画像説明と、Storeへ添付するファイル/まだ提出しないファイルの明確な区別

PNG確認：幅、高さ、PNG形式、50MB上限、画像の重複/内容の曖昧さ、言語一致、ロゴ・権利を確認。画像名とSHA256をmanifestへ記録。

**現在のGitHub ActionsにあるWorkflow Automation HubのGUI画像は964x678で、そのままではDesktop Store提出不可。** 実UI撮影の参考のみに使う。ほかの3製品は確認したCI実行に提出サイズのPNG成果物がないため実機撮影が必要。

## マイクロソフト認定との関係

StoreはMSIX提出後に自動セキュリティ/技術/コンテンツ審査を行い、公開時にStore署名を行う。Store配布のMSIXのために別途有料のCA署名証明書を購入する必要はない。ただしStore認定は個別顧客の入力・出力の動作を完全に保証するものではない。ユーザー向け宣伝画面は実機動作を正確に示すこと。

**StoreのPackagesにはMSIX、Store listingsにはPNGをそれぞれ登録する。** テスト用サンプルCSV/JSONと実出力は主に説明/検証用であり、必要時だけ認定Notes等へ安全な方法で提示する。Secretを含むログはアップロードしない。

## 最終報告

- 実行日時、Windows版、画面解像度/DPI、Git full SHA、使用EXE/MSIXのSHA256
- 製品ID/正式Identity、JP/ENスクリーンショット各枚数とパス、PNGサイズチェックのPASS/FAIL
- 実入力と実出力の絶対パス、差分の説明、元ファイル保全、実際の操作成功/未検証の区別
- 個人情報/認証情報/著作権チェック、採用画像と不採用画像
- 最終的に店頭へアップロードしてよい状態か、残りの必要事項を製品ごとに回答

何も撮影していない場合は「準備だけ完了」と記録する。コード担当のPCで撮影する工程まで実施して初めて「取得完了」とする。

## FolderAutomationEngine

- Store ID: 9P99MJX1R4V6
- 最新Draft PR: https://github.com/shihuiarenjinba-png/folder-automation-engine/pull/6
- branch: `codex/store-draft-validation-20261019`

## Folder Automation Engine の撮影

入力には機密を含まないCSVとテキストを用意する（例 `invoice_2026_1019.csv`, `notes_2026_1019.txt`）。`*.csv`を `processed-csv` へcopy、`*.txt`を `processed-text` へmove。出力先ディレクトリを必要に応じて作成する。

操作：①ルート/元/先フォルダー設定→②複数ルールの追加・優先順位→③Dry Runの対象一覧→④実行完了・監査/ログ→⑤任意の常時監視画面。実出力はExplorerで別の証拠写真も保存（元ファイルの存否と宛先一致）。

Store画像: `01_home.png`, `02_rules.png`, `03_preview.png`, `04_result.png`, `05_watch.png`。実入力・実コピー/移動後のファイルを `actual_inputs` と `actual_outputs` に保存。

初期サンプル内容に個人氏名や住所を入れない。既存ファイル上書きの発生しない場所で実演。複数ルール中の最初の一致のみが実行されることを説明。

画像説明例:
- JA「フォルダーとコピー・移動先を指定」
- JA「複数のルールを並べ替え可能」
- JA「実行前に対象ファイルを確認」
- EN "Route files using ordered copy and move rules" / "Preview changes before execution".
