"""Tests for the Store submission handoff validator."""
import copy
import unittest

from qa.validate_store_submission_bundle import CONTRACT, evaluate


def ready_bundle():
    return {
        "contract": CONTRACT,
        "mode": "UPLOAD",
        "product": {"kind": "app", "edition": "standard"},
        "package": {
            "format": "msix", "architecture": "x64", "path": "C:/final/app.msix",
            "sha256": "a" * 64, "source_commit": "b" * 40, "artifact_id": 1,
            "msix_version": "1.0.0.0", "inventory_path": "inventory.json",
            "third_party_notices_path": "THIRD_PARTY_NOTICES", "verified_by_operator": True,
        },
        "store": {
            "partner_center_reverified": True, "accepted_version_history_verified": True,
            "price": "OWNER_APPROVED", "markets": ["JP"], "age_rating": "OWNER_APPROVED",
            "privacy_policy": "OWNER_APPROVED", "support_contact": "OWNER_APPROVED",
        },
        "listing": {
            "ja": {"short_description": "a", "long_description": "b", "screenshots": ["ja.png"]},
            "en": {"short_description": "a", "long_description": "b", "screenshots": ["en.png"]},
            "final_logo": "logo.png", "owner_approved": True,
        },
        "proof": {
            "pre_store_ci_gui_pass": True,
            "private_audience_listing_screenshots_approved": True,
            "windows_user_gui_qa_pass": False,
            "store_signed_install_qa_pass": False,
            "filesystem_safety_qa_pass": True,
            "symlink_junction_qa_complete": True,
            "third_party_notices_approved": True,
            "all_screenshots_genuine": False,
        },
        "permissions": {
            "owner_upload_approval": True, "upload_package": True,
            "submit_certification": False, "publish": False,
        },
        "distribution": {
            "audience": "PRIVATE_AUDIENCE_TEST",
            "known_user_group": "owner-local-testers",
            "publishing_hold": "MANUAL",
            "public_release_approved": False,
        },
        "guards": {
            "fail_closed_on_identity_mismatch": True, "fail_closed_on_sha_mismatch": True,
            "fail_closed_on_missing_proof": True, "forbid_duplicate_product": True,
            "do_not_invent_question_answers": True, "do_not_skip_certification_fields": True,
            "require_manual_approval_for_each_write_phase": True,
        },
    }


class StoreSubmissionBundleTests(unittest.TestCase):
    def test_complete_upload_bundle_is_ready(self):
        state, missing = evaluate(ready_bundle())
        self.assertEqual(state, "PRIVATE_AUDIENCE_UPLOAD_READY")
        self.assertEqual(missing, [])

    def test_validate_only_draft_is_hold_not_crash(self):
        data = ready_bundle()
        data["mode"] = "VALIDATE_ONLY"
        data["package"]["path"] = None
        data["permissions"]["owner_upload_approval"] = False
        data["permissions"]["upload_package"] = False
        state, missing = evaluate(data)
        self.assertEqual(state, "HOLD")
        self.assertIn("package.path", missing)
        self.assertIn("permissions.owner_upload_approval", missing)

    def test_identity_or_proof_guard_cannot_be_disabled(self):
        data = ready_bundle()
        data["guards"]["fail_closed_on_identity_mismatch"] = False
        state, missing = evaluate(data)
        self.assertEqual(state, "HOLD")
        self.assertIn("guard:fail_closed_on_identity_mismatch", missing)

    def test_submit_or_publish_permission_is_rejected_at_upload_gate(self):
        for key in ("submit_certification", "publish"):
            data = ready_bundle()
            data["permissions"][key] = True
            with self.subTest(key=key):
                state, missing = evaluate(data)
                self.assertEqual(state, "HOLD")
                self.assertIn("write_phase_too_broad_for_upload_gate", missing)

    def test_private_audience_requires_known_user_group(self):
        data = ready_bundle()
        data["distribution"]["known_user_group"] = None
        state, missing = evaluate(data)
        self.assertEqual(state, "HOLD")
        self.assertIn("distribution.known_user_group", missing)

    def test_private_audience_cannot_be_marked_public_release(self):
        data = ready_bundle()
        data["distribution"]["public_release_approved"] = True
        state, missing = evaluate(data)
        self.assertEqual(state, "HOLD")
        self.assertIn("distribution.public_release_approved_must_be_false", missing)

    def test_manual_publishing_hold_is_required(self):
        data = ready_bundle()
        data["distribution"]["publishing_hold"] = "AUTO"
        state, missing = evaluate(data)
        self.assertEqual(state, "HOLD")
        self.assertIn("distribution.publishing_hold", missing)

    def test_private_audience_does_not_require_store_signed_install_qa(self):
        data = ready_bundle()
        state, missing = evaluate(data)
        self.assertEqual(state, "PRIVATE_AUDIENCE_UPLOAD_READY")
        self.assertNotIn("proof.windows_user_gui_qa_pass", missing)
        self.assertNotIn("proof.store_signed_install_qa_pass", missing)

    def test_public_release_requires_store_signed_install_qa_and_final_screenshots(self):
        data = ready_bundle()
        data["distribution"].update({
            "audience": "PUBLIC_RELEASE",
            "known_user_group": None,
            "public_release_approved": True,
        })
        data["proof"]["windows_user_gui_qa_pass"] = False
        data["proof"]["store_signed_install_qa_pass"] = False
        data["proof"]["all_screenshots_genuine"] = False
        state, missing = evaluate(data)
        self.assertEqual(state, "HOLD")
        self.assertIn("proof.windows_user_gui_qa_pass", missing)
        self.assertIn("proof.store_signed_install_qa_pass", missing)
        self.assertIn("proof.all_screenshots_genuine", missing)

    def test_public_release_ready_after_store_signed_qa(self):
        data = ready_bundle()
        data["distribution"].update({
            "audience": "PUBLIC_RELEASE",
            "known_user_group": None,
            "public_release_approved": True,
        })
        data["proof"]["windows_user_gui_qa_pass"] = True
        data["proof"]["store_signed_install_qa_pass"] = True
        data["proof"]["all_screenshots_genuine"] = True
        state, missing = evaluate(data)
        self.assertEqual(state, "PUBLIC_STORE_UPLOAD_READY")
        self.assertEqual(missing, [])

    def test_bad_sha_format_is_rejected(self):
        data = ready_bundle()
        data["package"]["sha256"] = "not-a-sha"
        state, missing = evaluate(data)
        self.assertEqual(state, "HOLD")
        self.assertIn("package_sha256_format", missing)


if __name__ == "__main__":
    unittest.main()
