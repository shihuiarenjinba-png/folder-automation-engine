import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "store"
NS = "http://schemas.microsoft.com/appx/manifest/foundation/windows10"
UAP10 = "http://schemas.microsoft.com/appx/manifest/uap/windows10/10"


class StoreIdentityDraftTests(unittest.TestCase):
    def test_identity_manifest_and_onedir_contract(self):
        identity = json.loads((STORE / "product_identity.json").read_text(encoding="utf-8"))
        self.assertEqual(identity["store_id"], "9P99MJX1R4V6")
        self.assertEqual(identity["package_identity_name"], "OkinawaDesktopTools.FolderAutomationEngine")
        self.assertEqual(identity["publisher"], "CN=46263F21-A700-41DB-8C9B-114C22FB82FC")
        self.assertIs(identity["submission_allowed"], False)
        text = (STORE / "AppxManifest.template.xml").read_text(encoding="utf-8")
        for key, value in {"__PACKAGE_IDENTITY_NAME__": identity["package_identity_name"], "__PUBLISHER__": identity["publisher"], "__PUBLISHER_DISPLAY_NAME__": identity["publisher_display_name"], "__VERSION__": identity["initial_msix_version"]}.items():
            text = text.replace(key, value)
        root = ET.fromstring(text); app = root.find(f".//{{{NS}}}Application")
        self.assertEqual(app.attrib["Executable"], "FolderAutomationEngine.exe")
        self.assertEqual(app.attrib[f"{{{UAP10}}}RuntimeBehavior"], "packagedClassicApp")
        self.assertIsNotNone(root.find(".//{*}Capability[@Name='runFullTrust']"))
        builder = (STORE / "build_msix_draft.ps1").read_text(encoding="utf-8")
        self.assertIn('Join-Path $payload "_internal"', builder)
        self.assertIn('onedir_runtime_verified=$true', builder)
        self.assertIn('symlink_safety_tests_complete=$false', builder)
        self.assertIn('sale_approved=$false', builder)
        workflow=(ROOT/".github"/"workflows"/"folder-desktop-store-draft.yml").read_text(encoding="utf-8")
        self.assertIn("build-folder-desktop-validation.ps1",workflow)
        self.assertIn("store/build_msix_draft.ps1",workflow)
        self.assertIn("FolderAutomationEngine-Store-MSIX-UNSIGNED-DRAFT",workflow)


if __name__ == "__main__":
    unittest.main()

