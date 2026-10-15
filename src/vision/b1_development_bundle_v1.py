"""Separate B1 local development pathway; explicit bound owner opt-in required.

No Option A fallback, approval promotion, training, upload or automatic retry.
"""
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import resource
import shutil
import zipfile

import numpy as np

from src.vision import b1_jpeg_source_v1 as source
from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_streaming as stream
from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_bundle_v4 as frozen


VERSION = "pp1-b1-real-development-v1"
SCOPE = "package_local_development_b1_v1"
ATTRIBUTION = deepcopy(legacy.DATASET_ATTRIBUTION)
ATTRIBUTION["transformation_notice"] = (
    "Local provisional development derivatives: ICCv2 matrix/TRC to unclipped extended "
    "encoded-sRGB float32 NPY; metadata removed; deterministic bilinear224 letterbox; "
    "three full-resolution CAM arrays. Display-only sRGB previews may clip. "
    "Originals and provisional caption maximum grades unchanged. No clinical validation "
    "or licensor endorsement. No cloud/training/final-research approval.")


def contract():
    return {"version": VERSION, "source_contract": source.CONTRACT,
            "counts": legacy.EXPECTED_COUNTS, "held": 181, "cam_ids": list(legacy.CAM_IDS),
            "research_schema": [0,1,2,3,4], "exploratory_schema": [1,2,3,4],
            "privacy": "NPY_and_allowlisted_JSON_no_source_metadata",
            "qualified_labels_approved": False, "participant_independence_verified": False,
            "final_research_approved": False}


def code_hashes():
    directory = Path(__file__).parent
    names = ["b1_development_bundle_v1.py", "b1_jpeg_source_v1.py", "colour_b1_iccv2_generated.py",
             "colour_b1_prototype.py", "colour_b1_streaming.py", "colour_qa.py", "colour_policy.py",
             "exploratory_bundle.py", "exploratory_bundle_v4.py", "model_pipeline.py", "train_pipeline.py"]
    return {n: legacy.sha256(directory/n) for n in names}


def validate_plan(plan):
    if (type(plan) is not dict or not {"records","protected_groups","uncertain_groups",
                                      "cam_ids","source_draft_sha256"} <= plan.keys()):
        raise ValueError("Missing/malformed pinned source plan")
    legacy.validate_source_plan(plan)
    legacy.fixed_cohort(plan["records"])
    if (plan["source_draft_sha256"] != legacy.DRAFT_SHA
            or frozen._identity(plan["records"]) != legacy.CANDIDATE_IDENTITY_SHA
            or plan["cam_ids"] != list(legacy.CAM_IDS)):
        raise ValueError("Pinned DRAFT/cohort/CAM identity mismatch")


def prepare(draft, inventory):
    plan, held = frozen._prepare(draft, inventory)
    validate_plan(plan)
    if held != 181:
        raise ValueError("All181 holds must remain excluded")
    return plan


def preflight(plan, root, progress=None):
    """Current hashes/headers plus exhaustive generated-code numerical proof."""
    validate_plan(plan)
    evidence, profiles = [], {}
    for index, row in enumerate(plan["records"]):
        path = legacy.safe_file(root, row["image_path"])
        with stream._open(path) as handle:
            before = source.identity(handle)
            digest = sha256()
            for block in iter(lambda: handle.read(1024*1024), b""):
                digest.update(block)
            if digest.hexdigest() != row["source_sha256"]:
                raise ValueError("Source SHA mismatch: "+row["source_record_id"])
            image, profile = source.checked_header(handle, row["source_dimensions"])
            if source.identity(handle) != before:
                raise ValueError("Source changed during header preflight")
            image.close()
        profile_hash = sha256(profile).hexdigest()
        profiles[profile_hash] = profile
        evidence.append({"source_record_id": row["source_record_id"],
                         "source_sha256": digest.hexdigest(), "source_identity": before,
                         "profile_sha256": profile_hash, "dimensions": row["source_dimensions"]})
        if progress and index % 50 == 0:
            progress({"source_headers_checked": index+1, "total": len(plan["records"])})
    qualification = {h: source.qualify_profile(p, progress) for h,p in profiles.items()}
    return {"version": VERSION, "contract_sha256": b1.digest_json(contract()),
            "code_sha256": b1.digest_json(code_hashes()),
            "source_plan_sha256": legacy.json_digest(plan), "records": evidence,
            "profile_qualification": qualification, "status": "PASS",
            "rgb_photographs_decoded": 0, "real_packaging_started": False}


def bindings(plan, preflight_record, output, owner_text_sha256):
    return {"export_version": VERSION, "bundle_id": Path(output).name,
            "output_path_sha256": sha256(str(Path(output).resolve()).encode()).hexdigest(),
            "source_draft_sha256": legacy.DRAFT_SHA,
            "source_plan_sha256": legacy.json_digest(plan),
            "preflight_sha256": b1.digest_json(preflight_record),
            "contract_sha256": b1.digest_json(contract()),
            "code_sha256": b1.digest_json(code_hashes()), "owner_text_sha256": owner_text_sha256}


def require_preflight(plan, evidence):
    validate_plan(plan)
    if (evidence.get("version") != VERSION or evidence.get("status") != "PASS"
            or evidence.get("contract_sha256") != b1.digest_json(contract())
            or evidence.get("code_sha256") != b1.digest_json(code_hashes())
            or evidence.get("source_plan_sha256") != legacy.json_digest(plan)
            or len(evidence.get("records", [])) != 733):
        raise ValueError("Missing/stale/unsafe real B1 preflight")
    expected = {r["source_record_id"]: r for r in plan["records"]}
    actual = {r["source_record_id"]: r for r in evidence["records"]}
    if len(actual) != 733 or actual.keys() != expected.keys():
        raise ValueError("Preflight exact membership mismatch")
    for identifier, record in actual.items():
        if (record["source_sha256"] != expected[identifier]["source_sha256"]
                or record["dimensions"] != expected[identifier]["source_dimensions"]):
            raise ValueError("Preflight source binding mismatch")
        check_qualification(evidence["profile_qualification"].get(record["profile_sha256"], {}),record["profile_sha256"])


def check_qualification(q, profile_hash):
    fields={"profile_sha256","codes_checked","xyz_max_abs","lab_max_delta_e76",
            "lcms_lab_delta_e76","minimum","maximum"}
    if (type(q) is not dict or set(q)!=fields or q["profile_sha256"]!=profile_hash
            or q["codes_checked"]!=256**3
            or any(type(q[k]) not in (int,float) or not math.isfinite(q[k]) or not 0<=q[k]<=limit
                   for k,limit in (("xyz_max_abs",2e-6),("lab_max_delta_e76",.002),("lcms_lab_delta_e76",.01)))
            or any(type(q[k]) not in (int,float) or not math.isfinite(q[k]) for k in ("minimum","maximum"))
            or not -16<=q["minimum"]<=q["maximum"]<=16):
        raise ValueError("Incomplete/unsafe B1 profile-domain qualification")


def write_json(path, value):
    with stream._open(path, write=True) as handle:
        handle.write((json.dumps(value, indent=2, allow_nan=False)+"\n").encode())


def load_json(path, maximum=8*1024**2):
    with stream._open(path) as handle:
        if handle.seek(0,2)>maximum:
            raise ValueError("Oversized JSON")
        handle.seek(0)
        return json.loads(handle.read(), object_pairs_hook=stream._unique_json_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))


def inspect_array(path, dimensions):
    with stream._open(path) as handle:
        evidence, offset, identity = stream._inspect(handle, (dimensions[1],dimensions[0],3))
    return evidence


def model_array(path, expected_sha):
    with stream._open(path) as handle:
        evidence, offset, identity = stream._inspect(handle, (224,224,3))
        if evidence["sha256"] != expected_sha:
            raise ValueError("Model payload hash mismatch")
        handle.seek(offset)
        values = np.frombuffer(handle.read(224*224*12), dtype="<f4").reshape(224,224,3).copy()
        if stream._identity(handle) != identity:
            raise ValueError("Model payload identity changed")
    return b1._array(values)


RECORD_KEYS = {"source_record_id","original_image_path","original_split","content_group_id",
               "provisional_mgi_grade","label_status","qualified_label_approved","source_sha256",
               "profile_sha256","source_dimensions","valid_box","model_path","model_sha256",
               "cam_path","cam_sha256"}
MANIFEST_KEYS = {"version","notice","contract","bindings","research_mgi_schema","pilot_mgi_schema",
                 "qualified_labels_approved","participant_independence_verified","final_research_approved",
                 "held_count","np015_excluded","protected_groups","uncertain_groups","records",
                 "profile_qualification","dataset_attribution","status"}


def validate_manifest(manifest):
    if (type(manifest) is not dict or set(manifest)!=MANIFEST_KEYS
            or manifest["version"] != VERSION or manifest["notice"] != legacy.NOTICE
            or manifest["contract"] != contract() or manifest["research_mgi_schema"] != [0,1,2,3,4]
            or manifest["pilot_mgi_schema"] != [1,2,3,4]
            or any(manifest[k] is not False for k in
                   ("qualified_labels_approved","participant_independence_verified","final_research_approved"))
            or manifest["held_count"]!=181 or manifest["np015_excluded"]!=list(legacy.NP015_IDS)
            or manifest["dataset_attribution"] != ATTRIBUTION or manifest["status"]!="provisional_exploratory_only"):
        raise ValueError("Not an approved-version provisional B1 development bundle")
    bound=manifest["bindings"]
    binding_keys={"export_version","bundle_id","output_path_sha256","source_draft_sha256","source_plan_sha256",
                  "preflight_sha256","contract_sha256","code_sha256","owner_text_sha256"}
    if (type(bound) is not dict or set(bound)!=binding_keys or bound["export_version"]!=VERSION
            or bound["source_draft_sha256"]!=legacy.DRAFT_SHA
            or bound["contract_sha256"]!=b1.digest_json(contract())
            or bound["code_sha256"]!=b1.digest_json(code_hashes())
            or any(not b1._sha(bound[k]) for k in binding_keys if k.endswith("sha256"))):
        raise ValueError("Stale/unsafe package bindings")
    rows = manifest["records"]
    if len(rows)!=733:
        raise ValueError("Exact733 B1 records required")
    identities, paths, groups, projected = set(), set(), set(), []
    blocked = set(manifest["protected_groups"]+manifest["uncertain_groups"])
    expected_files = {"bundle_manifest.json"}
    for row in rows:
        if type(row) is not dict or set(row)!=RECORD_KEYS or row["original_split"] not in legacy.EXPECTED_COUNTS:
            raise ValueError("Unexpected/Test B1 source row")
        identifier = row["source_record_id"]
        if (identifier in identities or identifier in legacy.NP015_IDS
                or row["content_group_id"] in groups|blocked
                or identifier != row["original_split"]+"/"+Path(row["original_image_path"]).stem
                or row["label_status"]!="provisional" or row["qualified_label_approved"] is not False
                or type(row["provisional_mgi_grade"]) is not int or row["provisional_mgi_grade"] not in [1,2,3,4]
                or row["valid_box"]!=stream.full_geometry(*row["source_dimensions"])):
            raise ValueError("Held/overlapping/invalid B1 row")
        legacy.relative_path(row["original_image_path"])
        for key in ("source_sha256","profile_sha256","model_sha256"):
            if not b1._sha(row[key]): raise ValueError("Missing SHA binding")
        check_qualification(manifest["profile_qualification"].get(row["profile_sha256"],{}),row["profile_sha256"])
        if row["model_path"]!="model/"+identifier+".npy":
            raise ValueError("Model path/split mismatch")
        if identifier in legacy.CAM_IDS:
            if row["cam_path"]!="cam/"+identifier+".npy" or not b1._sha(row["cam_sha256"]):
                raise ValueError("Fixed CAM binding mismatch")
            expected_files.add(row["cam_path"])
        elif row["cam_path"] is not None or row["cam_sha256"] is not None:
            raise ValueError("Unapproved full-resolution CAM")
        expected_files.add(row["model_path"])
        identities.add(identifier);groups.add(row["content_group_id"])
        if row["source_sha256"] in paths: raise ValueError("Duplicate source content")
        paths.add(row["source_sha256"])
        projected.append({"source_record_id":identifier,"image_path":row["original_image_path"],
                          "original_split":row["original_split"],"candidate_mgi_grade":row["provisional_mgi_grade"],
                          "content_group_id":row["content_group_id"]})
    legacy.fixed_cohort(projected)
    if frozen._identity(projected)!=legacy.CANDIDATE_IDENTITY_SHA:
        raise ValueError("Fixed candidate identity changed")
    return rows, expected_files


def verify(root, trusted_manifest_sha256):
    root = Path(root)
    path = legacy.safe_file(root,"bundle_manifest.json")
    if not b1._sha(trusted_manifest_sha256) or legacy.sha256(path)!=trusted_manifest_sha256:
        raise ValueError("Untrusted manifest SHA")
    manifest = load_json(path)
    rows, expected = validate_manifest(manifest)
    actual = set()
    allowed_directories = {str(Path(n).parent) for n in expected}
    allowed_directories |= {"model","cam","."}
    for p in root.rglob("*"):
        if p.is_symlink(): raise ValueError("Symlink payload")
        name = p.relative_to(root).as_posix()
        if p.is_file(): actual.add(name)
        elif not p.is_dir() or name not in allowed_directories:
            raise ValueError("Unexpected directory/nonregular payload")
    if actual!=expected:
        raise ValueError("Extra/missing package entries")
    for row in rows:
        values = model_array(legacy.safe_file(root,row["model_path"]),row["model_sha256"])
        if row["cam_path"]:
            path = legacy.safe_file(root,row["cam_path"])
            evidence = inspect_array(path,row["source_dimensions"])
            if evidence["sha256"]!=row["cam_sha256"]:
                raise ValueError("CAM hash mismatch")
            with stream._open(path) as handle:
                _,offset,identity=stream._inspect(handle,(row["source_dimensions"][1],row["source_dimensions"][0],3))
                sampled=stream._model_view(handle,offset,*row["source_dimensions"],identity)
            if not np.array_equal(sampled,values):
                raise ValueError("Full CAM/model alignment/content mismatch")
    return {"status":"PASS","records":len(rows),"model_arrays":733,"full_cam_arrays":3,
            "files":len(expected),"manifest_sha256":trusted_manifest_sha256}


def package(plan, root, evidence, output, authorization, opt_in=False, progress=None):
    require_preflight(plan,evidence)
    output=legacy.new_ignored_output(output,"data/vision")
    expected=bindings(plan,evidence,output,authorization.get("owner_text_sha256"))
    legacy.authorise(authorization,SCOPE,expected,opt_in)
    if (authorization.get("local_only") is not True or authorization.get("maximum_attempts")!=1
            or authorization.get("cloud_authorized") is not False or authorization.get("training_authorized") is not False
            or not b1._sha(authorization.get("owner_text_sha256"))):
        raise ValueError("Separate one-attempt local-only B1 owner scope required")
    marker=output.parent/("."+output.name+".attempt.json")
    archive=output.with_suffix(".zip")
    for p in (output,marker,archive,archive.with_suffix(".zip.partial")):
        if p.exists() or p.is_symlink(): raise ValueError("Fresh never-used output/attempt ID required")
    if shutil.disk_usage(output.parent).free < 5*1024**3:
        raise ValueError("Insufficient conservative5GiB free disk reserve")
    write_json(marker,{"status":"consumed","bindings":expected})
    output.mkdir(mode=0o700)
    checked={r["source_record_id"]:r for r in evidence["records"]}
    records=[];converters={}
    for index,row in enumerate(plan["records"]):
        prior=checked[row["source_record_id"]]
        path=legacy.safe_file(root,row["image_path"])
        with stream._open(path) as handle:
            if source.identity(handle)!=prior["source_identity"]:
                raise ValueError("Source identity changed after preflight")
            image,profile=source.checked_header(handle,row["source_dimensions"]);image.close()
        h=sha256(profile).hexdigest()
        if h!=prior["profile_sha256"]: raise ValueError("ICC changed after preflight")
        converter=converters.setdefault(h,source.Converter(profile))
        identifier=row["source_record_id"]
        model_path="model/"+identifier+".npy"
        cam_path="cam/"+identifier+".npy" if identifier in legacy.CAM_IDS else None
        (output/model_path).parent.mkdir(parents=True,exist_ok=True)
        with source.decoded(path,row["source_sha256"],row["source_dimensions"],h) as image:
            values=source.model_view(image,converter)
            with stream._open(output/model_path,write=True) as target:
                np.lib.format.write_array(target,values,version=(1,0),allow_pickle=False)
            model_sha=legacy.sha256(output/model_path)
            np.testing.assert_array_equal(model_array(output/model_path,model_sha),values)
            cam_sha=None
            if cam_path:
                (output/cam_path).parent.mkdir(parents=True,exist_ok=True)
                source.write_full_cam(image,converter,output/cam_path)
                cam_sha=inspect_array(output/cam_path,row["source_dimensions"])["sha256"]
        records.append({"source_record_id":identifier,"original_image_path":row["image_path"],
                        "original_split":row["original_split"],"content_group_id":row["content_group_id"],
                        "provisional_mgi_grade":row["candidate_mgi_grade"],"label_status":"provisional",
                        "qualified_label_approved":False,"source_sha256":row["source_sha256"],
                        "profile_sha256":h,"source_dimensions":row["source_dimensions"],
                        "valid_box":stream.full_geometry(*row["source_dimensions"]),"model_path":model_path,
                        "model_sha256":model_sha,"cam_path":cam_path,"cam_sha256":cam_sha})
        if progress and (index%20==0 or index+1==733):
            progress({"images_exported":index+1,"total":733})
    # Rehash originals after conversion; never assume successful reads prove preservation.
    for row in plan["records"]:
        if legacy.sha256(legacy.safe_file(root,row["image_path"]))!=row["source_sha256"]:
            raise ValueError("Source changed after packaging")
    manifest={"version":VERSION,"notice":legacy.NOTICE,"contract":contract(),"bindings":expected,
              "research_mgi_schema":[0,1,2,3,4],"pilot_mgi_schema":[1,2,3,4],
              "qualified_labels_approved":False,"participant_independence_verified":False,
              "final_research_approved":False,"held_count":181,"np015_excluded":list(legacy.NP015_IDS),
              "protected_groups":plan["protected_groups"],"uncertain_groups":plan["uncertain_groups"],
              "records":records,"profile_qualification":evidence["profile_qualification"],
              "dataset_attribution":ATTRIBUTION,"status":"provisional_exploratory_only"}
    write_json(output/"bundle_manifest.json",manifest)
    trusted=legacy.sha256(output/"bundle_manifest.json")
    verified=verify(output,trusted)
    return {"directory":str(output),"manifest_sha256":trusted,"verification":verified,
            "archive_pending_independent_verification":True,"peak_rss_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def publish_zip(root, trusted_manifest_sha256):
    """Only call after separate-process verification; never overwrite a ZIP."""
    root=Path(root)
    verify(root,trusted_manifest_sha256)
    archive=root.with_suffix(".zip");partial=root.with_suffix(".zip.partial")
    if archive.exists() or partial.exists(): raise ValueError("Archive already used")
    manifest=load_json(root/"bundle_manifest.json")
    _,names=validate_manifest(manifest)
    with zipfile.ZipFile(partial,"x",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as zipped:
        for name in sorted(names):
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100600<<16
            with stream._open(legacy.safe_file(root,name)) as src,zipped.open(info,"w",force_zip64=True) as dst:
                shutil.copyfileobj(src,dst,1024*1024)
    with zipfile.ZipFile(partial) as zipped:
        if set(zipped.namelist())!=names or len(zipped.namelist())!=len(names):
            raise ValueError("Archive exact membership mismatch")
        for name in names:
            digest=sha256()
            with zipped.open(name) as src:
                for block in iter(lambda:src.read(1024*1024),b""):digest.update(block)
            if digest.hexdigest()!=legacy.sha256(root/name):
                raise ValueError("Archive payload hash/CRC mismatch")
    partial.rename(archive)
    return {"archive":str(archive),"bytes":archive.stat().st_size,"sha256":legacy.sha256(archive)}
