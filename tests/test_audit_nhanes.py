"""Focused audit checks using synthetic rows, not the local NHANES files."""

import pandas as pd
import pytest

from src.tabular.audit_nhanes import (
    PREDICTORS,
    build_report,
    join_valid_outcomes,
    restore_xport_zeros,
)


def small_tables():
    return {
        "P_OHQ": pd.DataFrame({"SEQN": [1, 2, 3, 4, 5, None], "OHQ850": [1, 2, 7, 9, None, 1]}),
        "P_DEMO": pd.DataFrame({"SEQN": [1, 2, None], "RIDAGEYR": [30, 80, 99]}),
        "P_SMQ": pd.DataFrame({"SEQN": [1], "SMQ020": [2]}),
        "P_DIQ": pd.DataFrame({"SEQN": [1], "DIQ010": [3]}),
    }


def test_valid_labels_and_left_joins_preserve_unmatched_rows():
    tables = small_tables()
    original_ohq = tables["P_OHQ"].copy(deep=True)
    valid, cohort, stages = join_valid_outcomes(tables)
    assert set(valid["OHQ850"]) == {1, 2}
    pd.testing.assert_frame_equal(cohort[["SEQN", "OHQ850"]], valid[["SEQN", "OHQ850"]].reset_index(drop=True))
    assert [stage[1] for stage in stages] == [3, 3, 3, 3]
    assert pd.isna(cohort.loc[cohort["SEQN"].eq(2), "SMQ020"].iloc[0])
    assert cohort.loc[cohort["SEQN"].isna(), "RIDAGEYR"].isna().all()
    pd.testing.assert_frame_equal(tables["P_OHQ"], original_ohq)


@pytest.mark.parametrize("module", ["P_OHQ", "P_SMQ"])
def test_duplicate_participant_keys_are_rejected(module):
    tables = small_tables()
    tables[module] = pd.concat([tables[module], tables[module].iloc[[0]]], ignore_index=True)
    with pytest.raises(pd.errors.MergeError, match="not a one-to-one merge"):
        join_valid_outcomes(tables)


def test_zero_decoding_correction_requires_exact_artifact_and_preserves_other_values(tmp_path):
    source = tmp_path / "zero.xpt"
    source.write_bytes(b"\x00" * 32)
    original_bytes = source.read_bytes()
    table = pd.DataFrame({"OHQ870": [2.0**-260, 0.0, None, 1e-20]})
    restore_xport_zeros(table, source, 0, 8, [{"npos": 0, "field_length": 8}])
    assert table["OHQ870"].iloc[0] == 0.0
    assert table["OHQ870"].iloc[1] == 0.0
    assert pd.isna(table["OHQ870"].iloc[2])
    assert table["OHQ870"].iloc[3] == 1e-20
    assert table.attrs["zero_decode_repairs"] == {"OHQ870": 1}
    assert source.read_bytes() == original_bytes


def test_unverified_tiny_value_is_never_changed(tmp_path):
    source = tmp_path / "not_zero.xpt"
    source.write_bytes(b"\x41\x10" + b"\x00" * 6)
    table = pd.DataFrame({"INDFMPIR": [2.0**-260]})
    with pytest.raises(ValueError, match="refusing to change"):
        restore_xport_zeros(table, source, 0, 8, [{"npos": 0, "field_length": 8}])
    assert table["INDFMPIR"].iloc[0] == 2.0**-260


def test_report_flags_range_anomalies_and_reference_mismatches_without_excluding_rows():
    ohq = pd.DataFrame({"SEQN": [1, 2], "OHQ850": [1, 2]})
    for name in PREDICTORS:
        ohq[name] = [1, 2]
    ohq["RIDAGEYR"] = [30, 80]
    ohq["OHQ870"] = [9, 99]
    ohq["OHQ030"] = [7, 77]
    ohq["SMQ020"] = [2, 1]
    ohq["SMQ040"] = [None, 3]
    tables = {"P_OHQ": ohq}
    for module in ("P_DEMO", "P_SMQ", "P_DIQ"):
        tables[module] = pd.DataFrame({"SEQN": [1, 2]})
    report = build_report(tables)
    assert "| P_OHQ rows | 14986 | 2 | MISMATCH |" in report
    assert "| OHQ850 valid (1 or 2) | 7817 | 2 | MISMATCH |" in report
    assert "Yes (1): 1 (50.00% of valid labels)" in report
    assert "OHQ870 non-special responses outside the project's integer 0–7 rule: 1" in report
    assert "| OHQ870 | 0 | 77: 0, 99: 1 |" in report
    assert "| OHQ030 | 0 | 77: 1, 99: 0 |" in report
    assert "SMQ020=No: 1" in report
    assert "Rows after all three left joins: 2" in report
    assert all(f"| {name} |" in report for name in PREDICTORS)
