"""Development OOF interview-weight sensitivity; no fitting or held-out access."""

import hashlib
import json

import numpy as np
from sklearn.metrics import auc, average_precision_score, confusion_matrix, precision_recall_curve, roc_auc_score

from .baseline_nhanes import ROOT, DATA_DIR, read_development_xpt, markdown_table
from .pp1_questionnaire_workflow import MANIFEST_HASH, LOCAL


def weighted_metrics(labels, probabilities, weights):
    labels, probabilities, weights = (np.asarray(value) for value in (labels, probabilities, weights))
    if labels.ndim != 1 or probabilities.shape != labels.shape or weights.shape != labels.shape:
        raise ValueError("Aligned one-dimensional arrays required")
    if set(np.unique(labels)) != {0, 1} or not np.isfinite(probabilities).all() or np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError("Valid binary labels and probabilities required")
    if not np.isfinite(weights).all() or np.any(weights <= 0):
        raise ValueError("Positive finite interview weights required")
    # Normalize to mean one: weighted confusion counts sum to development N,
    # not to a claimed US population total from a development subset.
    normalized = weights / weights.mean()
    tn, fp, fn, tp = confusion_matrix(labels, probabilities >= .5, labels=[0, 1], sample_weight=normalized).ravel()
    precision, recall, _ = precision_recall_curve(labels, probabilities, sample_weight=normalized)
    return {"AUROC": float(roc_auc_score(labels, probabilities, sample_weight=normalized)),
            "PR-AUC (trapezoidal)": float(auc(recall, precision)),
            "Average precision": float(average_precision_score(labels, probabilities, sample_weight=normalized)),
            "Brier": float(np.average((labels-probabilities)**2, weights=normalized)),
            "Sensitivity @0.50": float(tp / (tp+fn)), "Specificity @0.50": float(tn / (tn+fp)),
            "normalized_weight_TN": float(tn), "normalized_weight_FP": float(fp),
            "normalized_weight_FN": float(fn), "normalized_weight_TP": float(tp)}


def main():
    report = ROOT / "docs/tabular_survey_sensitivity_v1.md"
    evidence = ROOT / "docs/tabular_survey_sensitivity_v1.json"
    if report.exists() or evidence.exists():
        raise FileExistsError("Preserve the existing sensitivity record")
    manifest_path = ROOT / "data/preprocessing/split_manifest.json"
    raw = manifest_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_HASH:
        raise ValueError("Frozen manifest mismatch")
    development = json.loads(raw)["development"]
    aggregate = json.loads((ROOT / "docs/tabular_pp1_completion_results_v1.json").read_text())
    predictions_path = LOCAL / "development_oof.npz"
    if hashlib.sha256(predictions_path.read_bytes()).hexdigest() != aggregate["oof_sha256"]:
        raise ValueError("Saved development predictions changed")
    with np.load(predictions_path, allow_pickle=False) as saved:
        if saved["SEQN"].tolist() != development:
            raise ValueError("OOF IDs/order differ from frozen development membership")
        labels = saved["y"].copy()
        probabilities = {name: saved[name].copy() for name in aggregate["scores"]}
    # The existing loader reads only selected development payloads; other records
    # supply only linkage bytes needed to skip them, never predictors or labels.
    demo = read_development_xpt(DATA_DIR / "P_DEMO.xpt", development).set_index("SEQN").loc[development]
    design = demo[["WTINTPRP", "SDMVSTRA", "SDMVPSU"]]
    if len(design) != 6251 or design.isna().any().any():
        raise ValueError("Incomplete development survey-design fields")
    weights = design["WTINTPRP"].to_numpy()
    measured = {name: weighted_metrics(labels, p, weights) for name, p in probabilities.items()}
    if manifest_path.read_bytes() != raw:
        raise ValueError("Frozen manifest changed")
    result = {"scope": "descriptive development-only OOF interview-weight sensitivity",
              "n": len(labels), "source": "P_DEMO WTINTPRP", "manifest_sha256": MANIFEST_HASH,
              "oof_sha256": aggregate["oof_sha256"], "strata": int(design["SDMVSTRA"].nunique()),
              "stratum_psu_pairs": int(design[["SDMVSTRA", "SDMVPSU"]].drop_duplicates().shape[0]),
              "weight_min": float(weights.min()), "weight_max": float(weights.max()),
              "weighted_positive_share": float(np.average(labels, weights=weights)), "scores": measured,
              "new_model_fits": 0, "held_out_payloads_accessed": False,
              "population_inference": False, "design_based_uncertainty_complete": False}
    evidence.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    names = list(next(iter(measured.values())))[:6]
    output = ["# Development OOF survey-weight sensitivity — 2026-10-15", "",
              "Reused six saved predictions; zero model fits. Selective development-only P_DEMO linkage reused. Frozen manifest/predictions unchanged; no held-out payloads read.", "",
              markdown_table(("Setting", *names), [(name, *[f"{scores[key]:.6f}" for key in names]) for name, scores in measured.items()]), "",
              f"N={len(labels)}; WTINTPRP positive/finite for all rows. Weighted positive share={result['weighted_positive_share']:.6f}. Design coverage: {result['strata']} strata / {result['stratum_psu_pairs']} stratum-PSU pairs.",
              "Weights normalized to mean one; normalized weighted confusion counts in JSON are not integer participant counts or population totals. Point sensitivity analysis only: not survey-weighted training, new tuning, final evaluation or nationally representative inference. Complex-design variance and appropriate domain analysis remain pending; respondent bootstrap intervals cannot replace them.",
              "Source: [CDC pre-pandemic demographics and interview weights](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm); signed proposal §3.5.", ""]
    report.write_text("\n".join(output))
    print("\n".join(output))


if __name__ == "__main__":
    main()
