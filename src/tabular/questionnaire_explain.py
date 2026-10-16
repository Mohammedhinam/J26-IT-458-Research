"""Development-reference TreeSHAP and constrained questionnaire re-inference.

No file loading, training, held-out access or clinical decisions occur on import.
"""

import hashlib
import math

import joblib
import numpy as np
import pandas as pd
import shap
from scipy.special import expit
from xgboost import DMatrix

from .preprocess_nhanes import CAT_CODES, FEATURES, NUMERIC


NOTICE = (
    "Development-only prototype: probability of self-reported previous gum treatment. "
    "Not current disease, diagnosis, future risk or a treatment-effect estimate. "
    "NHANES US definitions; use fictional profiles for demonstrations."
)
SCENARIO_NOTICE = (
    "Changing an answer changes the model output, not a person's actual treatment history. "
    "This is model sensitivity, not evidence that a behaviour improves health."
)
TOLERANCE = 1e-5
SUPPORT_WARNING_COUNT = 20  # UI heuristic only; not a validated reliability cutoff.
EDITABLE = frozenset(("SMOKING_STATUS", "OHQ870"))
FEATURE_LABELS = {
    "RIDAGEYR": "Age (80 means 80 or older)",
    "INDFMPIR": "US family income-to-poverty ratio",
    "OHQ870": "Interdental-cleaning days in the past week",
    "RIAGENDR": "Recorded sex category",
    "DMDEDUC2": "Adult education (NHANES categories)",
    "DMDMARTZ": "Marital status",
    "OHQ030": "Time since last dental visit",
    "OHQ845": "Self-rated teeth and gum health",
    "OHQ860": "Previously told of bone loss around teeth",
    "OHQ835": "Thinks they might have gum disease",
    "DIQ010": "Self-reported diabetes category",
    "SMOKING_STATUS": "Smoking status",
}
EXAMPLE_PROFILE = dict(
    RIDAGEYR=55, INDFMPIR=2.0, OHQ870=2, RIAGENDR="1", DMDEDUC2="4",
    DMDMARTZ="1", OHQ030="1", OHQ845="3", OHQ860="2", OHQ835="2",
    DIQ010="2", SMOKING_STATUS="current",
)


def validate_profile(profile):
    """Use codebook values, never accept outcome/ID fields or implicit coercions."""
    if not isinstance(profile, dict) or set(profile) != set(FEATURES):
        raise ValueError("Provide exactly the 12 input fields; outcomes and IDs are forbidden")
    result = {}
    for field in FEATURES:
        value = profile[field]
        if value is None or value == "unknown":
            if field == "RIDAGEYR":
                raise ValueError("Age is required to confirm adult eligibility")
            result[field] = None
            continue
        if isinstance(value, bool):
            raise ValueError(f"Boolean is not a valid answer for {field}")
        if field in NUMERIC:
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{field} must be a finite number or explicit unknown")
            low, high = {"RIDAGEYR": (30, 80), "INDFMPIR": (0, 5), "OHQ870": (0, 7)}[field]
            if not low <= value <= high or (field != "INDFMPIR" and value != int(value)):
                raise ValueError(f"{field} is outside its codebook/project range")
            result[field] = float(value) if field == "INDFMPIR" else int(value)
        else:
            # The API uses explicit strings for categories; floats are not codes.
            legal = tuple(str(code) for code in CAT_CODES[field])
            if not isinstance(value, str) or value not in legal:
                raise ValueError(f"Unsupported category for {field}")
            result[field] = value
    return result


def profile_frame(profile):
    canonical = validate_profile(profile)
    return pd.DataFrame([{key: np.nan if value is None else value
                          for key, value in canonical.items()}], columns=FEATURES)


def encoded_groups(names):
    """Group encoded columns and missing flags without dropping any contribution."""
    groups = []
    for name in names:
        matches = [field for field in FEATURES if name in (
            f"numeric__{field}", f"missing__missingindicator_{field}"
        ) or name.startswith(f"categorical__{field}_")]
        if len(matches) != 1:
            raise ValueError(f"Unrecognized or ambiguous encoded feature: {name}")
        groups.append(FEATURES.index(matches[0]))
    return groups


def explain_frame(model, frame):
    """Validate exact TreeSHAP against raw margins, probabilities and native SHAP."""
    if tuple(frame.columns) != FEATURES or frame.empty:
        raise ValueError("Explanation requires the full existing input schema")
    processor, classifier = model.named_steps["preprocess"], model.named_steps["classifier"]
    if classifier.get_params()["objective"] != "binary:logistic" or list(classifier.classes_) != [0, 1]:
        raise ValueError("Expected the binary previous-treatment XGBoost model")
    matrix = processor.transform(frame)
    if not np.isfinite(matrix).all():
        raise ValueError("Non-finite transformed inputs")
    names = processor.get_feature_names_out()
    explanation = shap.TreeExplainer(
        classifier, model_output="raw", feature_perturbation="tree_path_dependent",
    )(matrix, check_additivity=True)
    values = np.asarray(explanation.values, dtype=float)
    bases = np.asarray(explanation.base_values, dtype=float).reshape(-1)
    if values.shape != matrix.shape or bases.shape != (len(frame),):
        raise ValueError("Unexpected TreeSHAP output shape")
    margin = classifier.predict(matrix, output_margin=True)
    probability = model.predict_proba(frame)[:, 1]
    native = classifier.get_booster().predict(DMatrix(matrix), pred_contribs=True, approx_contribs=False)
    grouped = np.zeros((len(frame), len(FEATURES)), dtype=float)
    for column, group in enumerate(encoded_groups(names)):
        grouped[:, group] += values[:, column]
    errors = {
        "margin_max_abs_error": float(np.max(np.abs(bases + grouped.sum(axis=1) - margin))),
        "probability_max_abs_error": float(np.max(np.abs(expit(bases + grouped.sum(axis=1)) - probability))),
        "native_shap_max_abs_error": float(np.max(np.abs(values - native[:, :-1]))),
        "native_base_max_abs_error": float(np.max(np.abs(bases - native[:, -1]))),
    }
    if (not np.isfinite(values).all() or not np.isfinite(bases).all()
            or not np.isfinite(probability).all()
            or any(not math.isfinite(error) or error > TOLERANCE for error in errors.values())):
        raise ValueError("SHAP output failed finite-value/additivity/native verification")
    return {"probability": probability, "base_log_odds": bases, "contributions": grouped,
            "raw_log_odds": margin, "checks": errors, "encoded_features": len(names)}


def _category(value):
    return "unknown" if pd.isna(value) else str(value)


def _pair(smoking, days):
    day = "unknown" if pd.isna(days) else str(int(days))
    return _category(smoking) + "|" + day


def fit_support(frame):
    """Keep aggregate development counts only; no respondent IDs or outcomes."""
    if tuple(frame.columns) != FEATURES or frame.empty:
        raise ValueError("Support needs the full development input schema")
    categories = {field: frame[field].map(_category).value_counts().to_dict() for field in CAT_CODES}
    pairs = pd.Series([_pair(s, d) for s, d in zip(frame["SMOKING_STATUS"], frame["OHQ870"])])
    ranges = {}
    for field in NUMERIC:
        present = frame[field].dropna()
        ranges[field] = None if present.empty else [float(present.min()), float(present.max())]
    return {"n": len(frame), "categories": categories, "pairs": pairs.value_counts().to_dict(),
            "numeric_ranges": ranges}


def support_warnings(profile, support):
    warnings = []
    for field, value in profile.items():
        if value is None:
            warnings.append(f"{field}: unknown answer uses development-fitted missing handling")
        elif field in CAT_CODES and support["categories"][field].get(str(value), 0) < SUPPORT_WARNING_COUNT:
            warnings.append(f"{field}: fewer than {SUPPORT_WARNING_COUNT} development examples of this category")
        elif field in NUMERIC:
            bounds = support["numeric_ranges"][field]
            if bounds is None or not bounds[0] <= value <= bounds[1]:
                warnings.append(f"{field}: outside observed development range")
    count = int(support["pairs"].get(_pair(profile["SMOKING_STATUS"], profile["OHQ870"]), 0))
    if count < SUPPORT_WARNING_COUNT:
        warnings.append(f"Smoking/cleaning pair has {count} development examples; sparse-support heuristic")
    return {"warnings": warnings, "smoking_cleaning_pair_count": count,
            "warning_count_threshold": SUPPORT_WARNING_COUNT,
            "scope": "Marginal and two-input pair coverage only; full-profile reliability is unvalidated"}


class QuestionnairePrototype:
    """Use one fitted development reference for prediction, explanation and reset."""

    def __init__(self, model, support, provenance):
        self.model, self.support, self.provenance = model, support, dict(provenance)
        self.model_id = hashlib.sha256(joblib.hash(model).encode()).hexdigest()

    def predict(self, profile):
        canonical = validate_profile(profile)
        result = explain_frame(self.model, profile_frame(canonical))
        contributions = [
            {"field": field, "label": FEATURE_LABELS[field], "value": canonical[field],
             "contribution_log_odds": float(result["contributions"][0, i])}
            for i, field in enumerate(FEATURES)
        ]
        return {
            "notice": NOTICE, "model_id": self.model_id,
            "model_role": "Full XGBoost A development reference; not final model selection",
            "outcome": "self_reported_previous_gum_treatment",
            "probability": float(result["probability"][0]), "calibration": "raw, not separately calibrated",
            "base_log_odds": float(result["base_log_odds"][0]),
            "raw_log_odds": float(result["raw_log_odds"][0]),
            "contributions": contributions, "checks": result["checks"],
            "shap_method": "exact tree-path-dependent, encoded columns summed by original input",
            "support": support_warnings(canonical, self.support), "profile": canonical,
        }

    def simulate(self, original, changes, expected_model_id):
        """A new scenario always starts from the same immutable original profile."""
        if expected_model_id != self.model_id:
            raise ValueError("Model version changed; restart the demonstration")
        if not isinstance(changes, dict) or not set(changes) <= EDITABLE:
            raise ValueError("Only smoking status and interdental-cleaning days may change")
        before = validate_profile(original)
        after = validate_profile({**before, **changes})
        if "OHQ870" in changes and after["OHQ870"] is None:
            raise ValueError("Choose an explicit scenario cleaning value from 0 to 7")
        old, new = before["SMOKING_STATUS"], after["SMOKING_STATUS"]
        if new != old and (old not in ("former", "current") or new not in ("former", "current")):
            raise ValueError("A scenario cannot rewrite or invent lifetime smoking history")
        baseline, scenario = self.predict(before), self.predict(after)
        return {"notice": SCENARIO_NOTICE, "original": baseline, "scenario": scenario,
                "changed_fields": [key for key in FEATURES if before[key] != after[key]],
                "probability_difference": scenario["probability"] - baseline["probability"],
                "is_reset": not changes}

    def reset(self, original, expected_model_id):
        return self.simulate(original, {}, expected_model_id)
