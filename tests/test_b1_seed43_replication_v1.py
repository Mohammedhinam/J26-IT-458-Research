"""Small protocol and boundary tests; no real image or checkpoint is opened."""
from dataclasses import asdict

import pytest

from src.vision import exploratory_bundle as legacy
from src.vision import exploratory_pilot_b1_lastblock_v3 as stage
from src.vision import exploratory_pilot_b1_seed43_v1 as seed43
from src.vision import train_pipeline as trainer


def make_records():
    rows = []
    for split, count in legacy.EXPECTED_COUNTS.items():
        grades = [grade for grade in range(5)
                  for _ in range(legacy.EXPECTED_GRADES[split][grade])]
        for index in range(count):
            identifier = (seed43.CAM_IDS[index] if split == "Validation" and index < 3
                          else f"{split}/{index + 10000:05d}")
            rows.append({
                "source_record_id": identifier,
                "original_split": split,
                "content_group_id": "synthetic-group-" + str(len(rows)),
                "label_status": "provisional",
                "qualified_label_approved": False,
                "provisional_mgi_grade": grades[index],
            })
    return rows


def test_seed43_changes_only_seed_and_device_is_local():
    prior = asdict(stage.configuration("cpu"))
    current = asdict(seed43.configuration("cpu"))
    assert prior["seed"] == 42
    assert current["seed"] == 43
    current["seed"] = 42
    assert current == prior
    assert seed43.configuration("cpu").device == "cpu"
    assert seed43.protocol("cpu")["mgi_outputs"] == [1, 2, 3, 4]
    assert seed43.protocol("cpu")["research_mgi_schema_unchanged"] == [0, 1, 2, 3, 4]


def test_development_membership_and_all_original_content_groups_pass():
    summary = seed43.validate_records(make_records())
    assert summary["records"] == 733
    assert summary["counts"] == {"Training": 680, "Validation": 53}
    assert summary["unique_content_groups"] == 733
    assert summary["test_records"] == summary["held_records_included"] == 0
    assert summary["np015_included"] == 0


def test_test_or_nondevelopment_record_is_rejected_before_grade_read():
    class TestRow(dict):
        def get(self, key, default=None):
            if key == "provisional_mgi_grade":
                raise AssertionError("grade was read before split was rejected")
            return super().get(key, default)

    rows = make_records()
    rows.append(TestRow(original_split="Test", source_record_id="Test/00001"))
    with pytest.raises(ValueError, match="Test or nondevelopment"):
        seed43.validate_records(rows)


@pytest.mark.parametrize("identifier", legacy.NP015_IDS)
def test_np015_is_rejected(identifier):
    rows = make_records()
    rows[0]["source_record_id"] = identifier
    with pytest.raises(ValueError, match="NP015"):
        seed43.validate_records(rows)


def test_content_group_reuse_is_rejected():
    rows = make_records()
    rows[-1]["content_group_id"] = rows[0]["content_group_id"]
    with pytest.raises(ValueError, match="content group"):
        seed43.validate_records(rows)


def test_local_authorization_binds_every_protocol_and_excludes_cloud_test():
    run_id = "synthetic-seed43-run"
    record = {
        "status": "owner_confirmed", "scope": seed43.SCOPE,
        "authorizer": "synthetic owner fixture", "date": "synthetic",
        "evidence_reference": "generated test only",
        "acknowledgements": {name: True for name in legacy.ACKS},
        "local_training_authorized": True,
        "cloud_upload_authorized": False,
        "test_access_authorized": False,
        **seed43.bindings(run_id, "cpu"),
    }
    seed43.authorize_record(record, run_id, "cpu")
    record["initial_checkpoint_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="binding"):
        seed43.authorize_record(record, run_id, "cpu")


def test_runner_requires_opt_in_before_any_path_or_dataset_access(tmp_path):
    with pytest.raises(ValueError, match="opt-in"):
        seed43.run_local(tmp_path / "missing", tmp_path / "missing.zip",
                         tmp_path / "fresh-run", {}, opt_in=False)


def test_config_rejects_cloud_device_and_training_recipe_drift():
    with pytest.raises(ValueError, match="CPU or MPS"):
        seed43.configuration("cuda").validate()
    config = seed43.configuration("cpu")
    assert config.unfreeze_prefixes == ("layer4.2",)
    assert config.batch_size == 16 and config.epochs == 5 and config.patience == 2
    assert config.class_weight == "balanced" and config.batchnorm == "frozen"
    assert trainer.digest(seed43.protocol("cpu")["training"]) == trainer.digest(asdict(config))
