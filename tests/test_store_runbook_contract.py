from pathlib import Path
import unittest


class FolderStoreRunbookContractTests(unittest.TestCase):
    def test_frozen_store_candidate_and_local_conveyor_contract(self):
        root = Path(__file__).resolve().parents[1]
        text = (
            root / "store" / "LOCAL_INITIAL_DRAFT_AND_STORE_FIELDS_RUNBOOK_20261116.md"
        ).read_text(encoding="utf-8")

        for required in (
            "51597b389384be6cf2b3d85c09ee66099b80807e",
            "911f8eb13abfdbb51bea8f279006d138d6be9cba4a25413416c1d70458676450",
            "SourceCheckoutMode ContainedCommit",
            "run_store_preupload_readiness.ps1",
            "READY_FOR_MSIX_UPLOAD_APPROVAL",
            "APPLICATION_CONTROL_BLOCKED",
        ):
            self.assertIn(required, text)

        self.assertIn("do not pass `-RunSelfTest`", text)
        self.assertIn("do not rebuild", text.lower())
        self.assertIn("coordinate clicking is not part", text)
        self.assertIn("Package upload", text)
        self.assertIn("separate", text.lower())


if __name__ == "__main__":
    unittest.main()
