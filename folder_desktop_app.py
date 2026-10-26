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
from folder_desktop_flow import build_config, build_multi_config, revision, snapshot_inputs, format_activity
from ui_preferences import load_preferences, save_preferences

_GUI_PREF_PRODUCT = "FolderAutomationEngine"
_GUI_PREF_FIELDS = ("locale",)
_GUI_LANGUAGES = ("日本語", "English")


def load_gui_language() -> str:
    """Read only the allowlisted locale, without changing a damaged settings file."""
    try:
        value = load_preferences(_GUI_PREF_PRODUCT, _GUI_PREF_FIELDS).get("locale", "日本語")
    except (OSError, ValueError):
        return "日本語"
    return value if value in _GUI_LANGUAGES else "日本語"


def save_gui_language(language: str) -> None:
    if language not in _GUI_LANGUAGES:
        raise ValueError("Unsupported GUI language")
    save_preferences(_GUI_PREF_PRODUCT, {"locale": language}, _GUI_PREF_FIELDS)


def validate_saved_config(data: object) -> dict:
    """Accept only exact, safe Folder GUI config schema (never enable overwrite)."""
    if not isinstance(data, dict):
        raise ConfigError("Saved configuration must be a JSON object")
    rules = data.get("rules")
    if not isinstance(rules, list) or not 1 <= len(rules) <= 10 or any(
        not isinstance(item, dict) for item in rules
    ):
        raise ConfigError("Saved configuration must contain 1–10 folder rules")
    try:
        first = rules[0]
        rebuilt = build_multi_config(
            root_dir=data["root_dir"], input_folder=data["input_dir"],
            output_folder=first["destination"], filename_glob=first["glob"],
            action=first["action"],
            extra_rules=[
                {"destination": r["destination"], "glob": r["glob"], "action": r["action"]}
                for r in rules[1:]
            ],
        )
    except (KeyError, TypeError, AttributeError) as exc:
        raise ConfigError("Missing or invalid saved rule fields") from exc
    if rebuilt != data:
        raise ConfigError("Saved configuration was changed or enables unsupported settings")
    return rebuilt


class FolderDesktop:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Folder Automation Engine")
        self.root.geometry("960x740")
        self.root.minsize(720, 570)
        self.lang = tk.StringVar(value=load_gui_language())
        self.displayed_language = self.lang.get()
        self.root_path = tk.StringVar()
        self.input_folder = tk.StringVar(value="inbox")
        self.output_folder = tk.StringVar(value="processed")
        self.pattern = tk.StringVar(value="*.pdf")
        self.action = tk.StringVar(value="copy")
        self.extra_rules: list[dict] = []
        self.status = tk.StringVar(value="")
        self.preview_summary = tk.StringVar(value="")
        self.watch_indicator = tk.StringVar(value="")
        self.advanced_visible = False
        self.preview_revision: str | None = None
        self.preview_input_snapshot: tuple | None = None
        self.busy = False
        self.watch_active = False
        self.watch_stop = threading.Event()
        self.watch_thread: threading.Thread | None = None
        self.worker_thread: threading.Thread | None = None
        self.closing = False
        self.watch_seconds = tk.StringVar(value="60")
        self.messages: queue.Queue[tuple[str, bool, str, str, tuple | None]] = queue.Queue()
        self.build()
        for variable in (self.root_path, self.input_folder, self.output_folder, self.pattern, self.action):
            variable.trace_add("write", self._invalidate_preview_on_edit)
        self.root.protocol("WM_DELETE_WINDOW", self.request_close)
        self.root.after(100, self.poll)

    def t(self, ja: str, en: str) -> str:
        return en if self.lang.get() == "English" else ja

    def build(self) -> None:
        self.displayed_language = self.lang.get()
        for child in self.root.winfo_children():
            child.destroy()
        shell = ttk.Frame(self.root)
        shell.pack(fill="both", expand=True)
        self.preview_summary.set(self.t(
            "① フォルダーと条件を選んで試運転してください。変更はまだ行われません。",
            "Choose folders and preview first. No files change during preview."))
        history = ttk.LabelFrame(shell, text=self.t(
            "③ 対象ファイル・実行結果（常に表示）",
            "3. Files and activity (always visible)"), padding=9)
        history.pack(side="bottom", fill="x", padx=12, pady=(3, 10))
        ttk.Label(history, textvariable=self.preview_summary,
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 5))
        self.watch_indicator.set(self.t("監視停止中", "Watching off"))
        ttk.Label(history, textvariable=self.watch_indicator).pack(anchor="e")
        ttk.Label(history, textvariable=self.status, wraplength=820).pack(anchor="w")
        logframe = ttk.Frame(history)
        logframe.pack(fill="x", pady=(4, 0))
        self.log = tk.Text(logframe, wrap="word", height=5, state="disabled",
                           bg="#f7fafd", fg="#21384f", padx=8, pady=6, relief="flat")
        logscroll = ttk.Scrollbar(logframe, command=self.log.yview)
        self.log.configure(yscrollcommand=logscroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        logscroll.pack(side="right", fill="y")
        formhost = ttk.Frame(shell)
        formhost.pack(fill="both", expand=True, padx=10, pady=(7, 0))
        canvas = tk.Canvas(formhost, highlightthickness=0)
        scrollbar = ttk.Scrollbar(formhost, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        frame = ttk.Frame(canvas, padding=18)
        window = canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda _event: canvas.configure(
            scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(
            window, width=event.width))
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
                "① 親フォルダーを選ぶ → 整理元と整理先を選ぶ → ② 試運転 → 結果確認 → 実行",
                "1. Choose a parent folder and two subfolders → 2. Preview → Review results → Run",
            ),
            wraplength=810, justify="left",
        ).pack(anchor="w", pady=(10, 12))
        editor = ttk.LabelFrame(frame, text=self.t("① 整理する条件", "1. Choose your rule"), padding=12)
        editor.pack(fill="x", pady=(0, 10))
        editor.columnconfigure(1, weight=1)
        ttk.Label(editor, text=self.t("親フォルダー", "Parent folder")).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=5
        )
        self.root_entry = ttk.Entry(editor, textvariable=self.root_path)
        self.root_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.choose_btn = ttk.Button(
            editor, text=self.t("フォルダーを選ぶ", "Choose folder"), command=self.choose_folder
        )
        self.choose_btn.grid(row=0, column=2, padx=(8, 0))
        rows = [
            (1, "整理するフォルダー（親の直下）", "Source subfolder (inside parent)", self.input_folder),
            (2, "コピー・移動先（親の直下）", "Destination subfolder (inside parent)", self.output_folder),
            (3, "対象ファイル（例 *.pdf）", "Filename pattern (e.g. *.pdf)", self.pattern),
        ]
        self.entries: list[ttk.Entry] = [self.root_entry]
        self.child_browse_buttons = []
        for row, ja, en, variable in rows:
            ttk.Label(editor, text=self.t(ja, en)).grid(
                row=row, column=0, sticky="w", padx=(0, 8), pady=5
            )
            entry = ttk.Entry(editor, textvariable=variable)
            entry.grid(row=row, column=1, sticky="ew", pady=5)
            self.entries.append(entry)
            if row <= 2:
                browse = ttk.Button(editor, text=self.t("選択", "Choose"),
                    command=lambda v=variable: self.choose_child_folder(v))
                browse.grid(row=row, column=2, padx=(8, 0))
                self.child_browse_buttons.append(browse)
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
        self.rules_btn = ttk.Button(
            editor, text=self.t("複数ルールを追加・並べ替え（最大10件）",
                                "Add and reorder rules (up to 10)"),
            command=self.manage_rules)
        self.rules_btn.grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 1))
        buttons = ttk.LabelFrame(frame, text=self.t("② 試運転 → ③ 実行", "2. Preview → 3. Run"), padding=8)
        buttons.pack(fill="x", pady=(0, 10))
        self.preview_btn = ttk.Button(
            buttons, text=self.t("試運転（変更なし）", "Dry Run (no changes)"), command=self.preview
        )
        self.preview_btn.pack(side="left", padx=(0, 14), ipady=7, ipadx=8)
        self.run_btn = tk.Button(
            buttons, text=self.t("確認して実行", "Confirm and run"),
            command=self.run_live, bg="#1966ba", fg="white", activebackground="#14518f",
            activeforeground="white", relief="flat", bd=0, padx=18, pady=8,
            font=("Segoe UI", 10, "bold"), cursor="hand2"
        )
        self.run_btn.pack(side="left", padx=(0, 10))
        configs = ttk.Frame(frame)
        configs.pack(fill="x", pady=(0, 10))
        self.save_btn = ttk.Button(
            configs, text=self.t("設定JSONを新規保存", "Save new JSON config"), command=self.save_config
        )
        self.save_btn.pack(side="left", padx=(0, 10))
        self.load_btn = ttk.Button(
            configs, text=self.t("保存済み設定を読み込む", "Load saved JSON config"), command=self.load_config
        )
        self.load_btn.pack(side="left")
        watcher = ttk.LabelFrame(frame, text=self.t("④ 安全な常時監視（任意）", "4. Opt-in folder watcher"), padding=8)
        watcher.pack(fill="x", pady=(0, 10))
        ttk.Label(watcher, text=self.t("監視間隔（秒）", "Check every (seconds)")).pack(side="left")
        self.watch_interval_entry = ttk.Entry(watcher, textvariable=self.watch_seconds, width=7)
        self.watch_interval_entry.pack(side="left", padx=(6, 10))
        self.watch_start_btn = ttk.Button(watcher, text=self.t("監視を開始", "Start watching"),
                                          command=self.start_watch)
        self.watch_start_btn.pack(side="left")
        self.watch_stop_btn = ttk.Button(watcher, text=self.t("監視を停止", "Stop watching"),
                                         command=self.stop_watch)
        self.watch_stop_btn.pack(side="left", padx=(7, 0))
        ttk.Label(watcher, text=self.t(
            "開始時にルールを承認します。今後届くファイルにも適用します。PCとアプリの稼働中のみ。",
            "Approved rule also processes future files. Runs only while app and PC stay on."),
            wraplength=360).pack(side="right", padx=(12, 0))


        ttk.Label(frame, text=self.t(
            "安全: 常時監視は任意・承認したルールのみ。バックアップ復元検証は別画面です。",
            "Safety: watch mode is optional and uses only the approved rule. Backup verification is separate.",
        ), wraplength=820).pack(anchor="w", pady=(8, 0))
        self.set_busy(self.busy)

    def change_language(self, _event=None) -> None:
        if self.busy or self.watch_active:
            self.lang.set(self.displayed_language)
            return
        language = self.lang.get()
        if language not in _GUI_LANGUAGES:
            self.lang.set(self.displayed_language)
            return
        if language != self.displayed_language:
            try:
                save_gui_language(language)
            except (OSError, ValueError) as exc:
                self.lang.set(self.displayed_language)
                messagebox.showerror(
                    self.t("言語の保存に失敗", "Could not save language preference"),
                    str(exc), parent=self.root,
                )
                return
        self.build()

    def get_config(self) -> dict:
        return build_multi_config(
            root_dir=self.root_path.get(), input_folder=self.input_folder.get(),
            output_folder=self.output_folder.get(), filename_glob=self.pattern.get(),
            action=self.action.get(), extra_rules=getattr(self, "extra_rules", []),
        )

    def manage_rules(self) -> None:
        """Edit additional ordered rules in a modal without touching files."""
        if self.busy or self.watch_active:
            return
        draft = [dict(x) for x in self.extra_rules]
        dialog = tk.Toplevel(self.root)
        dialog.title(self.t("追加ルールの管理", "Manage additional rules"))
        dialog.geometry("730x490")
        dialog.transient(self.root)
        dialog.grab_set()
        container = ttk.Frame(dialog, padding=12)
        container.pack(fill="both", expand=True)
        ttk.Label(container, text=self.t(
            "最初のルールはメイン画面で設定します。ここでは第2ルール以降を追加します。"
            "先に一致したルールが適用され、後ろのルールは実行されません。",
            "Rule 1 is on the main screen. Add rules 2–10 here. First matching rule wins."),
            wraplength=690).pack(anchor="w", pady=(0, 9))
        listbox = ttk.Treeview(container, columns=("glob","destination","action"),
                               show="headings", height=8)
        for name, label in [
            ("glob",self.t("対象名", "Filename pattern")),
            ("destination",self.t("保存先", "Destination")),
            ("action",self.t("操作", "Action")),
        ]:
            listbox.heading(name, text=label)
            listbox.column(name, width=205 if name != "action" else 95)
        listbox.pack(fill="both", expand=True)
        editor = ttk.Frame(container)
        editor.pack(fill="x", pady=(10, 5))
        glob = tk.StringVar(value="*.csv")
        dest = tk.StringVar(value="csv-files")
        act = tk.StringVar(value="copy")
        for idx, (label, var) in enumerate([
            (self.t("パターン", "Pattern"), glob),
            (self.t("移動・コピー先", "Destination"), dest),
            (self.t("操作", "Action"), act)
        ]):
            ttk.Label(editor, text=label).grid(row=0, column=idx, sticky="w")
            if idx == 2:
                entry = ttk.Combobox(editor, textvariable=var, values=("copy","move"),
                                     state="readonly", width=12)
            else:
                entry = ttk.Entry(editor, textvariable=var, width=26)
            entry.grid(row=1, column=idx, sticky="ew", padx=(0, 10))
            editor.columnconfigure(idx, weight=1)
        btns = ttk.Frame(container)
        btns.pack(fill="x", pady=6)

        def refresh():
            listbox.delete(*listbox.get_children())
            for i, item in enumerate(draft):
                listbox.insert("", "end", iid=str(i),
                               values=(item["glob"], item["destination"], item["action"]))

        def add():
            proposed = {"glob": glob.get().strip(), "destination": dest.get().strip(),
                        "action": act.get()}
            try:
                build_multi_config(
                    root_dir=self.root_path.get(), input_folder=self.input_folder.get(),
                    output_folder=self.output_folder.get(), filename_glob=self.pattern.get(),
                    action=self.action.get(), extra_rules=draft + [proposed])
            except (ConfigError, ValueError, OSError) as exc:
                messagebox.showerror(self.t("ルールを確認", "Invalid rule"),
                                     str(exc), parent=dialog)
                return
            draft.append(proposed)
            refresh()

        def remove():
            selected = listbox.selection()
            if selected:
                draft.pop(int(selected[0]))
                refresh()

        def shift(diff):
            selected = listbox.selection()
            if not selected:
                return
            index = int(selected[0])
            target = index + diff
            if 0 <= target < len(draft):
                draft[index], draft[target] = draft[target], draft[index]
                refresh()
                listbox.selection_set(str(target))

        ttk.Button(btns, text=self.t("+ 追加", "+ Add"), command=add).pack(side="left")
        ttk.Button(btns, text=self.t("削除", "Remove"), command=remove).pack(side="left", padx=6)
        ttk.Button(btns, text="↑", command=lambda: shift(-1)).pack(side="left", padx=3)
        ttk.Button(btns, text="↓", command=lambda: shift(1)).pack(side="left", padx=3)
        ttk.Button(btns, text=self.t("キャンセル", "Cancel"), command=dialog.destroy
                   ).pack(side="right")
        def accept():
            try:
                build_multi_config(
                    root_dir=self.root_path.get(), input_folder=self.input_folder.get(),
                    output_folder=self.output_folder.get(), filename_glob=self.pattern.get(),
                    action=self.action.get(), extra_rules=draft)
            except (ConfigError, ValueError, OSError) as exc:
                messagebox.showerror(self.t("ルールを確認", "Invalid rules"),
                                     str(exc), parent=dialog)
                return
            self.extra_rules = draft
            self.preview_revision = None
            self.preview_input_snapshot = None
            self.status.set(self.t(
                f"ルール{len(draft)+1}件を設定しました。再試運転してください。",
                f"{len(draft)+1} rule(s) configured. Run Dry Run again."))
            dialog.destroy()
        ttk.Button(btns, text=self.t("ルールを適用", "Apply rules"), command=accept
                   ).pack(side="right", padx=6)
        refresh()
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        self.root.wait_window(dialog)

    def choose_folder(self) -> None:
        if self.busy or self.watch_active:
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
        closing = getattr(self, "closing", False)
        state = "disabled" if busy or self.watch_active or closing else "normal"
        for entry in self.entries:
            entry.configure(state=state)
        self.action_combo.configure(
            state="disabled" if busy or self.watch_active or closing else "readonly"
        )
        for button in (self.choose_btn, self.preview_btn, self.save_btn, self.load_btn,
                       self.rules_btn, self.advanced_btn, *self.child_browse_buttons):
            button.configure(state=state)
        self.run_btn.configure(
            state="normal" if state == "normal" and self.preview_revision is not None else "disabled"
        )
        self.watch_interval_entry.configure(state=state)
        self.watch_start_btn.configure(state=state)
        self.watch_stop_btn.configure(
            state="normal" if self.watch_active and not closing else "disabled"
        )

    def preview(self) -> None:
        if self.busy or self.watch_active:
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
        if self.busy or self.watch_active:
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
        preview_rules = "\n".join(
            f"{i+1}. {item['glob']} → {item['destination']} ({item['action']})"
            for i, item in enumerate(config["rules"]))
        warning = self.t(
            f"次の{len(config['rules'])}ルールを順番に評価し、各ファイルの最初に一致するルールを実行します。"
            f"\n{preview_rules}\n既存ファイルは上書きしません。よろしいですか？",
            f"Evaluate {len(config['rules'])} rule(s) in order (first match wins):"
            f"\n{preview_rules}\nNever overwrite existing files. Continue?",
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
        self.worker_thread = threading.Thread(target=work, daemon=True)
        self.worker_thread.start()

    def start_watch(self) -> None:
        if self.busy or self.watch_active:
            return
        try:
            interval = int(self.watch_seconds.get())
            if not 10 <= interval <= 3600:
                raise ConfigError("Watch interval must be 10–3600 seconds")
            config = self.get_config()
            expected = self.preview_input_snapshot
            if self.preview_revision != revision(config) or expected is None:
                raise ConfigError("Run a successful Dry Run on the unchanged rule first")
        except (ValueError, OSError, ConfigError) as exc:
            messagebox.showwarning(self.t("監視の設定", "Watcher setup"), str(exc),
                                   parent=self.root)
            return
        if not messagebox.askyesno(self.t("今後のファイルも処理します", "Process future files"),
                self.t(
                    "このルールを今後フォルダーに届くファイルにも自動適用します。"
                    "既存ファイルは上書きしません。アプリを閉じると停止します。開始しますか？",
                    "Apply this approved copy/move rule to future incoming files too? "
                    "Existing files are not overwritten. Watching stops if app exits."),
                parent=self.root):
            return
        self.preview_revision = None
        self.preview_input_snapshot = None
        self.watch_stop.clear()
        self.watch_active = True
        self.set_busy(False)
        self.status.set(self.t("監視を開始中…", "Starting watcher…"))

        def work() -> None:
            buffer = io.StringIO()
            try:
                if snapshot_inputs(config) != expected:
                    raise ConfigError("Files changed after Dry Run; restart preview")
                engine = Engine(config, dry_run=False)
                previous = expected
                while not self.watch_stop.is_set():
                    # Future files must be unchanged across two scans. A file
                    # still being written may not be copied at first sight.
                    current = snapshot_inputs(config)
                    stable = {item[0] for item in current if item in previous}
                    eligible = set()
                    for name in stable:
                        source_path = engine.input_dir / name
                        if source_path.is_file() and not source_path.is_symlink():
                            eligible.add(engine.signature(source_path))
                    buffer.seek(0)
                    buffer.truncate()
                    with contextlib.redirect_stdout(buffer):
                        count = engine.scan_once(eligible_signatures=eligible)
                    if count or buffer.getvalue():
                        self.messages.put(("watch", True, f"{count} file(s)\n{buffer.getvalue()}",
                                           "", None))
                    previous = current
                    if self.watch_stop.wait(interval):
                        break
            except Exception as exc:
                self.messages.put(("watch", False, f"{type(exc).__name__}: {exc}", "", None))
            finally:
                self.messages.put(("watch_done", True, "", "", None))

        self.watch_thread = threading.Thread(target=work, daemon=True)
        self.watch_thread.start()

    def stop_watch(self) -> None:
        if self.watch_active:
            self.watch_stop.set()
            self.status.set(self.t("監視の終了処理中…", "Stopping after current scan…"))

    def request_close(self) -> None:
        """Close only after active file work reaches a safe boundary."""
        if getattr(self, "closing", False):
            return
        worker = getattr(self, "worker_thread", None)
        watcher = getattr(self, "watch_thread", None)
        if not ((worker and worker.is_alive()) or (watcher and watcher.is_alive())):
            self.root.destroy()
            return
        self.closing = True
        self.watch_stop.set()
        self.status.set(self.t(
            "安全に終了しています。現在の処理が終わるまでお待ちください…",
            "Closing safely. Waiting for the current file operation to finish…",
        ))
        self.set_busy(self.busy)
        self.root.after(100, self._finish_close_when_safe)

    def _finish_close_when_safe(self) -> None:
        worker = getattr(self, "worker_thread", None)
        watcher = getattr(self, "watch_thread", None)
        if (worker and worker.is_alive()) or (watcher and watcher.is_alive()):
            self.root.after(100, self._finish_close_when_safe)
            return
        self.root.destroy()

    def poll(self) -> None:
        try:
            while True:
                mode, ok, text, rev, sampled = self.messages.get_nowait()
                if mode in {"watch", "watch_done"}:
                    if text:
                        self.append(format_activity(text, japanese=self.lang.get() == "日本語"))
                    if not ok:
                        self.watch_stop.set()
                        self.watch_active = False
                        self.status.set(self.t("監視はエラーで停止しました", "Watcher stopped after error"))
                        messagebox.showerror(self.t("監視エラー", "Watcher error"), text[-1500:],
                                             parent=self.root)
                    elif mode == "watch_done":
                        self.watch_active = False
                        self.status.set(self.t("監視を停止しました", "Watcher stopped"))
                    elif ok:
                        self.status.set(self.t("監視中（ルールによる処理が完了）",
                                               "Watching (scan completed)"))
                    self.set_busy(False)
                    continue
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

    def load_config(self) -> None:
        """Restore a deliberately selected saved JSON without file operations."""
        if self.busy or self.watch_active:
            return
        name = filedialog.askopenfilename(
            parent=self.root, filetypes=[("JSON", "*.json")]
        )
        if not name:
            return
        try:
            path = Path(name)
            if path.is_symlink() or path.stat().st_size > 65536:
                raise ConfigError("Unsafe config path or JSON larger than 64 KiB")
            saved = json.loads(path.read_text(encoding="utf-8"))
            config = validate_saved_config(saved)
        except (OSError, ValueError, ConfigError, UnicodeError) as exc:
            messagebox.showerror(
                self.t("設定の読込エラー", "Could not load saved config"),
                str(exc), parent=self.root,
            )
            return
        self.root_path.set(config["root_dir"])
        self.input_folder.set(config["input_dir"])
        self.output_folder.set(config["rules"][0]["destination"])
        self.pattern.set(config["rules"][0]["glob"])
        self.action.set(config["rules"][0]["action"])
        self.extra_rules = [
            {"destination": r["destination"], "glob": r["glob"], "action": r["action"]}
            for r in config["rules"][1:]
        ]
        self.preview_revision = None
        self.preview_input_snapshot = None
        self.status.set(self.t(
            "設定を読み込みました。再度試運転してから実行してください。",
            "Config loaded. Run a new Dry Run before any live action.",
        ))

    def save_config(self) -> None:
        if self.busy or self.watch_active:
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
    # --windowed PyInstaller executables may have sys.stdout=None.
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
