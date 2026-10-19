"""Verify the owner's fixed-fold Colab return; never fit or modify existing models."""
import hashlib
import json
from pathlib import Path
import shutil
import stat
import sys
import zipfile

import numpy as np
from PIL import Image, ImageDraw
import torch

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from src.vision import resnet50_fold0_pilot_v1 as pilot

INPUT = Path("/Users/vinuthanvinuthan/Downloads/resnet50_fold0_return_v1.zip")
EXPECTED_SHA = "e169edc135e5f6786bf510bd81d5cb3b77125d08edfa944ac5f121f4f694de8c"
PREPARATION = REPO / "data/vision/resnet50_fold0_pilot_v1_20261018_r2"
OUTPUT = PREPARATION / "colab_return_v1_20261018"


def independent_metrics(labels, probabilities):
    """Calculate confusion-based metrics without the training runner or sklearn."""
    predicted = probabilities.argmax(1) + 1
    matrix = np.zeros((4,4), dtype=int)
    np.add.at(matrix, (labels-1, predicted-1), 1)
    support, counts = matrix.sum(1), matrix.sum(0)
    diagonal = np.diag(matrix)
    recalls = diagonal / support
    f1 = np.divide(2*diagonal, support+counts, out=np.zeros(4), where=(support+counts)>0)
    distances = np.arange(4)[:, None] - np.arange(4)[None, :]
    expected = np.outer(support, counts) / len(labels)
    qwk = 1 - ((distances**2)*matrix).sum() / ((distances**2)*expected).sum()
    return {"accuracy": float(diagonal.sum()/len(labels)), "macro_f1": float(f1.mean()),
            "balanced_accuracy": float(recalls.mean()),
            "per_grade_recall": {str(i+1): float(v) for i,v in enumerate(recalls)},
            "confusion_matrix": matrix.tolist(), "confusion_matrix_labels": [1,2,3,4],
            "ordinal_mae": float((np.abs(distances)*matrix).sum()/len(labels)),
            "quadratic_weighted_kappa": float(qwk)}


def tensor_hashes(state):
    return {name: hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()
            for name, value in state.items()}


def main():
    if pilot.sha256_file(INPUT) != EXPECTED_SHA:
        raise ValueError("Return ZIP differs from owner's SHA")
    OUTPUT.mkdir()
    protected = json.loads((PREPARATION / "preservation_before.json").read_text())
    before = {name: pilot.sha256_file(REPO / name) for name in protected}
    if before != protected:
        raise ValueError("Existing protected artifacts changed before verification")
    pilot.write_json(OUTPUT / "preservation_before.json", before)
    copy = OUTPUT / INPUT.name
    shutil.copyfile(INPUT, copy)
    if pilot.sha256_file(copy) != EXPECTED_SHA:
        raise ValueError("Preservation copy differs")
    package = PREPARATION / "package"
    manifest_path = package / "manifest.json"
    manifest_sha = pilot.sha256_file(manifest_path)
    expected_preparation = json.loads((PREPARATION / "preparation.json").read_text())
    assert manifest_sha == expected_preparation["manifest_sha256"]
    manifest = json.loads(manifest_path.read_text())
    pilot.validate_records(manifest)
    assert pilot.sha256_file(Path(pilot.__file__)) == manifest["files"]["src/vision/resnet50_fold0_pilot_v1.py"]["sha256"]
    extracted = OUTPUT / "artifacts"
    extracted.mkdir()
    expected = {"run_binding.json", "complete.json", "metrics.json", "predictions.json"}
    for stage in ("warmup", "A", "B"):
        for epoch in range(1, 2 if stage == "warmup" else 6):
            expected.update({f"{stage}/epoch_{epoch:02}.pt", f"{stage}/epoch_{epoch:02}.json"})
    for record_id in manifest["cam_ids"]:
        number = record_id.split("/")[1]
        for arm in ("A", "B"):
            for target in ("predicted", "common_A_target"):
                expected.update({f"cam/{number}/{arm}/{target}/{name}" for name in
                                 ("original.png", "heatmap.png", "overlay.png", "explanation.json")})
    with zipfile.ZipFile(copy) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names)) == 215
        assert sum(i.file_size for i in archive.infolist()) < 3*1024**3
        files = {i.filename for i in archive.infolist() if not i.is_dir()}
        assert files == expected | {"return_integrity.json"}
        integrity = json.loads(archive.read("return_integrity.json"))
        assert set(integrity) == expected and len(integrity) == 154
        for info in archive.infolist():
            name = Path(info.filename)
            assert not name.is_absolute() and ".." not in name.parts
            assert not stat.S_ISLNK(info.external_attr >> 16)
            assert info.file_size < 512*1024**2
            if info.is_dir():
                continue
            path = extracted / name
            path.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with archive.open(info) as source, path.open("xb") as target:
                for block in iter(lambda: source.read(1024*1024), b""):
                    digest.update(block)
                    target.write(block)
            # Reading the full member also validates its ZIP CRC.
            if name.as_posix() != "return_integrity.json":
                assert digest.hexdigest() == integrity[name.as_posix()], name
    print("Return integrity:154/154 members passed; source archive preserved", flush=True)
    read = lambda name: json.loads((extracted / name).read_text())
    binding, complete = read("run_binding.json"), read("complete.json")
    assert binding["config"] == pilot.CONFIG and binding["manifest_sha256"] == manifest_sha
    assert binding["weights_sha256"] == pilot.WEIGHTS_SHA and binding["training_authorized"] is True
    assert complete["status"] == "fixed_fold0_completed"
    assert complete["test_used"] is False and complete["validation_used"] is False
    score_rows = [r for r in manifest["records"] if r["role"] == "score"]
    fit_rows = [r for r in manifest["records"] if r["role"] == "fit"]
    ids, labels = [r["id"] for r in score_rows], np.array([r["grade"] for r in score_rows])
    predictions, saved_metrics = read("predictions.json"), read("metrics.json")
    assert saved_metrics["n_score"] == 136
    recalculated, probabilities, max_difference = {}, {}, 0.
    for arm in ("A", "B"):
        rows = predictions[arm]
        assert [r["id"] for r in rows] == ids
        assert [r["provisional_grade"] for r in rows] == labels.tolist()
        values = np.array([r["uncalibrated_probabilities_grades_1_to_4"] for r in rows])
        assert values.shape == (136,4) and np.isfinite(values).all() and (values>=0).all()
        assert np.allclose(values.sum(1),1,atol=1e-6,rtol=0)
        assert [r["predicted_grade"] for r in rows] == (values.argmax(1)+1).tolist()
        recalculated[arm] = independent_metrics(labels, values)
        probabilities[arm] = values
        for name, value in recalculated[arm].items():
            if name in ("confusion_matrix", "confusion_matrix_labels", "per_grade_recall"):
                assert value == saved_metrics["arms"][arm][name]
            else:
                difference = abs(value - saved_metrics["arms"][arm][name])
                max_difference = max(max_difference, difference)
                assert difference < 1e-12
    majority = np.zeros((136,4)); majority[:,3] = 1
    recalculated["fitting_majority_grade4"] = independent_metrics(labels, majority)
    for key, value in saved_metrics["B_minus_A"].items():
        assert abs(value - (recalculated["B"][key]-recalculated["A"][key])) < 1e-12
    print("Independent136-image metrics reproduced for A/B", flush=True)
    torch.set_num_threads(2)
    weights = package / "weights/resnet50-11ad3fa6.pth"
    model = pilot.model_factory(weights).eval()
    fresh = pilot.state_hashes(model)
    allowed = {stage: set(pilot.configure(model, stage)[1]) for stage in ("warmup", "A", "B")}
    shapes = {name: tuple(value.shape) for name,value in model.state_dict().items()}
    del model
    expected_class_weights = pilot.class_weights(np.array([r["grade"] for r in fit_rows])).tolist()
    checkpoint_receipts, final_states, stage_initial, warmup_final = [], {}, {}, None
    for stage in ("warmup", "A", "B"):
        for epoch in range(1,2 if stage=="warmup" else 6):
            path = extracted / stage / f"epoch_{epoch:02}.pt"
            saved = torch.load(path, map_location="cpu", weights_only=True)
            log = read(f"{stage}/epoch_{epoch:02}.json")
            assert saved["binding"] == binding and saved["config"] == pilot.CONFIG
            assert saved["stage"] == stage and saved["epoch"] == epoch
            assert set(saved["trainable_names"]) == allowed[stage]
            assert saved["class_weights"] == expected_class_weights
            initial = saved["initial_tensor_hashes"]
            stage_initial.setdefault(stage, initial)
            assert stage_initial[stage] == initial
            assert set(saved["model"]) == set(shapes)
            assert all(tuple(v.shape)==shapes[n] and torch.isfinite(v).all() for n,v in saved["model"].items())
            actual = tensor_hashes(saved["model"])
            assert actual == saved["tensor_hashes"]
            changed = {name for name in initial if actual[name] != initial[name]}
            assert changed <= allowed[stage]
            expected_identity = pilot.digest({"binding":binding,"stage":stage,"initial":initial,
                "config":pilot.CONFIG,"torch":binding["torch"],"device":"cuda"})
            assert saved["identity"] == expected_identity
            order_sha = pilot.digest(pilot.epoch_order(544,stage,epoch).tolist())
            assert order_sha == saved["order_sha256"]
            assert all(log[key]==saved[key] for key in log)
            optimizer = saved["optimizer"]
            assert len(optimizer["state"]) == len(allowed[stage])
            assert [g["lr"] for g in optimizer["param_groups"]] == ([.001] if stage=="warmup" else [.001,.00001])
            assert all(g["weight_decay"]==0 for g in optimizer["param_groups"])
            assert all(float(item["step"])==34*epoch for item in optimizer["state"].values())
            assert all(torch.isfinite(item[field]).all() for item in optimizer["state"].values()
                       for field in ("exp_avg","exp_avg_sq"))
            checkpoint_receipts.append({"stage":stage,"epoch":epoch,"tensor_hashes_verified":len(actual),
                "trainable_tensors":len(allowed[stage]),"changed_tensors":len(changed),
                "frozen_tensors_unchanged":True,"order_sha256":order_sha,"optimizer_steps":34*epoch})
            if stage=="warmup": warmup_final=actual
            if epoch==(1 if stage=="warmup" else 5):
                completion = complete["warmup"] if stage=="warmup" else complete["arms"][stage]
                assert completion["initial_sha256"] == pilot.digest(initial)
                assert completion["final_sha256"] == pilot.digest(actual)
                if stage != "warmup": final_states[stage] = saved["model"]
            del saved
    assert stage_initial["A"] == stage_initial["B"] == warmup_final
    assert all(stage_initial["warmup"][n] == v for n,v in fresh.items() if not n.startswith("fc."))
    initializer_match = sum(stage_initial["warmup"][n]==v for n,v in fresh.items())
    print("All11 checkpoints: provenance, tensor hashes, frozen BN and optimizer counts passed", flush=True)
    cam_receipts, reproduction = [], []
    for arm in ("A", "B"):
        model = pilot.model_factory(weights).eval()
        model.load_state_dict(final_states[arm])
        start_hashes = pilot.state_hashes(model)
        for record_id in manifest["cam_ids"]:
            row = next(r for r in score_rows if r["id"]==record_id)
            i = ids.index(record_id)
            assert pilot.sha256_file(package/row["array"]) == row["array_sha256"]
            array = pilot.b1.normalize(np.load(package/row["array"],allow_pickle=False))
            with Image.open(package/row["preview"]) as image: original = np.asarray(image).copy()
            prepared = pilot.cam.RGBInput(original,array,tuple(row["valid_box"]))
            with torch.no_grad(): values=model(torch.from_numpy(array[None])).softmax(1)[0].numpy()
            error = float(np.abs(values-probabilities[arm][i]).max())
            assert error < 1e-4 and int(values.argmax())+1 == predictions[arm][i]["predicted_grade"]
            reproduction.append({"arm":arm,"id":record_id,"probability_max_abs_error":error})
            for target in ("predicted", "common_A_target"):
                index = int(probabilities[arm if target=="predicted" else "A"][i].argmax())
                directory = extracted/"cam"/record_id.split("/")[1]/arm/target
                detail = json.loads((directory/"explanation.json").read_text())
                assert detail["explained_grade"]==index+1 and detail["predicted_grade"]==int(values.argmax())+1
                assert detail["native_feature_shape"]==[1,2048,7,7] and detail["target_layer"]=="layer4[-1]"
                views, computed = pilot.gradcam(model, prepared, index)
                assert computed["explanation_status"]==detail["explanation_status"]
                differences = {}
                for name in ("original","heatmap","overlay"):
                    with Image.open(directory/(name+".png")) as image:
                        assert image.mode=="RGB" and not image.info
                        pixels=np.asarray(image)
                    assert pixels.shape==original.shape
                    if name=="original": assert np.array_equal(pixels,original)
                    delta = np.abs(pixels.astype(float)-views[name].astype(float))
                    differences[name] = {"max":float(delta.max()),"mean":float(delta.mean())}
                cam_receipts.append({"arm":arm,"id":record_id,"target":target,
                    "explained_grade":index+1,"status":detail["explanation_status"],
                    "display_byte_differences_cpu_minus_colab":differences})
        assert pilot.state_hashes(model)==start_hashes
        assert not model.layer4[-1]._forward_hooks
        assert all(p.grad is None for p in model.parameters())
        del model
    print("16 matched image predictions and32 CAM views independently reproduced on CPU", flush=True)
    # Contact sheets only arrange original saved panels; no attention pixels are edited.
    visual = OUTPUT/"review";visual.mkdir()
    for page in range(2):
        sheet=Image.new("RGB",(1600,4*300+55),"white")
        draw=ImageDraw.Draw(sheet)
        for col,label in enumerate(("Original / provisional label","A predicted-class CAM","B common A target","B predicted-class CAM")):
            draw.text((col*400+8,12),label,fill="black")
        for j,record_id in enumerate(manifest["cam_ids"][page*4:page*4+4]):
            row = next(r for r in score_rows if r["id"]==record_id)
            number=record_id.split("/")[1]
            panel_paths=[extracted/f"cam/{number}/A/predicted/original.png",
                         extracted/f"cam/{number}/A/predicted/overlay.png",
                         extracted/f"cam/{number}/B/common_A_target/overlay.png",
                         extracted/f"cam/{number}/B/predicted/overlay.png"]
            for col,path in enumerate(panel_paths):
                with Image.open(path) as image:
                    display=image.copy();display.thumbnail((390,260))
                sheet.paste(display,(col*400+5,j*300+75))
            i=ids.index(record_id)
            draw.text((8,j*300+55),f"{record_id} | provisional {row['grade']} | A {predictions['A'][i]['predicted_grade']} | B {predictions['B'][i]['predicted_grade']}",fill="black")
        sheet.save(visual/f"matched_cam_page_{page+1}.png")
    after={name:pilot.sha256_file(REPO/name) for name in before}
    assert before==after
    pilot.write_json(OUTPUT/"preservation_after.json",after)
    result={"status":"passed","return_sha256":EXPECTED_SHA,"return_files_verified":154,
            "checkpoint_count":len(checkpoint_receipts),"checkpoint_tensor_hash_checks":sum(r["tensor_hashes_verified"] for r in checkpoint_receipts),
            "shared_warmup_verified":True,"official_initializer_tensor_hash_matches":initializer_match,
            "initializer_tensor_count":len(fresh),"metrics_max_abs_error":max_difference,
            "matched_prediction_reproduction":reproduction,"cam_reproduction":cam_receipts,
            "checkpoint_checks":checkpoint_receipts,"metrics":recalculated,
            "protected_artifacts_unchanged":len(before),"new_training":False,"test_access":False,
            "clinical_localization_validated":False}
    pilot.write_json(OUTPUT/"verification.json",result)
    print(json.dumps({k:result[k] for k in ("status","return_files_verified","checkpoint_count","checkpoint_tensor_hash_checks",
        "shared_warmup_verified","official_initializer_tensor_hash_matches","initializer_tensor_count",
        "metrics_max_abs_error","protected_artifacts_unchanged")},indent=2))


if __name__=="__main__":
    main()
