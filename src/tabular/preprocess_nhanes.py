"""Clean NHANES inputs and fit preprocessing on development participants only.

Run with: .venv/bin/python -m src.tabular.preprocess_nhanes
"""

import hashlib
import json

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import MissingIndicator, SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .audit_nhanes import ROOT, PREDICTORS, SPECIAL_CODES, join_valid_outcomes, load_files, markdown_table


SEED = 42
NUMERIC = ("RIDAGEYR", "INDFMPIR", "OHQ870")
CAT_CODES = {
    "RIAGENDR": (1, 2),
    "DMDEDUC2": (1, 2, 3, 4, 5),
    "DMDMARTZ": (1, 2, 3),
    "OHQ030": (1, 2, 3, 4, 5, 6, 7),
    "OHQ845": (1, 2, 3, 4, 5),
    "OHQ860": (1, 2),
    "OHQ835": (1, 2),
    "DIQ010": (1, 2, 3),
    "SMOKING_STATUS": ("fewer_than_100_lifetime", "former", "current"),
}
FEATURES = NUMERIC + tuple(CAT_CODES)
LOCAL_DIR = ROOT / "data" / "preprocessing"


def derive_smoking_status(frame):
    """Use lifetime and follow-up answers, distinguishing structural skips."""
    lifetime = frame["SMQ020"].replace({7: np.nan, 9: np.nan})
    current = frame["SMQ040"].replace({7: np.nan, 9: np.nan})
    status = pd.Series(np.nan, index=frame.index, dtype=object)
    reason = pd.Series("unknown_lifetime_response", index=frame.index, dtype=object)
    no = lifetime.eq(2)
    yes = lifetime.eq(1)
    status.loc[no] = "fewer_than_100_lifetime"
    reason.loc[no] = "fewer_than_100_lifetime"
    status.loc[yes & current.isin((1, 2))] = "current"
    status.loc[yes & current.eq(3)] = "former"
    reason.loc[yes & current.notna()] = "answered_followup"
    reason.loc[yes & current.isna()] = "missing_followup"
    inconsistent = ~yes & current.notna()
    status.loc[inconsistent] = np.nan
    reason.loc[inconsistent] = "inconsistent_answers"
    skipped = no & frame["SMQ040"].isna()
    return status, reason, skipped


def clean_cohort(cohort):
    """Apply fixed rules without estimating values or changing the audit view."""
    required = ["SEQN", "OHQ850", *PREDICTORS]
    absent = [name for name in required if name not in cohort]
    if absent:
        raise ValueError("Missing required columns: " + ", ".join(absent))
    if cohort["SEQN"].isna().any() or cohort["SEQN"].duplicated().any():
        raise ValueError("SEQN must be unique and non-missing before participant splitting")
    if not cohort["OHQ850"].isin((1, 2)).all():
        raise ValueError("OHQ850 must contain only valid labels 1 and 2")

    cleaned = cohort.copy(deep=True)
    special_counts = {}
    # Special codes differ across fields. Never apply a blanket 7/9 rule.
    for name, codes in SPECIAL_CODES.items():
        mask = cleaned[name].isin(codes)
        special_counts[name] = int(mask.sum())
        cleaned[name] = cleaned[name].mask(mask)

    # Fail on unexpected codes instead of silently inventing categories.
    valid_codes = {name: codes for name, codes in CAT_CODES.items() if name != "SMOKING_STATUS"}
    valid_codes.update({"SMQ020": (1, 2), "SMQ040": (1, 2, 3)})
    for name, codes in valid_codes.items():
        if (cleaned[name].notna() & ~cleaned[name].isin(codes)).any():
            raise ValueError(f"Unexpected non-special code in {name}")
    income = cleaned["INDFMPIR"]
    if (income.notna() & ~income.between(0, 5)).any():
        raise ValueError("INDFMPIR must be missing or between 0 and 5")

    # Age eligibility is logged separately; missing predictors do not drop rows.
    eligible = cleaned["RIDAGEYR"].ge(30).fillna(False)
    days = cleaned["OHQ870"]
    unusual_days = days.notna() & (~days.between(0, 7) | days.mod(1).ne(0))
    review = cohort.loc[eligible & unusual_days].copy()
    review["exclusion_reason"] = "OHQ870_outside_integer_0_to_7"
    main = cleaned.loc[eligible & ~unusual_days].copy()
    # Derive from original responses so a refusal is distinguishable from a skip.
    smoking, reasons, skipped = derive_smoking_status(cohort.loc[main.index])
    main["SMOKING_STATUS"] = smoking
    main["smoking_status_reason"] = reasons
    main["SMQ040_skipped_by_design"] = skipped
    log = {
        "audit_valid_labels": len(cohort),
        "age_exclusions": int((~eligible).sum()),
        "cleaning_day_exclusions": len(review),
        "main_cohort": len(main),
        "special_codes_to_missing": special_counts,
    }
    return main, review, log


def model_inputs(frame):
    """Select predictors explicitly; identifiers, outcomes and metadata stay out."""
    x = frame.loc[:, list(FEATURES)].copy()
    for name in CAT_CODES:
        values = x[name]
        present = values.notna()
        encoded = pd.Series(np.nan, index=values.index, dtype=object)
        if name == "SMOKING_STATUS":
            encoded.loc[present] = values.loc[present]
        else:
            encoded.loc[present] = values.loc[present].astype(int).astype(str)
        x[name] = encoded
    y = frame["OHQ850"].map({1: 1, 2: 0}).astype(int)
    return x, y


def split_participants(main, manifest_path=None, seed=SEED):
    """Freeze a stratified participant split; no preprocessing is fitted here."""
    if main["SEQN"].isna().any() or main["SEQN"].duplicated().any():
        raise ValueError("SEQN must be unique and non-missing")
    ordered = main.sort_values("SEQN").set_index("SEQN", drop=False)
    identity = [[int(seqn), int(label)] for seqn, label in zip(ordered["SEQN"], ordered["OHQ850"])]
    fingerprint = hashlib.sha256(json.dumps(identity).encode()).hexdigest()
    if manifest_path is not None and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        if manifest["seed"] != seed or manifest["test_size"] != 0.2 or manifest["cohort_sha256"] != fingerprint:
            raise ValueError("Frozen split does not match cohort/settings; refusing to overwrite")
    else:
        development, held_out = train_test_split(
            ordered.index.to_numpy(), test_size=0.2, random_state=seed,
            stratify=ordered["OHQ850"],
        )
        manifest = {
            "seed": seed, "test_size": 0.2, "cohort_sha256": fingerprint,
            "development": [int(value) for value in development],
            "held_out": [int(value) for value in held_out],
        }

    dev_ids, test_ids = manifest["development"], manifest["held_out"]
    if len(set(dev_ids)) != len(dev_ids) or len(set(test_ids)) != len(test_ids):
        raise ValueError("Duplicate participant IDs in split manifest")
    if set(dev_ids) & set(test_ids) or set(dev_ids) | set(test_ids) != set(ordered.index):
        raise ValueError("Split membership must be disjoint and cover the cohort")
    if manifest_path is not None and not manifest_path.exists():
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with manifest_path.open("x", encoding="utf-8") as output:
            json.dump(manifest, output, indent=2)
    return ordered.loc[dev_ids].copy(), ordered.loc[test_ids].copy(), manifest


def make_preprocessor():
    """Build fresh sklearn steps for development fitting or each later CV fold."""
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
        ("scale", StandardScaler()),
    ])
    categories = [[str(code) for code in codes] + ["unknown"] for codes in CAT_CODES.values()]
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="unknown", keep_empty_features=True)),
        ("encode", OneHotEncoder(categories=categories, handle_unknown="error", sparse_output=False)),
    ])
    return ColumnTransformer([
        ("numeric", numeric, list(NUMERIC)),
        ("missing", MissingIndicator(features="all"), list(NUMERIC)),
        ("categorical", categorical, list(CAT_CODES)),
    ], remainder="drop")


def main():
    # Reuse audited loading/joining; never regenerate or overwrite the audit report.
    _, cohort, _ = join_valid_outcomes(load_files())
    cleaned, review, log = clean_cohort(cohort)
    development, held_out, manifest = split_participants(cleaned, LOCAL_DIR / "split_manifest.json")
    x_dev, y_dev = model_inputs(development)
    preprocessor = make_preprocessor()
    matrix = preprocessor.fit_transform(x_dev)
    if not np.isfinite(matrix).all():
        raise ValueError("Development preprocessing produced non-finite values")
    assert len(cleaned) == len(development) + len(held_out)
    # Save participant-level review details locally, never in the committed report.
    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    review[["SEQN", "OHQ850", "OHQ870", "exclusion_reason"]].to_csv(
        LOCAL_DIR / "ohq870_sensitivity_review.csv", index=False,
    )
    medians = preprocessor.named_transformers_["numeric"].named_steps["impute"].statistics_
    smoking_counts = cleaned["SMOKING_STATUS"].fillna("unknown").value_counts().items()
    missing_counts = [(name, int(cleaned[name].isna().sum())) for name in FEATURES]
    reasons = cleaned["smoking_status_reason"].value_counts().items()
    report = [
        "# Tabular cleaning and preprocessing verification — 2026-10-10", "",
        "Command: `.venv/bin/python -m src.tabular.preprocess_nhanes`. Rules: `docs/tabular_preprocessing_rules.md`.",
        "The existing audit report is preserved. No classifier was trained, no held-out predictions/metrics were generated, and held-out predictors were not transformed.", "",
        markdown_table(("Stage", "Rows"), [
            ("Audited valid OHQ850 view", log["audit_valid_labels"]),
            ("Age exclusions", log["age_exclusions"]),
            ("Non-special OHQ870 outside integer 0–7 excluded", log["cleaning_day_exclusions"]),
            ("Main cleaned cohort", len(cleaned)),
            ("Development", len(development)), ("Reserved held-out", len(held_out)),
        ]), "",
        f"Excluded OHQ870 values/counts: {review['OHQ870'].value_counts().to_dict()}. Participant details are stored only in ignored `data/preprocessing/ohq870_sensitivity_review.csv`.",
        f"Main cohort Yes: {int(cleaned['OHQ850'].eq(1).sum())}; No: {int(cleaned['OHQ850'].eq(2).sum())}. Development positive labels: {int(y_dev.sum())}.",
        f"Seed: {manifest['seed']}; held-out fraction: {manifest['test_size']}; split overlap: {len(set(manifest['development']) & set(manifest['held_out']))} participants.",
        "Membership is frozen locally in ignored `data/preprocessing/split_manifest.json`. No split IDs are committed.", "",
        "## Special-code replacements (before age/cleaning-day exclusions)", "",
        markdown_table(("Field", "Special codes mapped to missing"), log["special_codes_to_missing"].items()), "",
        "## Smoking derivation", "",
        markdown_table(("Derived status", "Rows"), smoking_counts), "",
        markdown_table(("Derivation/review reason", "Rows"), reasons), "",
        f"SMQ040 skipped by design: {int(cleaned['SMQ040_skipped_by_design'].sum())}. These rows have a known fewer-than-100 lifetime category, not imputed current-smoking responses.", "",
        "## Missing inputs after cleaning, before imputation", "",
        markdown_table(("Conceptual input", "Missing"), missing_counts), "",
        f"Conceptual inputs: {len(FEATURES)}; encoded columns: {matrix.shape[1]}; development matrix: {matrix.shape[0]} × {matrix.shape[1]}; all finite: {bool(np.isfinite(matrix).all())}.",
        "Three numeric inputs plus three missing indicators and codebook-defined categorical/unknown one-hot columns are used. SEQN, OHQ850, survey fields, raw smoking fields and review metadata are absent from the feature matrix.", "",
        "## Development-fitted numeric medians", "",
        markdown_table(("Field", "Imputer median/fallback", "Entire development column missing"), [
            (name, float(median), bool(x_dev[name].isna().all())) for name, median in zip(NUMERIC, medians)
        ]), "",
        "Encoded feature names: " + ", ".join(preprocessor.get_feature_names_out()), "",
        "Next: a fresh preprocessing + regularised logistic regression Pipeline fitted within development folds; compare a training-rate baseline using development-only validation. Keep final held-out evaluation deferred.", "",
    ]
    output = "\n".join(report)
    (ROOT / "docs" / "tabular_preprocessing.md").write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
