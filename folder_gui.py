"""Offline folder-rule GUI; no arbitrary shell commands or hidden tasks."""
import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from folder_automation import ConfigError, Engine


class FolderWindow(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=12)
        self.pack(fill="both", expand=True)
        self.root_dir = tk.StringVar(value=str(Path.home() / "FolderAutomation"))
        self.input_dir = tk.StringVar(value="inbox")
        self.glob = tk.StringVar(value="*.csv")
        self.action = tk.StringVar(value="copy")
        self.output = tk.StringVar(value="processed")
        self.status = tk.StringVar(value="Create rules and preview the matching files.")
        self.rules = []
        self.stop = threading.Event()
        self.worker = None
        self.columnconfigure(1, weight=1)
        self.rowconfigure(6, weight=1)
        for row, (label, var) in enumerate((("Working folder", self.root_dir),
                                            ("Input folder (under working folder)", self.input_dir),
                                            ("File match (glob)", self.glob))):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w")
            ttk.Entry(self, textvariable=var).grid(row=row, column=1, sticky="ew", pady=5)
        ttk.Button(self, text="Browse", command=self.browse).grid(row=0, column=2)
        ttk.Label(self, text="Action").grid(row=3, column=0, sticky="w")
        ttk.Combobox(self, values=("copy", "move"), textvariable=self.action,
                     state="readonly").grid(row=3, column=1, sticky="w")
        ttk.Label(self, text="Output folder").grid(row=4, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.output).grid(row=4, column=1, sticky="ew")
        ttk.Button(self, text="Add rule", command=self.add).grid(row=5, column=0)
        ttk.Button(self, text="Remove selected", command=self.remove).grid(row=5, column=1, sticky="w")
        self.items = tk.Listbox(self, exportselection=False, height=9)
        self.items.grid(row=6, column=0, columnspan=3, sticky="nsew")
        buttons = ttk.Frame(self)
        buttons.grid(row=7, column=0, columnspan=3, sticky="w", pady=8)
        for title, callback in (("Load", self.load), ("Save", self.save),
                                ("Preview", self.preview), ("Run once", self.run_once),
                                ("Start monitoring", self.start), ("Stop", self.stop_monitor)):
            ttk.Button(buttons, text=title, command=callback).pack(side="left", padx=3)
        ttk.Label(self, textvariable=self.status, wraplength=750).grid(
            row=8, column=0, columnspan=3, sticky="w")
        master.protocol("WM_DELETE_WINDOW", self.close)

    def browse(self):
        path = filedialog.askdirectory()
        if path:
            self.root_dir.set(path)

    def refresh(self):
        self.items.delete(0, "end")
        for rule in self.rules:
            self.items.insert("end", f"{rule['glob']}  → {rule['action']} → {rule['destination']}")

    def add(self):
        if not self.glob.get().strip() or not self.output.get().strip():
            messagebox.showerror("Invalid rule", "Match pattern and destination are required")
            return
        self.rules.append({"glob": self.glob.get().strip(), "action": self.action.get(),
                           "destination": self.output.get().strip(), "overwrite": False})
        self.refresh()

    def remove(self):
        selected = self.items.curselection()
        if selected:
            self.rules.pop(selected[0])
            self.refresh()

    def config(self):
        if not self.rules:
            raise ConfigError("At least one rule is required")
        if not self.input_dir.get().strip():
            raise ConfigError("Input folder is required")
        cfg = {"root_dir": str(Path(self.root_dir.get()).expanduser().resolve()),
               "input_dir": self.input_dir.get().strip(),
               "poll_seconds": 5, "min_stable_seconds": 3,
               "state_db": ".state/processed.sqlite3", "rules": list(self.rules)}
        engine = Engine(cfg, dry_run=True)
        for rule in self.rules:
            engine.destination(rule["destination"], engine.input_dir / "sample.csv")
        return cfg

    def preview(self):
        try:
            count = Engine(self.config(), dry_run=True).scan_once()
            self.status.set(f"Preview: {count} eligible files. No changes made.")
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))

    def save(self):
        try:
            cfg = self.config()
            path = filedialog.asksaveasfilename(defaultextension=".json")
            if path:
                with Path(path).open("x", encoding="utf-8") as stream:
                    json.dump(cfg, stream, ensure_ascii=False, indent=2)
                self.status.set("Saved " + path)
        except Exception as exc:
            messagebox.showerror("Not saved", str(exc))

    def load(self):
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            Engine(data, dry_run=True)
            self.root_dir.set(data["root_dir"])
            self.input_dir.set(data["input_dir"])
            self.rules = data["rules"]
            self.refresh()
        except Exception as exc:
            messagebox.showerror("Cannot load", str(exc))

    def run_once(self):
        try:
            cfg = self.config()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        if messagebox.askyesno("Process files", "Apply copy/move rules to eligible files now?"):
            self._launch(cfg, monitor=False)

    def start(self):
        if self.worker and self.worker.is_alive():
            self.status.set("Monitoring is already active.")
            return
        try:
            cfg = self.config()
        except Exception as exc:
            messagebox.showerror("Invalid settings", str(exc))
            return
        if messagebox.askyesno("Monitor", "Start monitoring while this window is open?"):
            self.stop.clear()
            self._launch(cfg, monitor=True)

    def _launch(self, cfg, monitor):
        self.status.set("Monitoring..." if monitor else "Processing...")
        def work():
            try:
                engine = Engine(cfg)
                total = 0
                while True:
                    total += engine.scan_once()
                    if not monitor or self.stop.wait(engine.interval):
                        break
                self.after(0, self.status.set, f"Completed; processed {total} files.")
            except Exception as exc:
                self.after(0, self.status.set, "Stopped after an error: " + str(exc))
        self.worker = threading.Thread(target=work, daemon=True)
        self.worker.start()

    def stop_monitor(self):
        self.stop.set()
        self.status.set("Stopping after the current file.")

    def close(self):
        self.stop.set()
        self.winfo_toplevel().destroy()


def main():
    root = tk.Tk()
    root.title("Folder Automation Engine")
    root.minsize(820, 520)
    FolderWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
