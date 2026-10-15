"""Explicit GENERATED-ONLY B1 packaging integration; no real input adapter.

The owner must separately authorise real-source compatibility and real use.
This API accepts generated recipes only; it never reads a dataset or ICC file.
"""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import shutil
import stat
import zipfile

from src.vision import colour_b1_prototype as b1
from src.vision import colour_b1_streaming as stream
from src.vision import exploratory_bundle as legacy


VERSION = "pp1-b1-generated-export-v1"
SCOPE = "package_generated_development_b1_v1"
GENERATED_SCOPE = "generated_only_not_production"
DATASET_ATTRIBUTION = {k:deepcopy(v) for k,v in legacy.DATASET_ATTRIBUTION.items()
                       if k != "transformation_notice"}
DATASET_ATTRIBUTION["transformation_notice"] = (
    "Generated-only engineering fixtures, not exported Mendeley photographs. "
    "Future dataset use must retain this source attribution. B1 interprets supported "
    "matrix/TRC colour into unclipped extended encoded-sRGB float32 NPY, removes source "
    "metadata and uses deterministic bilinear letterbox. Only three fixed full-size "
    "CAM arrays retained. Display previews may clip; no clinical colour validation.")
MAX_JSON = 4 * 1024**2
DRAFT_KEYS={"scope","status","activated","training_ready","mgi_schema","policy","approval","sealed_boundary","records"}
ROW_KEYS={"source_record_id","original_split","image_path","qualified_label_approved","training_eligible",
          "mgi_grade","participant_id","analysis_split","technical_candidate","draft_exclusion_reasons",
          "content_group_id","group_source_member_count","group_original_split_presence","candidate_mgi_grade",
          "cached_qa_requires_review","original_cached_status","cached_qa_issues","cached_original_issues",
          "candidate_label_status","proposed_analysis_split"}


def contract_spec():
    return {"version":VERSION,"scope":GENERATED_SCOPE,"base":b1.contract_hash(),
            "streaming":b1.digest_json(stream.CONTRACT),"counts":legacy.EXPECTED_COUNTS,
            "holds":181,"cam_ids":list(legacy.CAM_IDS),"mgi_schema":[0,1,2,3,4],
            "pilot":"supported_grades_1_to_4_exploration_only_no_model_change",
            "real_source_enabled":False,"research_training_gate_changed":False}


def source_code_hashes():
    directory=Path(__file__).parent
    names=("exploratory_bundle_b1.py","colour_b1_streaming.py","colour_b1_prototype.py",
           "model_pipeline.py","train_pipeline.py","exploratory_bundle.py",
           "exploratory_bundle_v4.py","exploratory_pilot.py","gamut_mapping_feasibility.py",
           "colour_qa.py","colour_policy.py")
    return {name:legacy.sha256(directory/name) for name in names}


def _select(draft):
    if type(draft) is not dict or set(draft)!=DRAFT_KEYS or draft.get("scope") != GENERATED_SCOPE:
        raise ValueError("Explicit generated-only DRAFT required; no real DRAFT accepted")
    if (set(draft["policy"])!={"optional_upper_partial_policy_activated"}
            or set(draft["approval"])!={"labels_approved","split_approved","duplicate_review_complete","participant_independence_verified"}
            or set(draft["sealed_boundary"])!={"protected_test_content_group_ids","unresolved_NP015_group_ids"}):
        raise ValueError("Unexpected private/extra DRAFT evidence fields")
    for row in draft["records"]:
        if type(row) is not dict or set(row)!=ROW_KEYS:
            raise ValueError("Unexpected private/extra DRAFT row fields")
        if row["original_split"] not in legacy.EXPECTED_COUNTS:
            raise ValueError("Test/nondevelopment DRAFT row forbidden before labels")
        if (not isinstance(row["content_group_id"],str)
                or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}",row["content_group_id"])
                or type(row["draft_exclusion_reasons"]) is not list
                or any(type(reason) is not str or reason not in {"held","needs_review","NP015_uncertain","protected_group","duplicate"}
                       for reason in row["draft_exclusion_reasons"])):
            raise ValueError("Unsupported generated group/exclusion provenance")
        if (row["cached_qa_issues"]!=[] or row["cached_original_issues"]!=[]
                or row["original_cached_status"] not in {"consistent","needs_review"}
                or row["candidate_label_status"]!="strict_technically_consistent_unapproved"
                or type(row["group_source_member_count"]) is not int or not 1<=row["group_source_member_count"]<=100
                or type(row["group_original_split_presence"]) is not list
                or not 1<=len(row["group_original_split_presence"])<=3
                or any(type(s) is not str or s not in {"Training","Validation","Test"} for s in row["group_original_split_presence"])
                or type(row["technical_candidate"]) is not bool or type(row["cached_qa_requires_review"]) is not bool):
            raise ValueError("Unexpected nested generated annotation metadata")
        if not row["technical_candidate"] and (row["candidate_mgi_grade"] is not None
                or row["proposed_analysis_split"] not in (None,row["original_split"])):
            raise ValueError("Held records cannot carry approved/candidate grades")
    selected=legacy.select_candidates(draft)
    legacy.fixed_cohort(selected)
    records=draft["records"]
    if (len(records)!=914 or len(records)-len(selected)!=181
            or len({r["source_record_id"] for r in records})!=914):
        raise ValueError("Exact914 records/181 holds required")
    held={r["source_record_id"]:r for r in records if r["technical_candidate"] is not True}
    if not set(legacy.NP015_IDS) <= held.keys():
        raise ValueError("Both unresolved NP015 records must remain held")
    boundary=draft["sealed_boundary"]
    if (not boundary["protected_test_content_group_ids"]
            or not boundary["unresolved_NP015_group_ids"]
            or not {held[i]["content_group_id"] for i in legacy.NP015_IDS}
               <= set(boundary["unresolved_NP015_group_ids"])):
        raise ValueError("Protected/uncertain group boundary missing")
    for row in records:
        if row["source_record_id"] != row["original_split"]+"/"+Path(row["image_path"]).stem:
            raise ValueError("Source identifier mismatch")
    return sorted(selected,key=lambda r:r["source_record_id"])


def _recipe(value):
    if type(value) is not dict or set(value)!={"width","height","pattern","profile_kind"}:
        raise ValueError("Generated recipe only; no source paths/ICC bytes/extra metadata")
    return stream.GeneratedSource(**value)


def _measure_recipe(value):
    source=_recipe(value)
    profile=source.profile()
    source_hash=sha256()
    numeric={"xyz_max_abs":0.,"lab_max_delta_e76":0.}
    for offset,count,shape in stream._chunks(source.width*source.height):
        pixels=source.pixels(offset,count).reshape(shape)
        values,measured=b1.convert_generated(pixels,profile)
        b1._array(values)
        source_hash.update(pixels.tobytes(order="C"))
        for name in numeric:numeric[name]=max(numeric[name],measured[name])
    return {"source_rgb_sha256":source_hash.hexdigest(),"profile_sha256":sha256(profile).hexdigest(),
            "numeric":numeric,"source_size_wh":[source.width,source.height]}


def prepare_generated_plan(draft,recipes):
    """Derive actual generated source checks, not caller-provided pass booleans."""
    selected=_select(draft)
    if type(recipes) is not dict or set(recipes)!={r["source_record_id"] for r in selected}:
        raise ValueError("Exact733 selected recipes required; no held/Test extras")
    rows=[]
    content_splits={}
    for row in selected:
        identifier=row["source_record_id"]
        measured=_measure_recipe(recipes[identifier])
        content_key=(*measured["source_size_wh"],measured["source_rgb_sha256"])
        if content_key in content_splits:
            raise ValueError("Duplicate generated source content, including cross-split collision")
        content_splits[content_key]=row["original_split"]
        rows.append({"source_record_id":identifier,"original_split":row["original_split"],
                     "content_group_id":row["content_group_id"],
                     "provisional_mgi_grade":row["candidate_mgi_grade"],
                     "generated_recipe":deepcopy(recipes[identifier]),
                     "checked_source":measured})
    return {"version":VERSION,"scope":GENERATED_SCOPE,"draft_sha256":b1.digest_json(draft),
            "records":rows,"held_ids":sorted(r["source_record_id"] for r in draft["records"]
                                              if r["technical_candidate"] is not True),
            "protected_groups":deepcopy(draft["sealed_boundary"]),"cam_ids":list(legacy.CAM_IDS)}


def authorization_bindings(plan,output):
    output=Path(output)
    if not re.fullmatch(r"generated_b1_[A-Za-z0-9_-]{1,64}",output.name):
        raise ValueError("Fresh explicit generated B1 output ID required")
    return {"export_version":VERSION,"bundle_id":output.name,"output_path":str(output.resolve()),
            "source_plan_sha256":b1.digest_json(plan),"source_draft_sha256":plan["draft_sha256"],
            "code_sha256":b1.digest_json(source_code_hashes()),
            "colour_contract_sha256":b1.digest_json(contract_spec())}


def _authorize(authorization,bindings,opt_in):
    legacy.authorise(authorization,SCOPE,bindings,opt_in)
    fields={"status","scope","authorizer","date","evidence_reference","acknowledgements",
            "data_scope","real_packaging_authorized"}|set(bindings)
    if (authorization.get("data_scope")!=GENERATED_SCOPE
            or authorization.get("real_packaging_authorized") is not False
            or set(authorization)!=fields or set(authorization["acknowledgements"])!=set(legacy.ACKS)):
        raise ValueError("Separate B1 generated-only authorization required")


def _current_plan(draft,plan,trusted_plan_sha256):
    if (not b1._sha(trusted_plan_sha256) or b1.digest_json(plan)!=trusted_plan_sha256
            or plan.get("version")!=VERSION or plan.get("scope")!=GENERATED_SCOPE
            or plan.get("cam_ids")!=list(legacy.CAM_IDS)):
        raise ValueError("Untrusted/stale/non-B1 generated plan")
    recipes={r["source_record_id"]:r["generated_recipe"] for r in plan["records"]}
    rebuilt=prepare_generated_plan(draft,recipes)
    if rebuilt!=plan:
        raise ValueError("Generated plan/current source measurements differ")


def _fresh_output(output):
    output=Path(output)
    parent=output.parent
    if not parent.is_dir() or any(p.is_symlink() for p in [parent,*parent.parents]):
        raise ValueError("Canonical existing scratch parent without symlinks required")
    marker=parent/("."+output.name+".attempt.json")
    for path in (output,output.with_suffix(".zip"),output.with_suffix(".zip.partial"),marker):
        if path.exists() or path.is_symlink():
            raise ValueError("Output/attempt ID already used; no automatic retry")
    return marker


def _copy_payload(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    with stream._open(source) as original,stream._open(destination,write=True) as target:
        shutil.copyfileobj(original,target,1024*1024)
    return legacy.sha256(destination)


def _export_row(row,work,output):
    identifier=row["source_record_id"]
    source=_recipe(row["generated_recipe"])
    stage=work/identifier.replace("/","_")
    result=stream.convert_generated_full(source,stage)
    verified=stream.verify_generated_outputs(stage,result["receipt_sha256"])
    receipt=verified["receipt"]
    expected=row["checked_source"]
    if (receipt["source_rgb_sha256"]!=expected["source_rgb_sha256"]
            or receipt["profile_sha256"]!=expected["profile_sha256"]
            or any(receipt["numeric"][k]!=expected["numeric"][k] for k in expected["numeric"])):
        raise ValueError("Actual B1 conversion differs from preflight")
    files={}
    prefix="records/"+identifier+"/"
    for source_name,target_name in (("model_rgb.npy","model_rgb.npy"),("receipt.json","source_receipt.json")):
        name=prefix+target_name
        files[name]=_copy_payload(stage/source_name,output/name)
    if identifier in legacy.CAM_IDS:
        name=prefix+"full_rgb.npy"
        files[name]=_copy_payload(stage/"full_rgb.npy",output/name)
    shutil.rmtree(stage)  # Only this row's freshly generated temporary data.
    return {**deepcopy(row),"label_status":"provisional","qualified_label_approved":False,
            "participant_id":None,"stream_receipt_sha256":result["receipt_sha256"],"files":files}


def _json_file(path):
    with stream._open(path) as source:
        if source.seek(0,2)>MAX_JSON:raise ValueError("Oversized generated JSON")
        source.seek(0)
        return json.loads(source.read(),object_pairs_hook=stream._unique_json_pairs)


def _payload_members(root):
    names=set()
    directories=set()
    for path in root.rglob("*"):
        if path.is_symlink():raise ValueError("Symlink in generated package")
        if path.is_file():names.add(path.relative_to(root).as_posix())
        elif path.is_dir():directories.add(path.relative_to(root).as_posix())
        else:raise ValueError("Nonregular generated package entry")
    allowed={parent.as_posix() for name in names for parent in Path(name).parents if parent.as_posix()!="."}
    if directories!=allowed:raise ValueError("Unexpected empty/private/Test directory")
    return names


def _verify_contents(root,bundle,bindings):
    keys={"version","scope","status","bindings","contract","attribution","notice","mgi_schema",
          "qualified_labels_approved","participant_independence_verified","final_research_approved",
          "generated_authorization","generated_draft","plan","records","files"}
    if (set(bundle)!=keys or bundle.get("version")!=VERSION or bundle.get("scope")!=GENERATED_SCOPE
            or bundle.get("status")!="verified_generated_exploratory_only"
            or bundle.get("bindings")!=bindings or bundle.get("contract")!=contract_spec()
            or bundle.get("attribution")!=DATASET_ATTRIBUTION or bundle.get("notice")!=legacy.NOTICE
            or bundle.get("mgi_schema")!=[0,1,2,3,4]
            or any(bundle.get(k) is not False for k in
                   ("qualified_labels_approved","participant_independence_verified","final_research_approved"))):
        raise ValueError("Invalid B1 contract/attribution/approval boundaries")
    _authorize(bundle["generated_authorization"],bindings,True)
    plan=bundle["plan"]
    _current_plan(bundle["generated_draft"],plan,bindings["source_plan_sha256"])
    rows=bundle["records"]
    expected={r["source_record_id"]:r for r in plan["records"]}
    if len(rows)!=733 or len({r["source_record_id"] for r in rows})!=733:
        raise ValueError("Exact manifest record membership required")
    all_files={}
    for row in rows:
        identifier=row["source_record_id"]
        if identifier not in expected or any(row.get(k)!=v for k,v in expected[identifier].items()):
            raise ValueError("Record differs from trusted source plan")
        if set(row)!=set(expected[identifier])|{"label_status","qualified_label_approved","participant_id","stream_receipt_sha256","files"}:
            raise ValueError("Extra/private package record fields")
        if row.get("qualified_label_approved") is not False or row.get("participant_id") is not None or row.get("label_status")!="provisional":
            raise ValueError("Unapproved labels/participant claims")
        prefix="records/"+identifier+"/"
        names={prefix+"model_rgb.npy",prefix+"source_receipt.json"}
        if identifier in legacy.CAM_IDS:names.add(prefix+"full_rgb.npy")
        if set(row["files"])!=names:raise ValueError("Wrong payload/CAM membership")
        receipt=_json_file(legacy.safe_file(root,prefix+"source_receipt.json"))
        if (b1.digest_json(receipt)!=row["stream_receipt_sha256"]
                or receipt["version"]!=stream.VERSION or receipt["scope"]!=GENERATED_SCOPE
                or receipt["contract_sha256"]!=b1.digest_json(stream.CONTRACT)
                or receipt["base_contract_sha256"]!=b1.contract_hash()
                or receipt["generated_source"]!=row["generated_recipe"]
                or receipt["source_rgb_sha256"]!=row["checked_source"]["source_rgb_sha256"]
                or receipt["profile_sha256"]!=row["checked_source"]["profile_sha256"]):
            raise ValueError("B1 source/precision receipt binding mismatch")
        spec=row["generated_recipe"]
        if receipt["valid_box"]!=stream.full_geometry(spec["width"],spec["height"]):
            raise ValueError("B1 geometry mismatch")
        for k,v in row["checked_source"]["numeric"].items():
            if receipt["numeric"][k]!=v:raise ValueError("B1 precision receipt mismatch")
        if set(receipt)!= {"version","scope","base_contract_sha256","contract_sha256","generated_source",
                           "source_rgb_sha256","profile_sha256","numeric","files","valid_box"}:
            raise ValueError("Private/extra source receipt metadata")
        if (set(receipt["numeric"])!={"xyz_max_abs","lab_max_delta_e76","peak_chunk_pixels"}
                or type(receipt["numeric"]["peak_chunk_pixels"]) is not int
                or not 1<=receipt["numeric"]["peak_chunk_pixels"]<=stream.TILE_PIXELS
                or set(receipt["files"])!={"full_rgb.npy","model_rgb.npy"}):
            raise ValueError("Private/invalid nested source receipt evidence")
        for name,digest in row["files"].items():
            path=legacy.safe_file(root,name)
            if legacy.sha256(path)!=digest:raise ValueError("Generated payload hash mismatch")
            if name.endswith(".npy"):
                key=Path(name).name
                shape=(224,224,3) if key=="model_rgb.npy" else (spec["height"],spec["width"],3)
                with stream._open(path) as payload:evidence,_,_=stream._inspect(payload,shape)
                if evidence!=receipt["files"][key]:raise ValueError("Actual NPY evidence mismatch")
            all_files[name]=digest
        if identifier in legacy.CAM_IDS:
            full_path=legacy.safe_file(root,prefix+"full_rgb.npy")
            with stream._open(full_path) as full:
                _,offset,identity=stream._inspect(full,(spec["height"],spec["width"],3))
                expected_model=stream._model_view(full,offset,spec["width"],spec["height"],identity)
            model_path=legacy.safe_file(root,prefix+"model_rgb.npy")
            with stream._open(model_path) as model:
                _,offset,_=stream._inspect(model,(224,224,3))
                model.seek(offset)
                if sha256(model.read()).hexdigest()!=sha256(expected_model.tobytes()).hexdigest():
                    raise ValueError("Retained CAM/model alignment mismatch")
    if all_files!=bundle["files"]:raise ValueError("Complete file manifest mismatch")
    return all_files


def _verify_archive(path,files,manifest_sha,root):
    with zipfile.ZipFile(path) as archive:
        entries=archive.infolist()
        expected={**files,"bundle_manifest.json":manifest_sha}
        if len(entries)!=len(expected) or {e.filename for e in entries}!=set(expected):
            raise ValueError("Generated ZIP membership mismatch")
        for entry in entries:
            actual=legacy.safe_file(root,entry.filename)
            if (not stat.S_ISREG(entry.external_attr>>16) or entry.flag_bits&1
                    or entry.file_size!=actual.stat().st_size
                    or entry.compress_type not in {zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED}):
                raise ValueError("Unsafe generated ZIP type/size/encoding")
            digest=sha256()
            with archive.open(entry) as content:
                for block in iter(lambda:content.read(1024*1024),b""):digest.update(block)
            if digest.hexdigest()!=expected[entry.filename]:raise ValueError("Generated ZIP hash/CRC mismatch")


def validate_generated_package(root,trusted_manifest_sha256,trusted_bindings):
    root=Path(root)
    manifest=legacy.safe_file(root,"bundle_manifest.json")
    if not b1._sha(trusted_manifest_sha256) or legacy.sha256(manifest)!=trusted_manifest_sha256:
        raise ValueError("Trusted B1 manifest hash mismatch")
    bundle=_json_file(manifest)
    current=authorization_bindings(bundle["plan"],root)
    if current!=trusted_bindings:raise ValueError("Stale B1 code/contract/output binding")
    files=_verify_contents(root,bundle,trusted_bindings)
    if _payload_members(root)!=set(files)|{"bundle_manifest.json","COMPLETE.json"}:
        raise ValueError("Extra/missing package files or incomplete output")
    complete=_json_file(legacy.safe_file(root,"COMPLETE.json"))
    archive=root.with_suffix(".zip")
    if (complete!={"manifest_sha256":trusted_manifest_sha256,"archive_sha256":legacy.sha256(archive),"scope":GENERATED_SCOPE}):
        raise ValueError("Completion/archive evidence mismatch")
    _verify_archive(archive,files,trusted_manifest_sha256,root)
    return {"records":len(bundle["records"]),"files":len(files),"scope":GENERATED_SCOPE}


def package_generated_b1(draft,plan,trusted_plan_sha256,output,authorization,*,opt_in=False):
    output=Path(output)
    bindings=authorization_bindings(plan,output)
    _authorize(authorization,bindings,opt_in)
    _current_plan(draft,plan,trusted_plan_sha256)
    attempt=_fresh_output(output)
    with stream._open(attempt,write=True) as marker:
        marker.write(json.dumps({"scope":GENERATED_SCOPE,"output_id":output.name,"bindings":bindings}).encode())
    output.mkdir(mode=0o700)
    work=output/".working";work.mkdir(mode=0o700)
    records=[];files={}
    for row in plan["records"]:
        item=_export_row(row,work,output);records.append(item);files.update(item["files"])
    work.rmdir()
    bundle={"version":VERSION,"scope":GENERATED_SCOPE,"status":"verified_generated_exploratory_only",
            "bindings":bindings,"contract":contract_spec(),"attribution":deepcopy(DATASET_ATTRIBUTION),
            "notice":legacy.NOTICE,"mgi_schema":[0,1,2,3,4],"qualified_labels_approved":False,
            "participant_independence_verified":False,"final_research_approved":False,
            "generated_authorization":deepcopy(authorization),"generated_draft":deepcopy(draft),
            "plan":deepcopy(plan),"records":records,"files":files}
    _verify_contents(output,bundle,bindings)
    if _payload_members(output)!=set(files):raise ValueError("Unexpected pre-manifest files")
    manifest=output/"bundle_manifest.json"
    with stream._open(manifest,write=True) as target:target.write((json.dumps(bundle,indent=2,allow_nan=False)+"\n").encode())
    manifest_sha=legacy.sha256(manifest)
    temporary=output.with_suffix(".zip.partial")
    with zipfile.ZipFile(temporary,"x",compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(set(files)|{"bundle_manifest.json"}):archive.write(legacy.safe_file(output,name),name)
    _verify_archive(temporary,files,manifest_sha,output)
    with stream._open(output/"COMPLETE.json",write=True) as target:
        target.write(json.dumps({"manifest_sha256":manifest_sha,"archive_sha256":legacy.sha256(temporary),"scope":GENERATED_SCOPE}).encode())
    # Hard link publishes without overwriting an existing final ZIP; last step.
    archive=output.with_suffix(".zip")
    os.link(temporary,archive)
    temporary.unlink()
    return {"directory":str(output),"archive":str(archive),"archive_sha256":legacy.sha256(archive),
            "manifest_sha256":manifest_sha,"bindings":bindings,"records":len(records),
            "scope":GENERATED_SCOPE,"real_packaging_authorized":False}
