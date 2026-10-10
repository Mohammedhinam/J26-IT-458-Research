"""Synthetic selection, fold fitting, metric and failure checks; no NHANES data."""

from io import BytesIO
import json
import struct
import warnings

import numpy as np
import pandas as pd
from pandas.io.sas import sas_xport
import pytest
from sklearn.exceptions import ConvergenceWarning
from sklearn.model_selection import StratifiedKFold

from src.tabular import baseline_nhanes as baseline
from src.tabular.preprocess_nhanes import CAT_CODES, FEATURES, NUMERIC


def synthetic_inputs(n=50):
    x = pd.DataFrame(index=pd.Index(range(100, 100+n), name="SEQN"))
    for name in NUMERIC:
        x[name] = np.arange(n, dtype=float)
    for name, codes in CAT_CODES.items():
        x[name] = str(codes[0])
    x.loc[x.index[::4], "INDFMPIR"] = np.nan
    y = pd.Series([0, 1] * (n // 2), index=x.index)
    return x.loc[:, list(FEATURES)], y


def synthetic_xpt(path):
    """Minimal XPORT with four fabricated IDs, zero days and unreadable sentinels."""
    stamp = "01JAN26:00:00:00"
    cards = [
        sas_xport._correct_line1,
        "SAS     SAS     SASLIB".ljust(24) + "9.4".ljust(8) + "TEST".ljust(8) + " "*24 + stamp,
        stamp.ljust(80),
        sas_xport._correct_header1 + "140  ",
        sas_xport._correct_header2,
        "SAS".ljust(8) + "TEST".ljust(8) + "SASDATA".ljust(8) + "9.4".ljust(8) + "TEST".ljust(8) + " "*24 + stamp,
        stamp + " "*64,
    ]
    namestr = list("HEADER RECORD*******NAMESTR HEADER RECORD!!!!!!!000000000000000000000000000000  ")
    namestr[54:58] = "0003"
    cards.append("".join(namestr))
    header = "".join(cards).encode()
    fields = []
    for number, (name, kind, length, offset) in enumerate(
        [(b"SEQN", 1, 8, 0), (b"OHQ870", 1, 8, 8), (b"PAD", 2, 72, 16)], start=1
    ):
        fields.append(struct.pack(">hhhh8s40s8shhh2s8shhl52s", kind, 0, length, number,
                                  name.ljust(8), b" "*40, b" "*8, 0, 0, 0, b"\x00"*2,
                                  b" "*8, 0, 0, offset, b"\x00"*52))
    header += b"".join(fields).ljust(480, b" ") + sas_xport._correct_obs_header.encode()
    rows = []
    for value in range(1, 5):
        identifier = bytes([0x41, value << 4]) + b"\x00"*6
        days = b"\x00"*8 if value == 3 else bytes([0x41, 0x10]) + b"\x00"*6
        rows.append(identifier + days + b" "*72)
    payload = b"".join(rows)
    path.write_bytes(header + payload + b" "*(-len(payload) % 80))
    return len(header), 88


def test_selective_xpt_reads_only_development_payload_and_repairs_original_zero(tmp_path):
    source = tmp_path / "synthetic.xpt"
    start, width = synthetic_xpt(source)
    original = source.read_bytes()
    selected_rows = {0, 2}

    class GuardedBytes(BytesIO):
        def read(self, size=-1):
            position = self.tell()
            if position >= start:
                row, offset = divmod(position-start, width)
                # For other participants only SEQN linkage bytes may be read.
                assert row in selected_rows or (offset == 0 and size == 8)
            return super().read(size)

    class GuardedPath:
        def __fspath__(self):
            return str(source)

        def open(self, mode):
            assert mode == "rb"
            return GuardedBytes(original)

    selected = baseline.read_development_xpt(GuardedPath(), [1, 3])
    assert selected["SEQN"].tolist() == [1, 3]
    assert selected.index.tolist() == [0, 2]
    assert selected["OHQ870"].tolist() == [1, 0]
    assert selected.attrs["zero_decode_repairs"] == {"OHQ870": 1}
    assert source.read_bytes() == original


@pytest.mark.parametrize("development,held_out", [([1, 1], [2]), ([1], [1]), ([], [2])])
def test_bad_frozen_membership_fails_before_loading_predictors(tmp_path, monkeypatch, development, held_out):
    manifest = tmp_path / "split.json"
    manifest.write_text(json.dumps({"seed": 42, "test_size": 0.2,
                                    "development": development, "held_out": held_out}))
    def forbidden(*args):
        pytest.fail("Invalid split must fail before XPT access")
    monkeypatch.setattr(baseline, "read_development_xpt", forbidden)
    with pytest.raises(ValueError):
        baseline.load_development(manifest, tmp_path)


def test_fresh_fold_pipelines_fit_training_medians_and_oof_prior_only(monkeypatch):
    x, y = synthetic_inputs()
    original = x.copy(deep=True)
    fitted = []
    factory = baseline.make_baseline
    def capture(name):
        pipeline = factory(name)
        fitted.append((name, pipeline))
        return pipeline
    monkeypatch.setattr(baseline, "make_baseline", capture)
    metrics, fold_rows, predictions = baseline.run_oof(x, y)
    splits = list(StratifiedKFold(5, shuffle=True, random_state=42).split(x, y))
    assert len(fitted) == 10 and len({id(p) for _, p in fitted}) == 10
    assert sum(row[3] for row in fold_rows) == len(x)
    for fold, (train, validation) in enumerate(splits):
        expected = x.iloc[train][list(NUMERIC)].median().to_numpy()
        for name, pipeline in fitted[fold*2:fold*2+2]:
            imputer = pipeline.named_steps["preprocess"].named_transformers_["numeric"].named_steps["impute"]
            np.testing.assert_allclose(imputer.statistics_, expected)
            assert pipeline.named_steps["preprocess"].n_features_in_ == 12
            assert np.isfinite(predictions[name][validation]).all()
        np.testing.assert_allclose(predictions[baseline.MODELS[0]][validation], y.iloc[train].mean())
    assert all(0 <= scores["AUROC"] <= 1 for scores in metrics.values())
    assert len(next(iter(predictions.values()))) == len(y)
    pd.testing.assert_frame_equal(x, original)


def test_known_metrics_and_threshold_ties():
    scores = baseline.score_predictions([0, 0, 1, 1], [0.1, 0.1, 0.9, 0.9])
    assert scores["AUROC"] == scores["PR-AUC (trapezoidal)"] == scores["Average precision"] == 1
    assert scores["Brier"] == pytest.approx(0.01)
    tied = baseline.score_predictions([0, 0, 1, 1], [0.1, 0.5, 0.5, 0.9])
    assert (tied["TN"], tied["FP"], tied["FN"], tied["TP"]) == (1, 1, 0, 2)
    assert tied["Sensitivity @0.50"] == 1 and tied["Specificity @0.50"] == 0.5
    with pytest.raises(ValueError):
        baseline.score_predictions([0, 1], [0.1, np.nan])


def test_reproducible_oof_and_identifier_or_label_inputs_rejected():
    x, y = synthetic_inputs()
    first = baseline.run_oof(x, y)[2]
    second = baseline.run_oof(x, y)[2]
    for name in baseline.MODELS:
        np.testing.assert_array_equal(first[name], second[name])
    with pytest.raises(ValueError, match="allowlist"):
        baseline.run_oof(x.assign(OHQ850=y), y)
    with pytest.raises(ValueError, match="five"):
        baseline.run_oof(x, y*0)


def test_nonconverged_fit_stops_the_experiment(monkeypatch):
    x, y = synthetic_inputs()
    class Nonconvergent:
        def fit(self, *_):
            warnings.warn("synthetic convergence failure", ConvergenceWarning)
    monkeypatch.setattr(baseline, "make_baseline", lambda _: Nonconvergent())
    with pytest.raises(ConvergenceWarning):
        baseline.run_oof(x, y)
