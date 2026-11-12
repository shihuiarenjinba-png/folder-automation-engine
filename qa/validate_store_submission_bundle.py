"""Fail-closed validation for Folder Automation Engine Store submission bundles.

This tool never opens Partner Center and never uploads anything. It only validates
the machine-readable handoff consumed by the owner's submission automation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

CONTRACT = "folder-standard-store-submission-smoke-v2"
SHA256_HEX_LEN = 64


def _present(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return value is not None and value != "" and value != []


def evaluate(data: dict[str, Any]) -> tuple[str, list[str]]:
    missing: list[str] = []
    if data.get("contract") != CONTRACT:
        missing.append("contract")
    if data.get("mode") not in {"VALIDATE_ONLY", "DRY_RUN", "UPLOAD"}:
        missing.append("mode")

    product = data.get("product") or {}
    if product.get("kind") != "app" or product.get("edition") != "standard":
        missing.append("product")
    package = data.get("package") or {}
    if package.get("format") != "msix" or package.get("architecture") != "x64":
        missing.append("package_format")
    sha = package.get("sha256")
    if _present(sha) and (not isinstance(sha, str) or len(sha) != SHA256_HEX_LEN
                          or any(ch not in "0123456789abcdefABCDEF" for ch in sha)):
        missing.append("package_sha256_format")

    store = data.get("store") or {}
    listing = data.get("listing") or {}
    proof = data.get("proof") or {}
    permissions = data.get("permissions") or {}
    guards = data.get("guards") or {}
    distribution = data.get("distribution") or {}

    audience = distribution.get("audience")
    if audience not in {"PRIVATE_AUDIENCE_TEST", "PUBLIC_RELEASE"}:
        missing.append("distribution.audience")
    if distribution.get("publishing_hold") != "MANUAL":
        missing.append("distribution.publishing_hold")
    if audience == "PRIVATE_AUDIENCE_TEST":
        if not _present(distribution.get("known_user_group")):
            missing.append("distribution.known_user_group")
        if distribution.get("public_release_approved") is not False:
            missing.append("distribution.public_release_approved_must_be_false")
    elif audience == "PUBLIC_RELEASE":
        if distribution.get("public_release_approved") is not True:
            missing.append("distribution.public_release_approved")

    for guard in (
        "fail_closed_on_identity_mismatch", "fail_closed_on_sha_mismatch",
        "fail_closed_on_missing_proof", "forbid_duplicate_product",
        "do_not_invent_question_answers", "do_not_skip_certification_fields",
        "require_manual_approval_for_each_write_phase",
    ):
        if guards.get(guard) is not True:
            missing.append(f"guard:{guard}")

    # VALIDATE_ONLY may intentionally contain blanks. A complete upload bundle
    # must satisfy every item below before the automation may mutate Partner Center.
    ready_requirements = {
        "package.path": package.get("path"),
        "package.sha256": package.get("sha256"),
        "package.source_commit": package.get("source_commit"),
        "package.artifact_id": package.get("artifact_id"),
        "package.msix_version": package.get("msix_version"),
        "package.inventory_path": package.get("inventory_path"),
        "package.third_party_notices_path": package.get("third_party_notices_path"),
        "package.verified_by_operator": package.get("verified_by_operator") is True,
        "store.partner_center_reverified": store.get("partner_center_reverified") is True,
        "store.accepted_version_history_verified": store.get("accepted_version_history_verified") is True,
        "store.price": store.get("price"),
        "store.markets": store.get("markets"),
        "store.age_rating": store.get("age_rating"),
        "store.privacy_policy": store.get("privacy_policy"),
        "store.support_contact": store.get("support_contact"),
        "listing.ja.short_description": (listing.get("ja") or {}).get("short_description"),
        "listing.ja.long_description": (listing.get("ja") or {}).get("long_description"),
        "listing.ja.screenshots": (listing.get("ja") or {}).get("screenshots"),
        "listing.en.short_description": (listing.get("en") or {}).get("short_description"),
        "listing.en.long_description": (listing.get("en") or {}).get("long_description"),
        "listing.en.screenshots": (listing.get("en") or {}).get("screenshots"),
        "listing.final_logo": listing.get("final_logo"),
        "listing.owner_approved": listing.get("owner_approved") is True,
        "proof.filesystem_safety_qa_pass": proof.get("filesystem_safety_qa_pass") is True,
        "proof.symlink_junction_qa_complete": proof.get("symlink_junction_qa_complete") is True,
        "proof.third_party_notices_approved": proof.get("third_party_notices_approved") is True,
        "permissions.owner_upload_approval": permissions.get("owner_upload_approval") is True,
        "distribution.audience": audience,
        "distribution.publishing_hold": distribution.get("publishing_hold"),
    }
    if audience == "PRIVATE_AUDIENCE_TEST":
        ready_requirements.update({
            "proof.pre_store_ci_gui_pass": proof.get("pre_store_ci_gui_pass") is True,
            "proof.private_audience_listing_screenshots_approved":
                proof.get("private_audience_listing_screenshots_approved") is True,
        })
    elif audience == "PUBLIC_RELEASE":
        ready_requirements.update({
            "proof.windows_user_gui_qa_pass": proof.get("windows_user_gui_qa_pass") is True,
            "proof.store_signed_install_qa_pass": proof.get("store_signed_install_qa_pass") is True,
            "proof.all_screenshots_genuine": proof.get("all_screenshots_genuine") is True,
        })
    readiness_missing = [key for key, value in ready_requirements.items() if not _present(value)]

    if permissions.get("submit_certification") or permissions.get("publish"):
        missing.append("write_phase_too_broad_for_upload_gate")
    if permissions.get("upload_package") and not permissions.get("owner_upload_approval"):
        missing.append("upload_without_owner_approval")

    missing.extend(readiness_missing)
    if missing:
        state = "HOLD"
    elif audience == "PRIVATE_AUDIENCE_TEST":
        state = "PRIVATE_AUDIENCE_UPLOAD_READY"
    else:
        state = "PUBLIC_STORE_UPLOAD_READY"
    return state, sorted(set(missing))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args()
    data = json.loads(args.bundle.read_text(encoding="utf-8"))
    state, missing = evaluate(data)
    print(json.dumps({"state": state, "missing": missing}, ensure_ascii=False, indent=2))
    if args.require_ready and state not in {"PRIVATE_AUDIENCE_UPLOAD_READY", "PUBLIC_STORE_UPLOAD_READY"}:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
