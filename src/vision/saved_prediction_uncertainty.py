"""Conditional uncertainty of saved v2/v3 predictions; no pixels or inference."""

import hashlib
import json
from pathlib import Path
import zipfile

import numpy as np
from scipy.stats import beta
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score


ROOT = Path(__file__).resolve().parents[2]


def measurements(labels, probabilities):
    labels, probabilities = np.asarray(labels), np.asarray(probabilities)
    if probabilities.shape != (len(labels), 4) or not np.isfinite(probabilities).all():
        raise ValueError("Expected finite four-grade probability rows")
    if not np.isin(labels, (1, 2, 3, 4)).all() or np.any(probabilities < 0) or not np.allclose(probabilities.sum(1), 1, atol=1e-6):
        raise ValueError("Invalid grade/probability mapping")
    predicted = probabilities.argmax(axis=1) + 1
    return {"accuracy": float(accuracy_score(labels, predicted)),
            "macro_f1": float(f1_score(labels, predicted, labels=[1, 2, 3, 4], average="macro", zero_division=0)),
            "ordinal_mae": float(np.mean(np.abs(labels - predicted))),
            "macro_auroc": float(np.mean([roc_auc_score(labels == grade, probabilities[:, grade-1]) for grade in (1, 2, 3, 4)]))}


def exact_recall_interval(correct, support):
    """Conditional binomial interval; single samples must not look certain."""
    if support < 1 or not 0 <= correct <= support:
        raise ValueError("Valid nonzero class support required")
    lower = 0.0 if correct == 0 else float(beta.ppf(.025, correct, support - correct + 1))
    upper = 1.0 if correct == support else float(beta.ppf(.975, correct + 1, support - correct))
    return [lower, upper]


def paired_bootstrap(labels, old, new, repetitions=1000):
    labels = np.asarray(labels)
    strata = [np.flatnonzero(labels == grade) for grade in (1, 2, 3, 4)]
    if not all(len(group) for group in strata) or repetitions < 1:
        raise ValueError("All four supported grades and positive repetitions required")
    measurements(labels, old)
    measurements(labels, new)
    generator = np.random.default_rng(42)
    draws = []
    names = tuple(measurements(labels, old))
    for _ in range(repetitions):
        indices = np.concatenate([generator.choice(group, len(group), replace=True) for group in strata])
        before, after = measurements(labels[indices], old[indices]), measurements(labels[indices], new[indices])
        draws.append([after[key] - before[key] for key in names])
    return dict(zip(names, np.quantile(draws, [.025, .975], axis=0).T.tolist()))


def main():
    output = ROOT / "docs/vision_saved_prediction_uncertainty_v1.json"
    report = ROOT / "docs/vision_saved_prediction_uncertainty_v1.md"
    if output.exists() or report.exists():
        raise FileExistsError("Preserve existing uncertainty evidence")
    prior = json.loads((ROOT / "docs/vision_grade2_v2_v3_diagnostic_v1.json").read_text())
    rows = {}
    for version in ("v2", "v3"):
        source = prior["sources"][version]
        # Read one already-verified small JSON member; no checkpoint/image member.
        with zipfile.ZipFile(source["path"]) as archive:
            raw = archive.read("validation_predictions_best.json")
        if hashlib.sha256(raw).hexdigest() != source["prediction_payload_sha256_verified"]:
            raise ValueError("Historical saved predictions changed")
        data = json.loads(raw)
        if data["grades"] != [1, 2, 3, 4] or len(data["records"]) != 53:
            raise ValueError("Historical grade/membership mismatch")
        rows[version] = {r["source_record_id"]: r for r in data["records"]}
        if len(rows[version]) != 53 or any(r["original_split"] != "Validation" for r in data["records"]):
            raise ValueError("Expected unique saved Validation predictions")
    if set(rows["v2"]) != set(rows["v3"]):
        raise ValueError("Paired membership differs")
    ids = sorted(rows["v2"])
    labels = np.array([rows["v2"][key]["provisional_mgi_grade"] for key in ids])
    if labels.tolist() != [rows["v3"][key]["provisional_mgi_grade"] for key in ids]:
        raise ValueError("Provisional labels differ")
    probabilities = {v: np.array([rows[v][key]["probabilities_mgi1_to4"] for key in ids]) for v in rows}
    intervals = paired_bootstrap(labels, probabilities["v2"], probabilities["v3"])
    recalls = []
    predicted = probabilities["v3"].argmax(1) + 1
    for grade in (1, 2, 3, 4):
        support = int(np.sum(labels == grade))
        correct = int(np.sum((labels == grade) & (predicted == grade)))
        recalls.append({"grade": grade, "support": support, "correct": correct,
                        "conditional_binomial_95": exact_recall_interval(correct, support)})
    result = {"n": 53, "scope": "saved-prediction conditional uncertainty only",
              "paired_stratified_resamples": 1000, "seed": 42,
              "v3_minus_v2_95": intervals, "v3_recall": recalls,
              "image_independence_assumed_not_verified": True,
              "selection_optimism_corrected": False, "new_training_or_inference": False,
              "original_images_or_test_accessed": False}
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    lines = ["# Saved Vision v2/v3 uncertainty — 2026-10-15", "",
             "Added conditional uncertainty to the completed Grade-2 diagnosis; no new experiment, image decoding, model inference or label adjudication.", "",
             "| Metric | v3 minus v2 conditional 95% interval |", "| --- | --- |"]
    lines += [f"| {name} | {bounds[0]:.6f} to {bounds[1]:.6f} |" for name, bounds in intervals.items()]
    lines += ["", "1,000 paired outcome-stratified resamples of the same 53 saved predictions, seed42. Image sampling assumes independence that remains unverified; fixed-label support and repeated checkpoint/model selection are not accounted for. These are descriptive sensitivity intervals, not final research or clinical confidence bounds.", "",
              "| Grade | Correct / support | Conditional exact-binomial recall interval |", "| --- | --- | --- |"]
    lines += [f"| {r['grade']} | {r['correct']} / {r['support']} | {r['conditional_binomial_95'][0]:.6f} to {r['conditional_binomial_95'][1]:.6f} |" for r in recalls]
    lines += ["", "Grade1 has only one Validation example. Its stratified bootstrap cannot measure class variation; report the broad conditional binomial interval instead, still subject to unverified independence/provisional labels. MGI0 has no supported full-image sample; no MGI0 performance can be estimated.",
              "Keep v1/v2/v3 as exploratory evidence. No email is required to continue the working PP1 software demo, but internet research cannot adjudicate uncertain clinical labels or establish participant identity. The 181 holds remain excluded. Next new real Vision experiment needs an explicit bounded protocol/authorization and Colab; this analysis does not activate one.", ""]
    report.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
