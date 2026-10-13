"""Optional Windows UI for backup_restore_verifier.

Separate from the existing folder automation rule engine, so previously
configured copy/move rules remain unchanged.
"""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from backup_restore_verifier import snapshot, verify


class BackupVerifierGUI(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("バックアップ整合性・復元テスト（試作版）")
        self.geometry("850x590")
        self.minsize(740, 500)
        self.source = tk.StringVar()
        self.backup = tk.StringVar()
        self.manifest = tk.StringVar()
        self.reports = tk.StringVar(value=str(Path.home() / "Documents"))
        self.maxmb = tk.IntVar(value=100)
        self.status = tk.StringVar(value="最初にバックアップ前の元データから基準manifestを作成します。")
        frame = ttk.Frame(self, padding=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="バックアップ復元検証", font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))
        self._row(frame, 1, "元データ（manifest作成）", self.source, "directory")
        self._row(frame, 2, "バックアップフォルダ", self.backup, "directory")
        self._row(frame, 3, "信頼できるmanifest", self.manifest, "file")
        self._row(frame, 4, "監査レポート出力先", self.reports, "directory")
        ttk.Label(frame, text="一時復元テスト上限（MB）").grid(row=5, column=0, sticky="w", pady=6)
        tk.Spinbox(frame, from_=0, to=5000, textvariable=self.maxmb, width=12).grid(
            row=5, column=1, sticky="w", pady=6)
        ttk.Label(frame, text="注意: 基準manifestは元データが正常なうちに作成し、バックアップとは別の安全な場所で保管します。",
                  wraplength=790).grid(row=6, column=0, columnspan=3, sticky="w", pady=(14, 8))
        row = ttk.Frame(frame)
        row.grid(row=7, column=0, columnspan=3, sticky="w", pady=10)
        ttk.Button(row, text="① 元データのmanifestを新規作成", command=self.make_manifest).pack(side="left", padx=(0, 12))
        ttk.Button(row, text="② バックアップを検証", command=self.run_verify).pack(side="left")
        ttk.Separator(frame).grid(row=8, column=0, columnspan=3, sticky="ew", pady=12)
        ttk.Label(frame, textvariable=self.status, wraplength=790, justify="left").grid(
            row=9, column=0, columnspan=3, sticky="w")
        ttk.Label(frame,
                  text="これはバイト単位の照合・一時復元コピーの確認です。アプリやデータベース全体の復旧保証ではありません。",
                  wraplength=790).grid(row=10, column=0, columnspan=3, sticky="w", pady=10)

    def _row(self, parent, row, label, variable, kind) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=6)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=6)
        def choose() -> None:
            if kind == "directory":
                value = filedialog.askdirectory()
            elif kind == "file":
                value = filedialog.askopenfilename(filetypes=[("JSON manifest", "*.json")])
            else:
                value = ""
            if value:
                variable.set(value)
        ttk.Button(parent, text="参照", command=choose).grid(row=row, column=2, padx=8)

    def make_manifest(self) -> None:
        if not self.source.get():
            messagebox.showwarning("入力不足", "元データを指定してください。")
            return
        target = filedialog.asksaveasfilename(
            title="manifest保存先（バックアップ元・保存先とは別の場所）",
            defaultextension=".json", filetypes=[("JSON manifest", "*.json")])
        if not target:
            return
        try:
            result = snapshot(self.source.get(), target)
            self.manifest.set(str(result))
            self.status.set(f"manifest作成: {result}\nこのファイルを別の安全な場所へ保存してください。")
            messagebox.showinfo("作成完了", f"基準manifestを作成しました:\n{result}")
        except Exception as exc:
            self.status.set(f"失敗: {exc}")
            messagebox.showerror("manifest作成に失敗", str(exc))

    def run_verify(self) -> None:
        if not self.backup.get() or not self.manifest.get():
            messagebox.showwarning("入力不足", "バックアップフォルダと基準manifestを選んでください。")
            return
        try:
            maxmb = self.maxmb.get()
            if not 0 <= maxmb <= 5000:
                raise ValueError("一時復元の上限は0～5000MBにしてください")
            if not messagebox.askyesno(
                "確認", "バックアップのSHA-256を検査し、指定容量まで一時フォルダへ復元コピーします。"
                        "\n元データ・バックアップは変更しません。続行しますか？"):
                return
            output = verify(self.backup.get(), self.manifest.get(), self.reports.get(),
                            restore_test_max_bytes=maxmb * 1000000)
            summary = json.loads((output / "verification.json").read_text(encoding="utf-8"))
            self.status.set(
                f"{summary['status']}: 検証済み {summary['summary']['verified']} / "
                f"検出 {summary['summary']['findings']} / 復元検査 {summary['summary']['sample_restored']}\n"
                f"レポート: {output}")
            messagebox.showinfo("検証結果", self.status.get())
        except Exception as exc:
            self.status.set(f"失敗: {exc}")
            messagebox.showerror("検証エラー", str(exc))



def _validation_smoke() -> None:
    """Noninteractive Tk widget construction smoke; not user-click testing."""
    import json
    import sys
    from pathlib import Path
    if len(sys.argv) != 4 or sys.argv[1] != "--smoke-test" or sys.argv[2] != "--smoke-output":
        raise SystemExit(2)
    app = BackupVerifierGUI()
    try:
        app.update_idletasks()
        app.update()
        assert app.winfo_exists() and app.title() and len(app.winfo_children()) > 0
        result = {"status": "GUI_PROCESS_SMOKE_OK", "title": app.title(),
                  "scope": "Tk initialization and event pump only; no simulated clicks"}
        with Path(sys.argv[3]).open("x", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False)
    finally:
        app.destroy()


if __name__ == "__main__":
    import sys
    if "--smoke-test" in sys.argv:
        _validation_smoke()
    else:
        BackupVerifierGUI().mainloop()
