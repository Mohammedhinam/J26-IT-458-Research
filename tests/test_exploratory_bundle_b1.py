"""Generated-only gate integration. Authorization records are test doubles only."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import stat
import zipfile

import numpy as np
from PIL import Image
import pytest

from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_streaming as stream
from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_bundle_b1 as export


def row(identifier,grade,*,held=False,group=None):
    split,stem=identifier.split("/")
    return {"source_record_id":identifier,"original_split":split,"image_path":"Dataset/"+split+"/Images/"+stem+".jpg",
            "qualified_label_approved":False,"training_eligible":False,"mgi_grade":None,"participant_id":None,
            "analysis_split":None,"technical_candidate":not held,"draft_exclusion_reasons":["held"] if held else [],
            "content_group_id":group or "SYN_"+split+"_"+stem,"group_source_member_count":1,
            "group_original_split_presence":[split],"candidate_mgi_grade":grade,
            "cached_qa_requires_review":held,"original_cached_status":"needs_review" if held else "consistent",
            "cached_qa_issues":[],"cached_original_issues":[],
            "candidate_label_status":"strict_technically_consistent_unapproved","proposed_analysis_split":split}


def generated_inputs():
    # IDs/labels are synthetic gate fixtures; no actual DRAFT or dataset is read.
    records=[];recipes={}
    for split,count in legacy.EXPECTED_COUNTS.items():
        grades=[g for g,n in enumerate(legacy.EXPECTED_GRADES[split]) for _ in range(n)]
        ids=(["Training/"+str(10000+i) for i in range(count)] if split=="Training" else
             list(legacy.CAM_IDS)+["Validation/"+str(20000+i) for i in range(count-3)])
        for index,(identifier,grade) in enumerate(zip(ids,grades)):
            records.append(row(identifier,grade))
            width=index+1 if split=="Training" else index+1001
            recipes[identifier]={"width":width,"height":3 if identifier in legacy.CAM_IDS else 1,
                                 "pattern":"primaries","profile_kind":"wide_red"}
    for split,count,np_id in [("Training",52,legacy.NP015_IDS[0]),("Validation",129,legacy.NP015_IDS[1])]:
        records.append(row(np_id,None,held=True,group="SYN_NP015_"+split))
        records.extend(row(split+"/"+str((30000 if split=="Training" else 40000)+i),None,held=True)
                       for i in range(count-1))
    draft={"scope":export.GENERATED_SCOPE,"status":"draft_not_approved","activated":False,"training_ready":False,
           "mgi_schema":[0,1,2,3,4],"policy":{"optional_upper_partial_policy_activated":False},
           "approval":{k:False for k in ("labels_approved","split_approved","duplicate_review_complete","participant_independence_verified")},
           "sealed_boundary":{"protected_test_content_group_ids":["SYN_PROTECTED_TEST"],
                              "unresolved_NP015_group_ids":["SYN_NP015_Training","SYN_NP015_Validation"]},"records":records}
    return draft,recipes


def authorization(plan,output):
    # A unit-test double, not a signed or real data-use permission record.
    return {"status":"owner_confirmed","scope":export.SCOPE,"authorizer":"SYNTHETIC_TEST_ONLY",
            "date":"2026-10-15","evidence_reference":"generated-only authorization unit-test double",
            "acknowledgements":{key:True for key in legacy.ACKS},"data_scope":export.GENERATED_SCOPE,
            "real_packaging_authorized":False,**export.authorization_bindings(plan,output)}


@pytest.fixture(scope="module")
def prepared():
    draft,recipes=generated_inputs()
    return draft,recipes,export.prepare_generated_plan(draft,recipes)


@pytest.fixture(scope="module")
def successful(tmp_path_factory,prepared):
    draft,recipes,plan=prepared
    root=tmp_path_factory.mktemp("b1_generated_export").resolve()
    output=root/"generated_b1_complete"
    result=export.package_generated_b1(draft,plan,b1.digest_json(plan),output,authorization(plan,output),opt_in=True)
    return result


def test_complete733_export_and_independent_post_verification(successful,prepared):
    result=successful
    verified=export.validate_generated_package(result["directory"],result["manifest_sha256"],result["bindings"])
    assert verified=={"records":733,"files":1469,"scope":export.GENERATED_SCOPE}
    bundle=json.loads((Path(result["directory"])/"bundle_manifest.json").read_text())
    assert {split:sum(r["original_split"]==split for r in bundle["records"]) for split in legacy.EXPECTED_COUNTS}==legacy.EXPECTED_COUNTS
    assert len(bundle["plan"]["held_ids"])==181 and set(legacy.NP015_IDS)<=set(bundle["plan"]["held_ids"])
    assert len([name for name in bundle["files"] if name.endswith("/full_rgb.npy")])==3
    assert set(r["source_record_id"] for r in bundle["records"] if any(n.endswith("/full_rgb.npy") for n in r["files"]))==set(legacy.CAM_IDS)
    assert bundle["mgi_schema"]==[0,1,2,3,4] and not bundle["qualified_labels_approved"]
    assert bundle["attribution"]["licence"]=="CC BY 4.0" and "generated" in bundle["attribution"]["transformation_notice"].lower()
    # Actual NPY values remain extended; no display preview is used as model data.
    path=Path(result["directory"])/"records/Training/10000/model_rgb.npy"
    actual=np.load(path,allow_pickle=False)
    assert actual.min()<0 and actual.max()>1
    # Only safe aggregate numbers; records remain synthetic, never dental data.
    report={"records":verified["records"],"payload_files":verified["files"],
            "archive_bytes":Path(result["archive"]).stat().st_size,
            "archive_sha256":result["archive_sha256"],"manifest_sha256":result["manifest_sha256"],
            "counts":legacy.EXPECTED_COUNTS,"holds":181,"full_cam_count":3,
            "model_min":float(actual.min()),"model_max":float(actual.max()),
            "real_packaging_authorized":False}
    Path("/tmp/rp_b1_export_generated_summary_v1.json").write_text(json.dumps(report,indent=2))


@pytest.mark.parametrize("problem",["test","np015","protected","same_group","multi_group","needs_review",
                                   "activated","approval","grade0","missing_cam","holds","duplicate_id",
                                   "draft_metadata","row_metadata","real_scope"])
def test_selection_failures_before_source_pixels_or_output(prepared,monkeypatch,problem):
    draft,recipes,_=deepcopy(prepared)
    candidate=draft["records"][0]
    if problem=="test":candidate["original_split"]="Test"
    elif problem=="np015":candidate["source_record_id"]=legacy.NP015_IDS[0]
    elif problem=="protected":candidate["content_group_id"]="SYN_PROTECTED_TEST"
    elif problem=="same_group":draft["records"][1]["content_group_id"]=candidate["content_group_id"]
    elif problem=="multi_group":candidate["group_source_member_count"]=2
    elif problem=="needs_review":candidate["cached_qa_requires_review"]=True
    elif problem=="activated":draft["activated"]=True
    elif problem=="approval":draft["approval"]["labels_approved"]=True
    elif problem=="grade0":candidate["candidate_mgi_grade"]=0
    elif problem=="missing_cam":
        r=next(r for r in draft["records"] if r["source_record_id"]==legacy.CAM_IDS[0])
        r["technical_candidate"]=False;r["draft_exclusion_reasons"]=["held"]
    elif problem=="holds":draft["records"].pop()
    elif problem=="duplicate_id":draft["records"][-1]["source_record_id"]=draft["records"][-2]["source_record_id"]
    elif problem=="draft_metadata":draft["EXIF"]="forbidden"
    elif problem=="row_metadata":candidate["GPS"]="forbidden"
    else:draft["scope"]="real_data"
    monkeypatch.setattr(stream.GeneratedSource,"pixels",lambda *a:pytest.fail("Rejected DRAFT reached pixels"))
    with pytest.raises(ValueError):export.prepare_generated_plan(draft,recipes)


@pytest.mark.parametrize("problem",["extra_recipe","held_recipe","source_path","unsupported_profile","content_duplicate"])
def test_generated_source_plan_rejections(prepared,problem):
    draft,recipes,_=deepcopy(prepared)
    first=next(iter(recipes))
    if problem=="extra_recipe":recipes["Test/00001"]=recipes[first]
    elif problem=="held_recipe":recipes[legacy.NP015_IDS[0]]=recipes[first]
    elif problem=="source_path":recipes[first]["image_path"]="forbidden.jpg"
    elif problem=="unsupported_profile":recipes[first]["profile_kind"]="camera-profile"
    else:recipes[legacy.CAM_IDS[0]]=deepcopy(recipes[first])
    with pytest.raises(ValueError):export.prepare_generated_plan(draft,recipes)


@pytest.mark.parametrize("problem",["no_optin","wrong_scope","stale_code","stale_contract","wrong_plan",
                                   "wrong_id","real_permission","auth_metadata","missing_ack"])
def test_authorization_rejected_before_measurement_or_writes(tmp_path,prepared,monkeypatch,problem):
    draft,recipes,plan=prepared
    output=tmp_path.resolve()/"generated_b1_rejected"
    auth=authorization(plan,output)
    opt_in=True
    if problem=="no_optin":opt_in=False
    elif problem=="wrong_scope":auth["scope"]="package_development_option_a_v4"
    elif problem=="stale_code":auth["code_sha256"]="0"*64
    elif problem=="stale_contract":auth["colour_contract_sha256"]="0"*64
    elif problem=="wrong_plan":auth["source_plan_sha256"]="0"*64
    elif problem=="wrong_id":auth["bundle_id"]="generated_b1_old"
    elif problem=="real_permission":auth["real_packaging_authorized"]=True
    elif problem=="auth_metadata":auth["MakerNote"]="forbidden"
    else:auth["acknowledgements"][legacy.ACKS[0]]=False
    monkeypatch.setattr(export,"_measure_recipe",lambda *a:pytest.fail("Rejected authorization reached source"))
    with pytest.raises(ValueError):export.package_generated_b1(draft,plan,b1.digest_json(plan),output,auth,opt_in=opt_in)
    assert not output.exists() and not output.with_suffix(".zip").exists()


def test_failed_attempt_is_not_retried_or_promoted(tmp_path,prepared,monkeypatch):
    draft,_,plan=prepared
    output=tmp_path.resolve()/"generated_b1_injected_failure"
    auth=authorization(plan,output)
    def fail(*args):raise ValueError("injected conversion failure")
    monkeypatch.setattr(export,"_export_row",fail)
    with pytest.raises(ValueError,match="injected"):export.package_generated_b1(draft,plan,b1.digest_json(plan),output,auth,opt_in=True)
    assert not (output/"bundle_manifest.json").exists() and not (output/"COMPLETE.json").exists()
    assert not output.with_suffix(".zip").exists()
    with pytest.raises(ValueError,match="already used"):export.package_generated_b1(draft,plan,b1.digest_json(plan),output,auth,opt_in=True)


@pytest.mark.parametrize("problem",["payload_tamper","corrupt_npy","extra_file","extra_directory","receipt_metadata",
                                   "nested_metadata","manifest_tamper","missing_complete","archive_tamper"])
def test_complete_package_tampering_rejected_and_fixture_restored(successful,problem):
    root=Path(successful["directory"])
    target=root/"records/Training/10000/model_rgb.npy"
    if problem in {"receipt_metadata","nested_metadata"}:target=root/"records/Training/10000/source_receipt.json"
    elif problem=="manifest_tamper":target=root/"bundle_manifest.json"
    elif problem=="missing_complete":target=root/"COMPLETE.json"
    elif problem=="archive_tamper":target=Path(successful["archive"])
    original=target.read_bytes()
    extra=root/"unexpected.txt"
    empty=root/"Test"
    try:
        if problem=="payload_tamper":target.write_bytes(original[:-1]+bytes([original[-1]^1]))
        elif problem=="corrupt_npy":target.write_bytes(b"not a safe npy")
        elif problem=="extra_file":extra.write_text("extra")
        elif problem=="extra_directory":empty.mkdir()
        elif problem in {"receipt_metadata","nested_metadata"}:
            value=json.loads(original)
            if problem=="receipt_metadata":value["GPSInfo"]="forbidden"
            else:value["numeric"]["GPS"]="forbidden"
            target.write_text(json.dumps(value))
        elif problem=="manifest_tamper":target.write_bytes(original+b" ")
        elif problem=="missing_complete":target.unlink()
        else:target.write_bytes(original[:-1]+bytes([original[-1]^1]))
        with pytest.raises((ValueError,OSError)):
            export.validate_generated_package(root,successful["manifest_sha256"],successful["bindings"])
    finally:
        target.write_bytes(original)
        if extra.exists():extra.unlink()
        if empty.exists():empty.rmdir()


def test_no_real_decoder_or_legacy_export_and_preserved_guards(tmp_path,prepared,monkeypatch):
    from src.vision import exploratory_bundle_v4 as v4
    draft,_,plan=prepared
    def forbidden(*a,**kw):pytest.fail("Generated B1 called real-source/Option A path")
    monkeypatch.setattr(Image,"open",forbidden)
    monkeypatch.setattr(Image.Image,"save",forbidden)
    monkeypatch.setattr(legacy,"package_development",forbidden)
    monkeypatch.setattr(v4,"package_development",forbidden)
    old=v4.policy_spec()
    # Preflight genuinely generates/measures data but performs no decoder call.
    export._current_plan(draft,plan,b1.digest_json(plan))
    assert v4.policy_spec()==old and legacy.ROUNDTRIP_LIMIT==2
    with pytest.raises(ValueError):legacy.vp.approved_training_records({"status":"provisional_exploratory_only"})


def test_held_nested_metadata_is_rejected(prepared):
    draft,recipes,_=deepcopy(prepared)
    draft["records"][-1]["cached_original_issues"]=[{"GPS":"forbidden"}]
    with pytest.raises(ValueError,match="nested"):export.prepare_generated_plan(draft,recipes)


def test_actual_unsupported_icc_and_precision_fault_fail_before_output(prepared,monkeypatch):
    draft,recipes,_=prepared
    monkeypatch.setattr(stream.GeneratedSource,"profile",lambda self:b"malformed-generated-ICC")
    with pytest.raises(ValueError):export.prepare_generated_plan(draft,recipes)


def test_export_row_never_uses_a_real_decoder_or_fallback(tmp_path,prepared,monkeypatch):
    from src.vision import exploratory_bundle_v4 as v4
    def forbidden(*args,**kwargs):pytest.fail("Generated row reached decoder/fallback")
    monkeypatch.setattr(Image,"open",forbidden)
    monkeypatch.setattr(Image.Image,"save",forbidden)
    monkeypatch.setattr(v4,"package_development",forbidden)
    output=tmp_path/"generated";output.mkdir()
    work=tmp_path/"work";work.mkdir()
    item=export._export_row(prepared[2]["records"][0],work,output)
    assert item["label_status"]=="provisional" and item["participant_id"] is None


@pytest.mark.parametrize("problem",["corrupt_npy","nested_receipt_metadata"])
def test_intrinsic_verifier_rejects_rebound_hashes(successful,problem):
    root=Path(successful["directory"])
    bundle=json.loads((root/"bundle_manifest.json").read_text())
    row=bundle["records"][0]
    name=next(n for n in row["files"] if n.endswith("model_rgb.npy" if problem=="corrupt_npy" else "source_receipt.json"))
    path=root/name;original=path.read_bytes()
    try:
        if problem=="corrupt_npy":path.write_bytes(b"unsafe-npy")
        else:
            receipt=json.loads(original);receipt["numeric"]["GPS"]="forbidden"
            path.write_text(json.dumps(receipt));row["stream_receipt_sha256"]=b1.digest_json(receipt)
        digest=legacy.sha256(path);row["files"][name]=digest;bundle["files"][name]=digest
        with pytest.raises(ValueError):export._verify_contents(root,bundle,successful["bindings"])
    finally:path.write_bytes(original)


def test_final_publication_failure_is_not_a_valid_package(tmp_path,prepared,monkeypatch):
    draft,_,plan=prepared
    output=tmp_path.resolve()/"generated_b1_publish_failure"
    auth=authorization(plan,output)
    def fail_link(*args):raise OSError("injected publication failure")
    monkeypatch.setattr(export.os,"link",fail_link)
    with pytest.raises(OSError,match="publication"):
        export.package_generated_b1(draft,plan,b1.digest_json(plan),output,auth,opt_in=True)
    assert not output.with_suffix(".zip").exists() and output.with_suffix(".zip.partial").exists()
    manifest=legacy.sha256(output/"bundle_manifest.json")
    with pytest.raises((ValueError,OSError)):
        export.validate_generated_package(output,manifest,export.authorization_bindings(plan,output))
    with pytest.raises(ValueError,match="already used"):
        export.package_generated_b1(draft,plan,b1.digest_json(plan),output,auth,opt_in=True)


def test_archive_rejects_link_metadata_even_with_identical_payloads(tmp_path,successful):
    root=Path(successful["directory"])
    bundle=json.loads((root/"bundle_manifest.json").read_text())
    target=tmp_path/"unsafe-generated.zip"
    with zipfile.ZipFile(successful["archive"]) as original,zipfile.ZipFile(target,"x") as altered:
        for index,entry in enumerate(original.infolist()):
            if index==0:entry.external_attr=(stat.S_IFLNK|0o777)<<16
            altered.writestr(entry,original.read(entry))
    with pytest.raises(ValueError,match="ZIP type"):
        export._verify_archive(target,bundle["files"],successful["manifest_sha256"],root)
