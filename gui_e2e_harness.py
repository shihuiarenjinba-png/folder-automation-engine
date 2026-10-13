"""Compiled backup verifier GUI E2E with safe synthetic source+backup files."""
from __future__ import annotations
import json
import sys
import tempfile
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from unittest.mock import patch


def buttons(app, label):
    found=[]
    def visit(n):
        for w in n.winfo_children():
            if isinstance(w, ttk.Button) and w.cget("text")==label:
                found.append(w)
            visit(w)
    visit(app)
    return found


def run(GUI):
    if len(sys.argv)!=3 or sys.argv[1]!="--e2e-test":
        raise ValueError("Usage: --e2e-test <proof.json>")
    target=Path(sys.argv[2]).resolve()
    trace=target.with_suffix(".trace.txt")
    def mark(stage):
        with trace.open("a", encoding="utf-8") as log:
            log.write(stage + "\n")
    mark("begin")
    with tempfile.TemporaryDirectory(prefix="backup_gui_e2e_") as folder:
        root=Path(folder)
        source=root/"source"
        backup=root/"backup"
        reports=root/"reports"
        source.mkdir()
        backup.mkdir()
        original=b"trusted business file 1234"
        (source/"a.txt").write_bytes(original)
        (backup/"a.txt").write_bytes(original)
        manifest=root/"trusted_manifest.json"
        mark("before_gui")
        app=GUI()
        mark("after_gui")
        errors=[]
        infos=[]
        try:
            app.withdraw()
            app.update()
            mark("after_update")
            browse=buttons(app,"参照")
            assert len(browse)==4
            with patch.object(filedialog,"askdirectory",return_value=str(source)):
                browse[0].invoke()
                mark("selected_source")
            with patch.object(filedialog,"askdirectory",return_value=str(backup)):
                browse[1].invoke()
                mark("selected_backup")
            with patch.object(filedialog,"askdirectory",return_value=str(reports)):
                browse[3].invoke()
                mark("selected_reports")
            assert app.source.get()==str(source) and app.backup.get()==str(backup)
            with patch.object(messagebox,"showinfo",side_effect=lambda *args: infos.append(args)), \
                 patch.object(messagebox,"showerror",side_effect=lambda *args: errors.append(args)), \
                 patch.object(messagebox,"askyesno",return_value=True), \
                 patch.object(filedialog,"asksaveasfilename",return_value=str(manifest)):
                make=buttons(app,"① 元データのmanifestを新規作成")
                verify_button=buttons(app,"② バックアップを検証")
                assert len(make)==len(verify_button)==1
                mark("before_manifest")
                make[0].invoke()
                mark(f"after_manifest exists={manifest.is_file()}, app_path={app.manifest.get()!r}, errors={errors!r}, status={app.status.get()!r}")
                assert manifest.is_file()
                assert app.manifest.get()==str(manifest)
                with patch.object(filedialog,"askopenfilename",return_value=str(manifest)):
                    browse[2].invoke()
                    mark("selected_manifest")
                assert app.manifest.get()==str(manifest)
                mark("before_verify")
                verify_button[0].invoke()
                mark("after_verify")
                result_files=list(reports.glob("backup_verify_*/verification.json"))
                assert len(result_files)==1, result_files
                data=json.loads(result_files[0].read_text(encoding="utf-8"))
                assert data["summary"]["verified"]==1
                assert data["summary"]["sample_restored"]==1
                assert data["summary"]["findings"]==0
                assert (source/"a.txt").read_bytes()==original
                assert (backup/"a.txt").read_bytes()==original
                # Simulate a corrupt backup and require failure notification.
                (backup/"a.txt").write_bytes(b"tampered")
                mark("tampered_backup")
                verify_button[0].invoke()
                second=[x for x in reports.glob("backup_verify_*/verification.json") if x not in result_files]
                assert len(second)==1
                corrupt=json.loads(second[0].read_text(encoding="utf-8"))
                assert corrupt["status"]=="REVIEW"
                assert {x["code"] for x in corrupt["findings"]}&{"size_mismatch","hash_mismatch"}
                assert (source/"a.txt").read_bytes()==original
                assert infos and not errors, errors
            mark("before_proof")
            with target.open("x",encoding="utf-8") as out:
                json.dump({"status":"GUI_E2E_OK","scenario":"select -> manifest -> verify -> corrupted backup detection",
                           "actual_output_verified":True,"input_unchanged":True,
                           "negative_case_verified":True,"interactive_human_test":False},out,ensure_ascii=False,indent=2)
        finally:
            app.destroy()
