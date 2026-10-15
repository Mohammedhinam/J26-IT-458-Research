"""Synthetic-only qualification of the one-variable weighted comparison."""
from dataclasses import asdict, replace
import json
from pathlib import Path

import numpy as np
import pytest

from src.vision import exploratory_pilot_b1_balanced_v2 as weighted
from src.vision import exploratory_pilot_b1_v1 as base
from src.vision import verify_b1_balanced_runtime_v2 as verification
from src.vision import train_pipeline as trainer


def test_only_class_weight_changes_training_configuration():
    old, new = asdict(base.configuration()), asdict(weighted.configuration())
    assert new.pop("class_weight") == "balanced"
    assert old.pop("class_weight") == "none"
    assert old == new
    assert weighted.protocol()["research_schema_unchanged"] == [0, 1, 2, 3, 4]
    assert weighted.protocol()["grades"] == [1, 2, 3, 4]


def test_weights_match_independent_training_only_reference():
    labels = np.repeat([1, 2, 3, 4], [12, 84, 223, 361])
    np.testing.assert_allclose(weighted.training_weights(labels),
                               [680/(4*n) for n in (12,84,223,361)], rtol=1e-7)
    assert np.dot(weighted.training_weights(labels), [12,84,223,361]) == pytest.approx(680)


@pytest.mark.parametrize("bad", [[], [0,1,2,3], [1,2,3], [1,2,3,5], [1.,2.,3.,4.], [-1,2,3,4]])
def test_no_fabricated_absent_or_invalid_grade_weights(bad):
    with pytest.raises(ValueError): weighted.training_weights(bad)


def prediction_example():
    rows = [{"source_record_id": "Validation/" + str(800+i).zfill(5), "original_split": "Validation",
             "provisional_mgi_grade": i+1} for i in range(4)]
    return rows, {"labels": [1,2,3,4], "probabilities": np.eye(4).tolist()}


def test_probabilities_cover_original_validation_ids_and_grades():
    rows, evidence = prediction_example()
    result = weighted.validation_predictions(rows, evidence)
    assert [r["predicted_mgi_grade"] for r in result["records"]] == [1,2,3,4]
    assert result["records"][0]["source_record_id"] == "Validation/00800"


@pytest.mark.parametrize("bad", ["Test", "NP015", "duplicate", "label", "length", "nan"])
def test_prediction_export_rejects_wrong_coverage_or_labels(bad):
    rows, evidence = prediction_example()
    if bad == "Test": rows[0]["original_split"] = "Test"
    if bad == "NP015": rows[0]["source_record_id"] = "Validation/00736"
    if bad == "duplicate": rows[1]["source_record_id"] = rows[0]["source_record_id"]
    if bad == "label": rows[0]["provisional_mgi_grade"] = 2
    if bad == "length": rows.pop()
    if bad == "nan": evidence["probabilities"][0][0] = float("nan")
    with pytest.raises(ValueError): weighted.validation_predictions(rows, evidence)


def auth_example():
    record = {"scope": weighted.SCOPE, "status": "owner_confirmed", "authorizer": "synthetic-test-owner",
              "date": "synthetic", "evidence_reference": "temporary unit-test fixture, not a real approval",
              "acknowledgements": {name: True for name in base.legacy.ACKS},
              "cloud_upload_authorized": True, "training_authorized": True,
              "bundle_manifest_sha256": weighted.MANIFEST_SHA,
              "protocol_sha256": trainer.digest(weighted.protocol()),
              "code_sha256": trainer.digest(weighted.code_hashes()), "weights_sha256": weighted.WEIGHTS_SHA,
              "verification_sha256": "a"*64, "output_run_id": "synthetic_run"}
    return record, {"sha256": weighted.WEIGHTS_SHA, "status": "documented_cache_present"}


@pytest.mark.parametrize("field", ["scope", "protocol_sha256", "code_sha256", "weights_sha256", "verification_sha256", "output_run_id"])
def test_old_scope_stale_bindings_and_replay_target_rejected(field):
    record, weights = auth_example()
    record[field] = "old-or-stale"
    with pytest.raises(ValueError):
        weighted.validate_execution(record, "synthetic_run", weighted.MANIFEST_SHA, weights, "a"*64)


def test_no_opt_in_fails_before_any_runtime_or_data_access():
    with pytest.raises(ValueError, match="opt-in"):
        weighted.run_pilot("/nonexistent", {}, "/nonexistent", "/nonexistent")


def test_synthetic_gate_reads_xml_and_actual_payload_hashes(tmp_path, monkeypatch):
    # Temporary generated proof fixture tests the gate; it is not execution evidence.
    project = tmp_path / "project"
    project.mkdir()
    source = project / "synthetic.py"
    source.write_text("# generated fixture only\n")
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    monkeypatch.setattr(verification, "__file__", str(project / "src/vision/runtime.py"))
    expected = {"synthetic.py": base.legacy.sha256(source)}
    ids = ["synthetic::" + name for name in verification.BACKENDS]
    (project / "verification_manifest.json").write_text(json.dumps({"files": expected, "expected_case_ids": ids}))
    xml = '<testsuites><testsuite>' + ''.join('<testcase classname="synthetic" name="'+n+'"/>' for n in verification.BACKENDS) + '</testsuite></testsuites>'
    (evidence / "junit.xml").write_text(xml)
    _, counts, _ = verification.case_results(evidence / "junit.xml")
    values = {"summary.json": {"status": "PASS", "pytest_exit_code": 0, "counts": counts},
              "source_hashes_before.json": expected, "source_hashes_after.json": expected}
    for name, value in values.items(): (evidence/name).write_text(json.dumps(value))
    (evidence / "pytest.log").write_text("generated gate fixture, not actual test evidence")
    hashes = {p.name: base.legacy.sha256(p) for p in evidence.iterdir()}
    (evidence / "evidence_manifest.json").write_text(json.dumps({"files": hashes}))
    assert len(verification.require_pass(evidence)) == 64
    (evidence / "junit.xml").write_text(xml.replace('/>', '><skipped/></testcase>', 1))
    # Even a self-consistent receipt and a claimed PASS cannot hide a real skip.
    _, skipped_counts, _ = verification.case_results(evidence / "junit.xml")
    (evidence / "summary.json").write_text(json.dumps({"status":"PASS", "pytest_exit_code":0,
                                                     "counts":skipped_counts}))
    hashes = {p.name: base.legacy.sha256(p) for p in evidence.iterdir() if p.name != "evidence_manifest.json"}
    (evidence / "evidence_manifest.json").write_text(json.dumps({"files":hashes}))
    with pytest.raises(ValueError): verification.require_pass(evidence)


def backend():
    torch = pytest.importorskip("torch", reason="Colab backend required; no local install")
    pytest.importorskip("torchvision")
    torch.set_num_threads(1)
    return torch


def test_weighted_mean_matches_independent_reference_and_all_one_gradients():
    torch = backend()
    logits = torch.tensor([[2.,0.,-1.,.5],[0.,1.,2.,-1.],[1.,0.,-1.,2.]], requires_grad=True)
    targets = torch.tensor([0,2,3])
    weights = torch.tensor([4.,2.,1.,.5])
    losses = torch.nn.functional.cross_entropy(logits, targets, reduction="none")
    actual = weighted.weighted_objective(losses, targets, weights)
    reference = torch.nn.functional.cross_entropy(logits, targets, weight=weights)
    np.testing.assert_allclose(actual.detach(), reference.detach(), rtol=1e-6)
    raw = logits.detach().numpy().astype(float)
    raw_ce = np.log(np.exp(raw).sum(axis=1)) - raw[np.arange(3), [0,2,3]]
    expected = np.dot(raw_ce, [4.,1.,.5]) / 5.5
    assert actual.item() == pytest.approx(expected, rel=1e-6)
    ones = weighted.weighted_objective(losses, targets, torch.ones(4))
    expected_unweighted = losses.mean()
    a = torch.autograd.grad(ones, logits, retain_graph=True)[0]
    b = torch.autograd.grad(expected_unweighted, logits)[0]
    assert torch.equal(a,b)
    for invalid in (torch.tensor([0.,1.,1.,1.]), torch.full((4,),float('nan'))):
        with pytest.raises(ValueError): weighted.weighted_objective(losses, targets, invalid)


def test_weighted_resnet_step_keeps_initialization_backbone_and_batchnorm():
    torch = backend()
    trainer.seed_everything(42)
    first = base.make_model(pretrained=False)["model"]
    expected = first.fc.weight.detach().clone()
    del first
    trainer.seed_everything(42)
    network = base.make_model(pretrained=False)
    model = network["model"]
    assert torch.equal(model.fc.weight, expected)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    config = weighted.configuration(device)
    model.to(device)
    expected = expected.to(device)
    trainer.configure_trainable_layers(model,config)
    trainer.training_mode(model,config)
    mean = model.bn1.running_mean.clone()
    backbone = model.conv1.weight.detach().clone()
    values = torch.linspace(-3.,3.,2*3*32*32,device=device).reshape(2,3,32,32)
    logits = model(values)
    targets = torch.tensor([0,3],device=device)
    losses = torch.nn.functional.cross_entropy(logits,targets,reduction="none")
    optimizer = torch.optim.Adam([p for p in model.parameters() if p.requires_grad],lr=.001)
    weighted.weighted_objective(losses,targets,torch.tensor([4.,2.,1.,.5],device=device)).backward()
    optimizer.step()
    assert not torch.equal(model.fc.weight,expected)
    assert torch.equal(model.conv1.weight,backbone) and torch.equal(model.bn1.running_mean,mean)
    assert all(not p.requires_grad for name,p in model.named_parameters() if not name.startswith("fc."))
    assert logits.shape == (2,4)


def generated_data(torch, split):
    class Data:
        records = [{"source_record_id": split+"/"+str(100+i).zfill(5), "original_split": split,
                    "provisional_mgi_grade": i%4+1} for i in range(8)]
        def __len__(self): return 8
        def __getitem__(self,i): return torch.full((3,8,8),i/8), i%4
    return Data()


def tiny(torch):
    class Tiny(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.features = torch.nn.Sequential(torch.nn.Conv2d(3,4,1),torch.nn.BatchNorm2d(4),torch.nn.ReLU())
            self.fc = torch.nn.Linear(4,4)
        def forward(self,values): return self.fc(self.features(values).mean((2,3)))
    return Tiny()


def test_generated_weighted_fit_checkpoint_probabilities_and_reproducibility(tmp_path):
    torch = backend()
    config = replace(weighted.configuration("cpu"),batch_size=4,epochs=2)
    training, validation = generated_data(torch,"Training"), generated_data(torch,"Validation")
    results = []
    for name in ("a","b"):
        trainer.seed_everything(42)
        model = tiny(torch)
        result = weighted.fit(model,training,validation,config,tmp_path/name,{"generated_only":True})
        state = weighted.load_checkpoint(tmp_path/name/"best.pt",base.legacy.sha256(tmp_path/name/"best.pt"),{"generated_only":True},config)
        predictions = json.loads((tmp_path/name/"validation_predictions_best.json").read_text())
        assert (tmp_path/name/"initial_head.pt").is_file()
        assert len(predictions["records"]) == 8 and state["schema"] == [1,2,3,4]
        p = [r["probabilities_mgi1_to4"] for r in predictions["records"]]
        labels = [r["provisional_mgi_grade"] for r in predictions["records"]]
        assert base.metrics(labels,p) == {k:v for k,v in result["best_validation"].items() if k not in ("loss","weighted_ce_diagnostic")}
        results.append(result)
    assert results[0] == results[1]
    with pytest.raises(FileExistsError): weighted.fit(tiny(torch),training,validation,config,tmp_path/"a",{})


def test_weighted_epoch_uses_weight_sum_and_validation_does_not_update():
    torch = backend()
    config = weighted.configuration("cpu")
    trainer.seed_everything(42)
    model = tiny(torch)
    trainer.configure_trainable_layers(model,config)
    values = torch.ones((3,3,8,8)); targets = torch.tensor([0,0,3])
    weights = np.array([4.,2.,1.,.5],dtype=np.float32)
    before = {n:v.detach().clone() for n,v in model.state_dict().items()}
    metrics, evidence = weighted.run_epoch(model,[(values,targets)],config,weights)
    for name, value in model.state_dict().items(): assert torch.equal(value,before[name])
    with torch.no_grad():
        losses = torch.nn.functional.cross_entropy(model(values),targets,reduction="none")
    assert metrics["loss"] == pytest.approx(losses.mean().item())
    assert metrics["weighted_ce_diagnostic"] == pytest.approx((losses[0]*4+losses[1]*4+losses[2]*.5).item()/8.5)
    assert evidence["labels"] == [1,1,4]
