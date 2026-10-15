"""Generated sources only; synthetic owners are NOT real packaging permissions."""
from copy import deepcopy
import json
from pathlib import Path

import numpy as np
from PIL import Image, PngImagePlugin
import pytest

from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_bundle_v4 as v4
from src.vision import colour_qa as qa
from src.vision import colour_policy as policy
from test_exploratory_bundle import draft_fixture, authorization
from test_colour_qa import profile_fixture
from test_colour_policy import sparse_profile_fixture, set_distribution, set_gamut


@pytest.fixture
def setup(tmp_path, monkeypatch):
    draft = draft_fixture()
    for i in range(181):
        row = deepcopy(draft["records"][0])
        identifier = "00591" if i == 0 else f"{1000+i:05}"
        row.update(source_record_id="Training/"+identifier,
                   image_path="Dataset/Training/Images/"+identifier+".jpg",
                   technical_candidate=False, draft_exclusion_reasons=["synthetic hold"],
                   content_group_id="possible" if i == 0 else f"held-{i}")
        draft["records"].append(row)
    sources = tmp_path / "sources"
    selected = legacy.select_candidates(draft)
    for row in selected:
        path = sources / row["image_path"]; path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (100, 100), (128, 128, 128)).save(path, format="PNG")
    monkeypatch.setattr(legacy, "EXPECTED_COUNTS", {"Training": 2, "Validation": 2})
    monkeypatch.setattr(legacy, "EXPECTED_GRADES", {"Training": [0, 1, 0, 0, 1], "Validation": [0, 1, 1, 0, 0]})
    monkeypatch.setattr(legacy, "CAM_IDS", ("Validation/00003",))
    monkeypatch.setattr(legacy, "CANDIDATE_IDENTITY_SHA", v4._identity(selected))
    # Only filesystem location and pinned synthetic constants change in tests.
    # Actual draft selection, 181-hold validation, hashes and authorization run.
    monkeypatch.setattr(legacy, "new_ignored_output", lambda path, category: Path(path))
    return {"tmp": tmp_path, "draft": draft, "sources": sources,
            "draft_path": tmp_path / "draft.json", "inventory": tmp_path / "inventory.json",
            "output": tmp_path / "generated_bundle_v4", "monkeypatch": monkeypatch}


def prepare(case):
    case["draft"]["input_sha256"] = {}
    case["draft_path"].write_text(json.dumps(case["draft"]))
    case["monkeypatch"].setattr(legacy, "DRAFT_SHA", legacy.sha256(case["draft_path"]))
    entries = []
    for row in case["draft"]["records"]:
        if not row["technical_candidate"]: continue
        path = case["sources"] / row["image_path"]
        with Image.open(path) as image: width, height = image.size
        entries.append({"split": row["original_split"], "image_path": row["image_path"],
                        "sha256": legacy.sha256(path), "width": width, "height": height})
    entries.append({"split": "Test", "image_path": "DO_NOT_DECODE", "sha256": "DO_NOT_DECODE"})
    case["inventory"].write_text(json.dumps({"result": {"manifest": entries}}, indent=2)+"\n")
    plan, held = v4._prepare(case["draft_path"], case["inventory"])
    assert held == 181
    return plan


def package(case, auth=None):
    plan = prepare(case)
    if auth is None:
        auth = authorization(v4.SCOPE, **v4.authorization_bindings(plan, case["output"]))
    return v4.package_development(case["draft_path"], case["inventory"], case["sources"],
                                  case["output"], auth, opt_in=True)


def read(case, result):
    return v4.validate_bundle(case["output"], result["bundle_manifest_sha256"])[0]


def rewrite(case, bundle):
    path = case["output"] / "bundle_manifest.json"
    path.write_text(json.dumps(bundle, allow_nan=False))
    return legacy.sha256(path)


def test_v4_roundtrip_real_checks_181_holds_and_legacy_no_fallback(setup):
    before = {p: p.read_bytes() for p in setup["sources"].rglob("*.jpg")}
    result = package(setup)
    bundle = read(setup, result)
    assert len(bundle["records"]) == 4 and len(bundle["files"]) == 5
    assert bundle["checked_context"]["held_count"] == 181
    assert not bundle["qualified_labels_approved"] and not bundle["final_research_approved"]
    for row in bundle["records"]:
        assert row["colour_evidence"]["qa_sha256"] == policy.measurement_digest(row["colour_measurements"])
        assert all(v["reference"].startswith("v4-checked-receipt:") for v in row["colour_evidence"]["checks"].values())
    assert all(p.read_bytes() == value for p, value in before.items())
    with pytest.raises(ValueError): legacy.validate_bundle(setup["output"])


def test_source_shadow_reverse_exceeds_two_only_in_v4(setup):
    source = np.repeat((np.arange(100, dtype=np.uint8) % 32)[None, :, None], 3, axis=2)
    source = Image.fromarray(np.repeat(source, 100, axis=0))
    source.info["icc_profile"] = profile_fixture(2.2)[0]
    path = setup["sources"] / setup["draft"]["records"][0]["image_path"]
    source.save(path, format="PNG", icc_profile=source.info["icc_profile"])
    with pytest.raises(ValueError, match="round-trip"):
        legacy.export_rgb_png(source, setup["tmp"] / "legacy_rejected.png")
    result = package(setup)
    row = read(setup, result)["records"][0]
    assert row["colour_roundtrip_max_channel_error"] > legacy.ROUNDTRIP_LIMIT == 2
    assert not (setup["tmp"] / "legacy_rejected.png").exists()


@pytest.mark.parametrize("criterion", ["mean_delta_e", "tail_delta_e", "max_delta_e", "extent", "gamut_excursion"])
def test_every_gate_enforced_before_write_and_again_post_export(setup, monkeypatch, criterion):
    result = package(setup)
    bundle = read(setup, result)
    def violate(report):
        report = deepcopy(report)
        if criterion in {"mean_delta_e", "tail_delta_e", "max_delta_e"}:
            set_distribution(report, criterion, {"mean_delta_e": .491, "tail_delta_e": .991, "max_delta_e": 1.991}[criterion])
        elif criterion == "extent": set_gamut(report, 11, .001)
        else: set_gamut(report, 1, .008)
        return report
    row = bundle["records"][0]
    row["colour_measurements"] = violate(row["colour_measurements"])
    row["colour_roundtrip_max_channel_error"] = row["colour_measurements"]["reverse_rgb"]["per_pixel_max"]["max"]
    row["colour_evidence"] = v4._receipt_evidence(row["colour_measurements"], row["colour_receipt"])
    verdict = policy.evaluate_option_a(row["colour_measurements"], row["colour_evidence"])
    expected = {"gamut_count", "gamut_fraction"} if criterion == "extent" else {criterion}
    assert set(verdict["failed_checks"]) == expected
    with pytest.raises(ValueError, match="Option A colour rejection"):
        v4.validate_bundle(setup["output"], rewrite(setup, bundle))
    real_qa = qa.diagnose_forward_colour
    monkeypatch.setattr(qa, "diagnose_forward_colour", lambda *a, **k: violate(real_qa(*a, **k)))
    setup["output"] = setup["tmp"] / "must_stop_v4"
    with pytest.raises(ValueError, match="Option A colour rejection"):
        package(setup)
    assert not list(setup["output"].rglob("*.png")) and not setup["output"].with_suffix(".zip").exists()


@pytest.mark.parametrize("change", ["old_scope", "code_sha256", "colour_policy_sha256", "export_version", "source_plan_sha256", "no_opt_in"])
def test_old_stale_or_missing_permission_rejected_before_decode(setup, monkeypatch, change):
    plan = prepare(setup)
    auth = authorization(v4.SCOPE, **v4.authorization_bindings(plan, setup["output"]))
    if change == "old_scope": auth["scope"] = "package_development"
    elif change != "no_opt_in": auth[change] = "stale"
    def forbidden(*args, **kwargs): pytest.fail("unauthorized source decode")
    monkeypatch.setattr(Image, "open", forbidden)
    with pytest.raises(ValueError):
        v4.package_development(setup["draft_path"], setup["inventory"], setup["sources"],
                               setup["output"], auth, opt_in=change != "no_opt_in")
    assert not setup["output"].exists()


@pytest.mark.parametrize("change", ["held_count", "held_selected", "np015", "protected", "duplicate", "test", "clinical_approval"])
def test_real_source_selection_checks_not_caller_boolean_claims(setup, change):
    prepare(setup)  # Valid inventory first: rejection must concern the changed draft.
    draft = setup["draft"]
    if change == "held_count": draft["records"].pop()
    elif change == "held_selected": draft["records"][4]["technical_candidate"] = True
    elif change == "np015":
        row=draft["records"][0]; row.update(source_record_id="Training/00591", image_path="Dataset/Training/Images/00591.jpg")
    elif change == "protected": draft["records"][0]["content_group_id"] = "sealed"
    elif change == "duplicate": draft["records"][2]["content_group_id"] = draft["records"][0]["content_group_id"]
    elif change == "test": draft["records"][0]["original_split"] = "Test"
    else: draft["records"][0]["qualified_label_approved"] = True
    # No file/header decode is required to reject these pinned synthetic drafts.
    draft["input_sha256"] = {}
    setup["draft_path"].write_text(json.dumps(draft))
    setup["monkeypatch"].setattr(legacy, "DRAFT_SHA", legacy.sha256(setup["draft_path"]))
    expected_message = "Frozen holds/cohort" if change == "held_count" else None
    with pytest.raises(ValueError, match=expected_message):
        v4._prepare(setup["draft_path"], setup["inventory"])


@pytest.mark.parametrize("case", ["invalid_icc", "large_clipping", "orientation"])
def test_profile_clipping_and_ambiguous_geometry_fail_closed(setup, case):
    path = setup["sources"] / setup["draft"]["records"][0]["image_path"]
    if case == "large_clipping":
        source, _, _ = sparse_profile_fixture(.1)
        source.save(path, format="PNG", icc_profile=source.info["icc_profile"])
    elif case == "invalid_icc":
        Image.new("RGB", (100, 100)).save(path, format="PNG", icc_profile=b"invalid")
    else:
        exif = Image.Exif(); exif[274] = 6
        Image.new("RGB", (100, 100)).save(path, format="PNG", exif=exif)
    with pytest.raises(ValueError): package(setup)
    assert not list(setup["output"].rglob("*.png"))
    assert not setup["output"].with_suffix(".zip").exists()


def test_no_silent_exclusion_or_completed_archive_after_later_failure(setup):
    path = setup["sources"] / setup["draft"]["records"][1]["image_path"]
    source, _, _ = sparse_profile_fixture(.1)
    source.save(path, format="PNG", icc_profile=source.info["icc_profile"])
    with pytest.raises(ValueError): package(setup)
    assert len(list(setup["output"].rglob("*.png"))) == 1
    assert not (setup["output"] / "bundle_manifest.json").exists()
    assert not setup["output"].with_suffix(".zip").exists()


@pytest.mark.parametrize("change", ["policy", "qa", "pixel", "metadata", "manifest", "extra_test"])
def test_postexport_tampering_and_metadata_rejected(setup, change):
    result = package(setup); bundle = read(setup, result)
    row = bundle["records"][0]
    if change == "policy": bundle["colour_policy_sha256"] = "0" * 64
    elif change == "qa": row["colour_measurements"]["forward_delta_e76_D50"]["mean"] = .6
    elif change == "manifest": bundle["notice"] = "altered"
    elif change == "extra_test":
        (setup["output"] / "Test").mkdir(); (setup["output"] / "Test/unexpected.txt").write_text("synthetic")
    else:
        path = setup["output"] / row["image_path"]
        with Image.open(path) as image: clean = Image.frombytes("RGB", image.size, image.tobytes())
        if change == "pixel": clean.putpixel((0, 0), (1, 2, 3))
        metadata = PngImagePlugin.PngInfo(); metadata.add(b"sRGB", b"\x01")
        if change == "metadata": metadata.add_text("private", "generated marker")
        clean.save(path, pnginfo=metadata)
        if change == "metadata":
            # Even a re-hashed payload must pass the actual chunk allowlist.
            row["image_payload_sha256"] = legacy.sha256(path)
            bundle["files"][row["image_path"]] = row["image_payload_sha256"]
            row["colour_receipt"]["verified_payloads"][row["image_path"]] = row["image_payload_sha256"]
            row["colour_evidence"] = v4._receipt_evidence(row["colour_measurements"], row["colour_receipt"])
    new_sha = rewrite(setup, bundle)
    with pytest.raises(ValueError): v4.validate_bundle(setup["output"], new_sha)
    if change != "extra_test":
        with pytest.raises(ValueError): v4.validate_bundle(setup["output"], result["bundle_manifest_sha256"])


def test_runtime_reference_failure_stops_before_any_source_decode(setup, monkeypatch):
    plan = prepare(setup)
    auth = authorization(v4.SCOPE, **v4.authorization_bindings(plan, setup["output"]))
    monkeypatch.setattr(v4, "_runtime_reference", lambda: (_ for _ in ()).throw(ValueError("runtime check")))
    monkeypatch.setattr(Image, "open", lambda *a, **k: pytest.fail("decoded before runtime qualification"))
    with pytest.raises(ValueError, match="runtime check"):
        v4.package_development(setup["draft_path"], setup["inventory"], setup["sources"], setup["output"], auth, True)


@pytest.mark.parametrize("change", ["source_hash", "geometry", "fake_flags"])
def test_pinned_source_checks_cannot_be_replaced_by_input_flags(setup, monkeypatch, change):
    plan = prepare(setup)
    if change == "source_hash":
        path = setup["sources"] / plan["records"][0]["image_path"]
        path.write_bytes(b"generated tampering")
    elif change == "geometry":
        inventory = json.loads(setup["inventory"].read_text())
        inventory["result"]["manifest"][0]["width"] = 99
        setup["inventory"].write_text(json.dumps(inventory, indent=2)+"\n")
        plan, _ = v4._prepare(setup["draft_path"], setup["inventory"])
    else:
        # An apparently passing external assertion cannot replace actual selection.
        setup["draft"]["records"][0]["cached_qa_requires_review"] = True
        setup["draft"]["checks"] = {key: True for key in policy.PREREQUISITES}
        setup["draft_path"].write_text(json.dumps(setup["draft"]))
        monkeypatch.setattr(legacy, "DRAFT_SHA", legacy.sha256(setup["draft_path"]))
    auth = authorization(v4.SCOPE, **v4.authorization_bindings(plan, setup["output"]))
    with pytest.raises(ValueError):
        v4.package_development(setup["draft_path"], setup["inventory"], setup["sources"],
                               setup["output"], auth, True)
    assert not list(setup["output"].rglob("*.png"))
    assert not setup["output"].with_suffix(".zip").exists()


def test_incorrect_colour_transform_is_measured_and_rejected(setup, monkeypatch):
    original = v4._managed
    def wrong(image):
        clean, conversion = original(image)
        clean.paste((255, 0, 0), (0, 0, *clean.size))
        return clean, conversion
    monkeypatch.setattr(v4, "_managed", wrong)
    with pytest.raises(ValueError, match="Option A colour rejection"):
        package(setup)
    assert not list(setup["output"].rglob("*.png"))


@pytest.mark.parametrize("change", ["protected_groups", "uncertain_groups", "simulated_qa", "post_source_hash", "old_code"])
def test_postexport_version_source_and_isolation_bindings(setup, change):
    result = package(setup); bundle = read(setup, result)
    row = bundle["records"][0]
    if change in {"protected_groups", "uncertain_groups"}: bundle[change] = []
    elif change == "simulated_qa": row["colour_measurements"]["output_mode"] = "simulated_srgb_in_memory"
    elif change == "post_source_hash": row["colour_receipt"]["source_after_export_sha256"] = "0"*64
    else: bundle["packaging_authorization"]["code_sha256"] = "0"*64
    row["colour_evidence"] = v4._receipt_evidence(row["colour_measurements"], row["colour_receipt"])
    with pytest.raises(ValueError):
        v4.validate_bundle(setup["output"], rewrite(setup, bundle))
