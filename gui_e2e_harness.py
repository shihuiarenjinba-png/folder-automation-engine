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
        app=GUI()
        errors=[]
        infos=[]
        try:
            app.withdraw()
            app.update()
            browse=buttons(app,"参照")
            assert len(browse)==4
            with patch.object(filedialog,"askdirectory",return_value=str(source)):
                browse[0].invoke()
            with patch.object(filedialog,"askdirectory",return_value=str(backup)):
                browse[1].invoke()
            with patch.object(filedialog,"askdirectory",return_value=str(reports)):
                browse[3].invoke()
            assert app.source.get()==str(source) and app.backup.get()==str(backup)
            with patch.object(messagebox,"showinfo",side_effect=lambda *args: infos.append(args)), \
                 patch.object(messagebox,"showerror",side_effect=lambda *args: errors.append(args)), \
                 patch.object(messagebox,"askyesno",return_value=True), \
                 patch.object(filedialog,"asksaveasfilename",return_value=str(manifest)):
                make=buttons(app,"① 元データのmanifestを新規作成")
                verify_button=buttons(app,"② バックアップを検証")
                assert len(make)==len(verify_button)==1
                make[0].invoke()
                assert manifest.is_file()
                assert app.manifest.get()==str(manifest)
                with patch.object(filedialog,"askopenfilename",return_value=str(manifest)):
                    browse[2].invoke()
                assert app.manifest.get()==str(manifest)
                verify_button[0].invoke()
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
                verify_button[0].invoke()
                second=[x for x in reports.glob("backup_verify_*/verification.json") if x not in result_files]
                assert len(second)==1
                corrupt=json.loads(second[0].read_text(encoding="utf-8"))
                assert corrupt["status"]=="REVIEW"
                assert {x["code"] for x in corrupt["findings"]}&{"size_mismatch","hash_mismatch"}
                assert (source/"a.txt").read_bytes()==original
                assert infos and not errors, errors
            with target.open("x",encoding="utf-8") as out:
                json.dump({"status":"GUI_E2E_OK","scenario":"select -> manifest -> verify -> corrupted backup detection",
                           "actual_output_verified":True,"input_unchanged":True,
                           "negative_case_verified":True,"interactive_human_test":False},out,ensure_ascii=False,indent=2)
        finally:
            app.destroy()
