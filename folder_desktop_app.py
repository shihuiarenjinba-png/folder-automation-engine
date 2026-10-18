"""Guided, local-only Folder Automation Engine desktop UI (draft).

Start: python folder_desktop_app.py
The independent backup verifier GUI remains a separate product surface.
"""
from __future__ import annotations

import contextlib
import io
import json
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from folder_automation import ConfigError, Engine
from folder_desktop_flow import build_config, revision, snapshot_inputs, format_activity


class FolderDesktop:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Folder Automation Engine")
        self.root.geometry("900x690")
        self.root.minsize(720, 570)
        self.lang = tk.StringVar(value="日本語")
        self.displayed_language = "日本語"
        self.root_path = tk.StringVar()
        self.input_folder = tk.StringVar(value="inbox")
        self.output_folder = tk.StringVar(value="processed")
        self.pattern = tk.StringVar(value="*.pdf")
        self.action = tk.StringVar(value="copy")
        self.status = tk.StringVar(value="")
        self.preview_revision: str | None = None
        self.preview_input_snapshot: tuple | None = None
        self.busy = False
        self.messages: queue.Queue[tuple[str, bool, str, str, tuple | None]] = queue.Queue()
        self.build()
        self.root.after(100, self.poll)

    def t(self, ja: str, en: str) -> str:
        return en if self.lang.get() == "English" else ja

    def build(self) -> None:
        self.displayed_language = self.lang.get()
        for child in self.root.winfo_children():
            child.destroy()
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)
        heading = ttk.Frame(frame)
        heading.pack(fill="x")
        ttk.Label(
            heading, text=self.t("フォルダー自動整理", "Folder Automation Engine"),
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left", anchor="w")
        lang = ttk.Combobox(heading, textvariable=self.lang, state="readonly",
                            values=("日本語", "English"), width=10)
        lang.pack(side="right")
        lang.bind("<<ComboboxSelected>>", self.change_language)
        ttk.Label(
            frame,
            text=self.t(
                "指定したフォルダーのファイルを、拡張子などの条件に応じて別フォルダーへコピー・移動します。\n"
                "①フォルダーと条件を選択 → ②試運転で対象を確認 → ③確認後に1回実行。",
                "Copy or move files into another folder based on a filename pattern.\n"
                "1. Choose folders and rule → 2. Preview files without changes → 3. Confirm and run once.",
            ),
            wraplength=810, justify="left",
        ).pack(anchor="w", pady=(10, 12))
        editor = ttk.LabelFrame(frame, text=self.t("① 整理する条件", "1. Choose your rule"), padding=12)
        editor.pack(fill="x", pady=(0, 10))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text=self.t("基準フォルダー", "Main folder")).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.root_entry = ttk.Entry(editor, textvariable=self.root_path)
        self.root_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.choose_btn = ttk.Button(
            editor, text=self.t("フォルダーを選ぶ", "Choose folder"), command=self.choose_folder
        )
        self.choose_btn.grid(row=0, column=2, padx=(8, 0))
        rows = [
            (1, "読み込み先の名前（基準内）", "Input folder name (inside main)", self.input_folder),
            (2, "保存先の名前（基準内）", "Output folder name (inside main)", self.output_folder),
            (3, "対象ファイル（例 *.pdf）", "Filename pattern (e.g. *.pdf)", self.pattern),
        ]
        self.entries: list[ttk.Entry] = [self.root_entry]
        for row, ja, en, variable in rows:
            ttk.Label(editor, text=self.t(ja, en)).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=5
            )
            entry = ttk.Entry(editor, textvariable=variable)
            entry.grid(row=row, column=1, columnspan=2, sticky="ew", pady=5)
            self.entries.append(entry)
        ttk.Label(editor, text=self.t("操作", "Action")).grid(row=4, column=0, sticky="w", pady=5)
        self.action_combo = ttk.Combobox(
            editor, textvariable=self.action, values=("copy", "move"), state="readonly", width=16
        )
        self.action_combo.grid(row=4, column=1, sticky="w", pady=5)
        ttk.Label(
            editor, text=self.t(
                "copy = 元ファイルを残す / move = 元ファイルを移す。既存ファイルへの上書きは禁止です。",
                "copy keeps the original; move removes it after safe transfer. Existing files are never overwritten.",
            ), wraplength=740,
        ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(5, 0))
        buttons = ttk.LabelFrame(frame, text=self.t("② 試運転 → ③ 実行", "2. Preview → 3. Run"), padding=8)
        buttons.pack(fill="x", pady=(0, 10))
        self.preview_btn = ttk.Button(
            buttons, text=self.t("試運転（変更なし）", "Dry Run (no changes)"), command=self.preview
        )
        self.preview_btn.pack(side="left", padx=(0, 10))
        self.run_btn = ttk.Button(
            buttons, text=self.t("確認して1回実行", "Confirm and run once"), command=self.run_live
        )
        self.run_btn.pack(side="left", padx=(0, 10))
        self.save_btn = ttk.Button(
            buttons, text=self.t("設定JSONを新規保存", "Save a new JSON config"), command=self.save_config
        )
        self.save_btn.pack(side="left")
        ttk.Label(frame, textvariable=self.status, wraplength=820).pack(anchor="w", pady=(0, 8))
        logframe = ttk.LabelFrame(frame, text=self.t("対象ファイル・実行結果", "Preview and results"), padding=8)
        logframe.pack(fill="both", expand=True)
        self.log = tk.Text(logframe, wrap="word", height=10, state="disabled")
        scrollbar = ttk.Scrollbar(logframe, command=self.log.yview)
        self.log.configure(yscrollcommand=scrollbar.set)
        self.log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        ttk.Label(frame, text=self.t(
            "安全上の制限: この画面は1回実行のみ。常時監視とバックアップ復元検証は別の操作です。",
            "Scope: one-shot processing only. Continuous monitoring and backup verification are separate operations.",
        ), wraplength=820).pack(anchor="w", pady=(8, 0))
        self.set_busy(self.busy)

    def change_language(self, _event=None) -> None:
        if self.busy:
            self.lang.set(self.displayed_language)
            return
        self.build()

    def get_config(self) -> dict:
        return build_config(
            root_dir=self.root_path.get(), input_folder=self.input_folder.get(),
            output_folder=self.output_folder.get(), filename_glob=self.pattern.get(),
            action=self.action.get(),
        )

    def choose_folder(self) -> None:
        if self.busy:
            return
        name = filedialog.askdirectory(parent=self.root)
        if name:
            self.root_path.set(name)

    def append(self, data: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", data.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        state = "disabled" if busy else "normal"
        for entry in self.entries:
            entry.configure(state=state)
        self.action_combo.configure(state="disabled" if busy else "readonly")
        for button in (self.choose_btn, self.preview_btn, self.run_btn, self.save_btn):
            button.configure(state=state)

    def preview(self) -> None:
        if self.busy:
            return
        try:
            config = self.get_config()
        except (OSError, ValueError, ConfigError) as exc:
            messagebox.showerror(self.t("設定エラー", "Invalid configuration"), str(exc), parent=self.root)
            return
        self.preview_revision = None
        self.preview_input_snapshot = None
        self.start_worker("preview", config)

    def run_live(self) -> None:
        if self.busy:
            return
        try:
            config = self.get_config()
        except (OSError, ValueError, ConfigError) as exc:
            messagebox.showerror(self.t("設定エラー", "Invalid configuration"), str(exc), parent=self.root)
            return
        if self.preview_revision != revision(config):
            messagebox.showwarning(
                self.t("試運転が必要", "Dry Run required"),
                self.t("同じ設定の試運転が必要です。先に試運転してください。",
                       "Run Dry Run successfully on these exact settings first."),
                parent=self.root,
            )
            return
        warning = self.t(
            f"「{config['input_dir']}」内の {config['rules'][0]['glob']} を「{config['rules'][0]['destination']}」へ "
            f"{'コピー' if self.action.get() == 'copy' else '移動'}します。既存ファイルは上書きしません。実行しますか？",
            f"Files matching {config['rules'][0]['glob']} in {config['input_dir']} will be "
            f"{'copied' if self.action.get() == 'copy' else 'moved'} to {config['rules'][0]['destination']}. Never overwrite existing files. Continue?",
        )
        if not messagebox.askyesno(self.t("変更を承認", "Confirm filesystem changes"), warning, parent=self.root):
            return
        # Fail-closed even if some files were processed before a later failure.
        self.preview_revision = None
        self.start_worker("live", config)

    def start_worker(self, mode: str, config: dict) -> None:
        self.set_busy(True)
        self.status.set(self.t("試運転中…", "Preview running…") if mode == "preview" else
                        self.t("ファイルを処理中…", "Processing files…"))
        rev = revision(config)
        expected_files = self.preview_input_snapshot if mode == "live" else None
        if mode == "live":
            self.preview_input_snapshot = None

        def work() -> None:
            buf = io.StringIO()
            try:
                actual_files = snapshot_inputs(config)
                if mode == "live" and (expected_files is None or actual_files != expected_files):
                    raise ConfigError(
                        "Files changed after Dry Run. Preview again / 試運転後にファイルが変わりました。再試運転してください"
                    )
                with contextlib.redirect_stdout(buf):
                    count = Engine(config, dry_run=(mode == "preview")).scan_once()
                if mode == "preview" and snapshot_inputs(config) != actual_files:
                    raise ConfigError(
                        "Files changed during Dry Run. Preview again / 試運転中にファイルが変わりました"
                    )
                self.messages.put((mode, True, f"{count} file(s)\n{buf.getvalue()}", rev,
                                   actual_files if mode == "preview" else None))
            except Exception as exc:
                self.messages.put((mode, False, f"{type(exc).__name__}: {exc}", rev, None))
        threading.Thread(target=work, daemon=True).start()

    def poll(self) -> None:
        try:
            while True:
                mode, ok, text, rev, sampled = self.messages.get_nowait()
                self.set_busy(False)
                self.append(format_activity(text, japanese=self.lang.get() == "日本語"))
                if ok and mode == "preview":
                    try:
                        config = self.get_config()
                        unchanged = revision(config) == rev and snapshot_inputs(config) == sampled
                        self.preview_revision = rev if unchanged else None
                        self.preview_input_snapshot = sampled if unchanged else None
                    except (OSError, ValueError, ConfigError):
                        self.preview_revision = None
                        self.preview_input_snapshot = None
                    self.status.set(self.t(
                        "試運転が完了しました。変更対象を確認してから実行してください。" if self.preview_revision else
                        "対象ファイルが変わりました。再試運転してください。",
                        "Dry Run finished. Review the files before running." if self.preview_revision else
                        "Input files changed; please preview again.",
                    ))
                elif ok:
                    self.status.set(self.t("実行が完了しました。", "Execution completed."))
                else:
                    self.preview_revision = None
                    self.preview_input_snapshot = None
                    self.status.set(self.t("失敗しました。元データと保存先を確認してください。",
                                           "Operation failed. Check the source and destination."))
                    messagebox.showerror(self.t("実行エラー", "Operation error"), text[-1500:], parent=self.root)
        except queue.Empty:
            pass
        if self.root.winfo_exists():
            self.root.after(100, self.poll)

    def save_config(self) -> None:
        if self.busy:
            return
        try:
            config = self.get_config()
        except (OSError, ValueError, ConfigError) as exc:
            messagebox.showerror(self.t("設定エラー", "Invalid configuration"), str(exc), parent=self.root)
            return
        name = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".json",
            filetypes=[("JSON", "*.json")], initialfile="folder-rule.json",
        )
        if not name:
            return
        try:
            # Never overwrite a pre-existing config file.
            with Path(name).open("x", encoding="utf-8") as fh:
                json.dump(config, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            self.status.set(self.t("新しい設定JSONを保存しました。", "New configuration JSON saved."))
        except OSError as exc:
            messagebox.showerror(self.t("保存エラー", "Save failed"), str(exc), parent=self.root)


def self_test() -> int:
    """Exercise installed engine wiring without opening windows or touching user files."""
    import tempfile
    with tempfile.TemporaryDirectory(prefix="folder-desktop-selftest-") as folder:
        root = Path(folder)
        inbox = root / "inbox"
        inbox.mkdir()
        (inbox / "sample.pdf").write_bytes(b"self-test only")
        config = build_config(
            root_dir=str(root), input_folder="inbox", output_folder="processed",
            filename_glob="*.pdf", action="copy",
        )
        if config["rules"][0]["overwrite"] is not False:
            raise RuntimeError("Unsafe overwrite in default rule")
        with contextlib.redirect_stdout(io.StringIO()):
            handled = Engine(config, dry_run=True).scan_once()
        if handled != 1 or (root / "processed").exists() or (root / ".state").exists():
            raise RuntimeError("Packaged Dry Run did not preserve local files")
    print("FOLDER_DESKTOP_SELF_TEST_OK")
    return 0


def main() -> None:
    root = tk.Tk()
    FolderDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--self-test"]:
        raise SystemExit(self_test())
    main()
