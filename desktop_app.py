from __future__ import annotations

import contextlib
import io
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from folder_automation import ConfigError, Engine


class FolderAutomationDesktop:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Folder Automation Engine / フォルダ自動化")
        self.root.geometry("940x700")
        self.root.minsize(820, 600)
        self.config_path = tk.StringVar()
        self.status = tk.StringVar(value="Ready / 準備完了")
        self.stop_event = threading.Event()
        self.monitor_thread: threading.Thread | None = None
        self.config: dict | None = None
        self._build()
        default = Path(__file__).resolve().parent / "config.example.json"
        if default.is_file():
            self.config_path.set(str(default))
            self._load_config(show_error=False)

    def _build(self) -> None:
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Folder Automation Engine", font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(outer, text="決められたフォルダとルールだけを処理するローカル自動化").pack(anchor="w", pady=(0, 14))

        cfg = ttk.LabelFrame(outer, text="Configuration / 設定", padding=10)
        cfg.pack(fill="x", pady=(0, 10))
        ttk.Entry(cfg, textvariable=self.config_path).pack(side="left", fill="x", expand=True)
        ttk.Button(cfg, text="Browse / 選択", command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(cfg, text="Validate / 検証", command=self._validate).pack(side="left", padx=(6, 0))

        self.summary = ttk.Treeview(outer, columns=("key", "value"), show="headings", height=6)
        self.summary.heading("key", text="Item / 項目")
        self.summary.heading("value", text="Value / 内容")
        self.summary.column("key", width=190, anchor="w")
        self.summary.column("value", width=650, anchor="w")
        self.summary.pack(fill="x", pady=(0, 10))

        actions = ttk.LabelFrame(outer, text="Run / 実行", padding=10)
        actions.pack(fill="x", pady=(0, 10))
        self.dry_btn = ttk.Button(actions, text="Dry Run Once / 1回確認", command=lambda: self._run_once(True))
        self.dry_btn.pack(side="left")
        self.run_btn = ttk.Button(actions, text="Run Once / 1回実行", command=lambda: self._run_once(False))
        self.run_btn.pack(side="left", padx=6)
        self.start_btn = ttk.Button(actions, text="Start Monitor / 監視開始", command=self._start_monitor)
        self.start_btn.pack(side="left")
        self.stop_btn = ttk.Button(actions, text="Stop / 停止", command=self._stop_monitor, state="disabled")
        self.stop_btn.pack(side="left", padx=6)
        ttk.Label(actions, text="Dry Runはコピー/移動もprocessed記録も行いません。", wraplength=430).pack(side="right")

        logbox = ttk.LabelFrame(outer, text="Activity / 実行ログ", padding=8)
        logbox.pack(fill="both", expand=True)
        self.log = tk.Text(logbox, wrap="word", height=18, state="disabled", font=("Consolas", 9))
        scroll = ttk.Scrollbar(logbox, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        ttk.Label(outer, textvariable=self.status).pack(fill="x", pady=(8, 0))

    def _browse(self) -> None:
        path = filedialog.askopenfilename(title="Folder Automation JSON", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
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
            self.status.set("Configuration valid / 設定OK")
            return True
        except Exception as exc:
            self.config = None
            self.status.set(f"Configuration error / 設定エラー: {type(exc).__name__}")
            if show_error:
                messagebox.showerror("Configuration", str(exc))
            return False

    def _validate(self) -> None:
        self._load_config(show_error=True)

    def _show_summary(self, engine: Engine) -> None:
        for item in self.summary.get_children():
            self.summary.delete(item)
        values = [
            ("Root / ルート", str(engine.root)),
            ("Inbox / 入力", str(engine.input_dir)),
            ("Poll / 監視間隔", f"{engine.interval:g} sec"),
            ("Rules / ルール数", str(len(engine.rules))),
            ("State DB", str(engine.state_db)),
            ("Overwrite / 上書き", "Per rule; default false / ルール単位・既定false"),
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
        self.status.set("Dry Run… / 確認中…" if dry_run else "Running… / 実行中…")
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
        self.status.set(("Dry Run complete" if dry_run else "Run complete") + f" / handled={handled}" if ok else "Failed / 失敗")
        self._set_busy(False)
        if not ok:
            messagebox.showerror("Folder Automation", detail[-1500:])

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
        self.status.set("Monitoring / 監視中")
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
                self.root.after(0, lambda: messagebox.showerror("Monitor", f"{type(exc).__name__}: {exc}"))
            finally:
                self.root.after(0, self._monitor_stopped)
        self.monitor_thread = threading.Thread(target=loop, daemon=True)
        self.monitor_thread.start()

    def _stop_monitor(self) -> None:
        self.stop_event.set()
        self.status.set("Stopping… / 停止中…")

    def _monitor_stopped(self) -> None:
        self.monitor_thread = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.dry_btn.configure(state="normal")
        self.run_btn.configure(state="normal")
        self.status.set("Stopped / 停止しました")


def main() -> None:
    root = tk.Tk()
    FolderAutomationDesktop(root)
    root.mainloop()


if __name__ == "__main__":
    main()
