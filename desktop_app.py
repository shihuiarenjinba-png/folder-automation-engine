from __future__ import annotations

import contextlib
import io
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from folder_automation import ConfigError, Engine
from ui_language import load_language, save_language

APP_ID = "folder-automation-engine"


class FolderAutomationDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.lang = load_language(APP_ID)
        self.root.geometry("940x720")
        self.root.minsize(820, 620)
        self.config_path = tk.StringVar()
        self.status = tk.StringVar(value="")
        self.stop_event = threading.Event()
        self.monitor_thread: threading.Thread | None = None
        self.config: dict | None = None
        self._build()
        default = Path(__file__).resolve().parent / "config.example.json"
        if default.is_file():
            self.config_path.set(str(default))
            self._load_config(show_error=False)
        else:
            self.status.set(self.t("準備完了", "Ready"))

    def t(self, ja: str, en: str) -> str:
        return en if self.lang == "en" else ja

    def _build(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(self.t("フォルダ自動化", "Folder Automation Engine"))

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        language = ttk.Frame(outer)
        language.pack(fill="x", pady=(0, 8))
        ttk.Label(language, text="言語 / Language", font=("Segoe UI", 9, "bold")).pack(side="right", padx=(0, 6))
        self.language_var = tk.StringVar(value="日本語" if self.lang == "ja" else "English")
        combo = ttk.Combobox(language, textvariable=self.language_var, values=("日本語", "English"), state="readonly", width=10)
        combo.pack(side="right")
        combo.bind("<<ComboboxSelected>>", self._language_changed)

        ttk.Label(outer, text=self.t("フォルダ自動化", "Folder Automation Engine"), font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(
            outer,
            text=self.t("決められたフォルダとルールだけを処理するローカル自動化", "Local automation that only processes configured folders and rules."),
        ).pack(anchor="w", pady=(0, 14))

        cfg = ttk.LabelFrame(outer, text=self.t("設定ファイル", "Configuration"), padding=10)
        cfg.pack(fill="x", pady=(0, 10))
        ttk.Entry(cfg, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg, text=self.t("選択", "Browse"), command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(cfg, text=self.t("検証", "Validate"), command=self._validate).pack(side="left", padx=(6, 0))

        self.summary = ttk.Treeview(outer, columns=("key", "value"), show="headings", height=6)
        self.summary.heading("key", text=self.t("項目", "Item"))
        self.summary.heading("value", text=self.t("内容", "Value"))
        self.summary.column("key", width=190, anchor="w")
        self.summary.column("value", width=650, anchor="w")
        self.summary.pack(fill="x", pady=(0, 10))

        actions = ttk.LabelFrame(outer, text=self.t("実行", "Run"), padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.dry_btn = ttk.Button(actions, text=self.t("1回確認（Dry Run）", "Dry Run Once"), command=lambda: self._run_once(True))
        self.dry_btn.pack(side="left")
        self.run_btn = ttk.Button(actions, text=self.t("1回実行", "Run Once"), command=lambda: self._run_once(False))
        self.run_btn.pack(side="left", padx=6)
        self.start_btn = ttk.Button(actions, text=self.t("監視開始", "Start Monitor"), command=self._start_monitor)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(actions, text=self.t("停止", "Stop"), command=self._stop_monitor, state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        ttk.Label(
            actions,
            text=self.t("Dry Runはコピー/移動もprocessed記録も行いません。", "Dry Run does not copy/move files or mark them as processed."),
            wraplength=430,
        ).pack(side="right")

        logbox = ttk.LabelFrame(outer, text=self.t("実行ログ", "Activity"), padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", height=18, state="disabled", font=("Consolas", 9))
        scroll = ttk.Scrollbar(logbox, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))

        if self.monitor_thread is not None:
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.dry_btn.configure(state="disabled")
            self.run_btn.configure(state="disabled")

    def _language_changed(self, _event=None) -> None:
        self.lang = "en" if self.language_var.get() == "English" else "ja"
        save_language(APP_ID, self.lang)
        current_status = self.status.get()
        self._build()
        if self.config is not None:
            try:
                self._show_summary(Engine(self.config, dry_run=True))
            except Exception:
                pass
        if self.monitor_thread is not None:
            self.status.set(self.t("監視中", "Monitoring"))
        elif current_status:
            self.status.set(self.t("準備完了", "Ready"))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(
            title=self.t("フォルダ自動化JSONを選択", "Choose Folder Automation JSON"),
            filetypes=[("JSON", "*.json"), (self.t("すべてのファイル", "All files"), "*.*")],
        )
        if path:
            self.config_path.set(path)
            self._load_config(show_error=True)

    def _read_config(self) -> dict:
        path = Path(self.config_path.get()).expanduser().resolve()
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ConfigError("config root must be an object")
        return raw

    def _load_config(self, show_error: bool) -> bool:
        try:
            config = self._read_config()
            engine = Engine(config, dry_run=True)
            self.config = config
            self._show_summary(engine)
            self.status.set(self.t("設定OK", "Configuration valid"))
            return True
        except Exception as exc:
            self.config = None
            self.status.set(self.t(f"設定エラー: {type(exc).__name__}", f"Configuration error: {type(exc).__name__}"))
            if show_error:
                messagebox.showerror(self.t("設定エラー", "Configuration error"), str(exc), parent=self.root)
            return False

    def _validate(self) -> None:
        self._load_config(show_error=True)

    def _show_summary(self, engine: Engine) -> None:
        for item in self.summary.get_children():
            self.summary.delete(item)
        values = [
            (self.t("ルート", "Root"), str(engine.root)),
            (self.t("入力フォルダ", "Inbox"), str(engine.input_dir)),
            (self.t("監視間隔", "Poll interval"), f"{engine.interval:g} sec"),
            (self.t("ルール数", "Rules"), str(len(engine.rules))),
            ("State DB", str(engine.state_db)),
            (self.t("上書き", "Overwrite"), self.t("ルール単位・既定false", "Per rule; default false")),
        ]
        for row in values:
            self.summary.insert("", "end", values=row)

    def _append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text.rstrip() + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.dry_btn.configure(state=state)
        self.run_btn.configure(state=state)
        self.start_btn.configure(state=state if self.monitor_thread is None else "disabled")

    def _run_once(self, dry_run: bool) -> None:
        if not self._load_config(show_error=True):
            return
        assert self.config is not None
        config = self.config
        self._set_busy(True)
        self.status.set(self.t("確認中…", "Dry Run…") if dry_run else self.t("実行中…", "Running…"))

        def worker() -> None:
            buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(buffer):
                    handled = Engine(config, dry_run=dry_run).scan_once()
                detail = buffer.getvalue() or f"handled={handled}"
                self.root.after(0, lambda: self._finish_once(True, detail, handled, dry_run))
            except Exception as exc:
                detail = buffer.getvalue() + f"ERROR: {type(exc).__name__}: {exc}"
                self.root.after(0, lambda: self._finish_once(False, detail, 0, dry_run))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_once(self, ok: bool, detail: str, handled: int, dry_run: bool) -> None:
        self._append_log(detail)
        if ok:
            prefix = self.t("確認完了", "Dry Run complete") if dry_run else self.t("実行完了", "Run complete")
            self.status.set(f"{prefix} / handled={handled}")
        else:
            self.status.set(self.t("失敗", "Failed"))
        self._set_busy(False)
        if not ok:
            messagebox.showerror(self.t("フォルダ自動化", "Folder Automation"), detail[-1500:], parent=self.root)

    def _start_monitor(self) -> None:
        if not self._load_config(show_error=True) or self.monitor_thread is not None:
            return
        assert self.config is not None
        config = self.config
        self.stop_event.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.dry_btn.configure(state="disabled")
        self.run_btn.configure(state="disabled")
        self.status.set(self.t("監視中", "Monitoring"))

        def loop() -> None:
            try:
                engine = Engine(config, dry_run=False)
                while not self.stop_event.is_set():
                    buffer = io.StringIO()
                    with contextlib.redirect_stdout(buffer):
                        handled = engine.scan_once()
                    text = buffer.getvalue()
                    if text or handled:
                        self.root.after(0, lambda t=text, h=handled: self._append_log(t or f"handled={h}"))
                    self.stop_event.wait(engine.interval)
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror(self.t("監視エラー", "Monitor error"), f"{type(exc).__name__}: {exc}", parent=self.root))
            finally:
                self.root.after(0, self._monitor_stopped)

        self.monitor_thread = threading.Thread(target=loop, daemon=True)
        self.monitor_thread.start()

    def _stop_monitor(self) -> None:
        self.stop_event.set()
        self.status.set(self.t("停止中…", "Stopping…"))

    def _monitor_stopped(self) -> None:
        self.monitor_thread = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.dry_btn.configure(state="normal")
        self.run_btn.configure(state="normal")
        self.status.set(self.t("停止しました", "Stopped"))


def main() -> None:
    root = tk.Tk()
    FolderAutomationDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
