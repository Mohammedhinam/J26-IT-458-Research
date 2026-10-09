"""Audit the four NHANES XPT files without modelling or cleaning rows."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
REPORT_PATH = ROOT / "docs" / "nhanes_audit.md"

FILES = ("P_DEMO", "P_OHQ", "P_SMQ", "P_DIQ")
PREDICTORS = (
    "RIDAGEYR",
    "RIAGENDR",
    "DMDEDUC2",
    "DMDMARTZ",
    "INDFMPIR",
    "OHQ030",
    "OHQ845",
    "OHQ860",
    "OHQ870",
    "OHQ835",
    "SMQ020",
    "SMQ040",
    "DIQ010",
)
NUMERIC_PREDICTORS = {"RIDAGEYR", "INDFMPIR"}

# These are documented refusal, don't-know, or out-of-range codes for the
# individual fields. OHQ030 code 7 is a valid response, not a special code.
SPECIAL_CODES = {
    "RIAGENDR": (7, 9),
    "DMDEDUC2": (7, 9),
    "DMDMARTZ": (77, 99),
    "OHQ030": (77, 99),
    "OHQ845": (7, 9),
    "OHQ860": (7, 9),
    "OHQ870": (8, 9, 77, 99),
    "OHQ835": (7, 9),
    "SMQ020": (7, 9),
    "SMQ040": (7, 9),
    "DIQ010": (7, 9),
}


def markdown_table(headers, rows):
    """Format simple rows as a Markdown table."""
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def counts_with_missing(series):
    """Show category counts while retaining missing values in the output."""
    counts = series.value_counts(dropna=False, sort=False)
    return ", ".join(
        f"{('NaN' if pd.isna(value) else value)}: {count}"
        for value, count in counts.items()
    ) or "None"


def load_files():
    """Read each requested XPORT file and verify its linkage key."""
    tables = {}
    for file_name in FILES:
        file_path = DATA_DIR / f"{file_name}.xpt"
        if not file_path.is_file():
            raise FileNotFoundError(f"Required input file not found: {file_path}")
        tables[file_name] = pd.read_sas(file_path, format="xport")
        if "SEQN" not in tables[file_name].columns:
            raise ValueError(f"{file_name} is missing the required SEQN column")
    return tables


def file_audit(tables):
    """Summarize input dimensions and duplicate participant IDs."""
    rows = []
    for name, table in tables.items():
        duplicate_rows = int(table["SEQN"].duplicated(keep=False).sum())
        unique_ids = int(table["SEQN"].nunique(dropna=True))
        missing_ids = int(table["SEQN"].isna().sum())
        rows.append((name, len(table), len(table.columns), duplicate_rows, unique_ids, missing_ids))
    return rows


def join_valid_outcomes(tables):
    """Left-join the valid-label OHQ rows and keep missing module matches."""
    ohq = tables["P_OHQ"]
    if "OHQ850" not in ohq.columns:
        raise ValueError("P_OHQ is missing the required OHQ850 outcome column")

    # Use only the two valid label codes; this defines the requested audit view.
    valid = ohq.loc[ohq["OHQ850"].isin((1, 2))].copy()
    counts = [("P_OHQ valid OHQ850", len(valid), int(valid["SEQN"].nunique(dropna=True)))]

    cohort = valid
    for module_name in ("P_DEMO", "P_SMQ", "P_DIQ"):
        module = tables[module_name]
        # pandas matches missing keys to each other, unlike a SQL join. Exclude
        # unkeyed module rows so missing SEQN values remain unmatched.
        keyed_module = module.loc[module["SEQN"].notna()]
        before_rows = len(cohort)
        before_ids = int(cohort["SEQN"].nunique(dropna=True))
        cohort = cohort.merge(
            keyed_module,
            on="SEQN",
            how="left",
            suffixes=("", f"_{module_name}"),
        )
        counts.append(
            (
                f"After left join {module_name}",
                len(cohort),
                int(cohort["SEQN"].nunique(dropna=True)),
            )
        )
        if before_ids > int(cohort["SEQN"].nunique(dropna=True)):
            raise AssertionError(f"Unique SEQN count fell during the {module_name} left join")
        if len(cohort) < before_rows:
            raise AssertionError(f"Rows were lost during the {module_name} left join")
    return valid, cohort, counts


def predictor_audit(cohort):
    """Summarize missing, special, category, or numeric range values."""
    missing_columns = [name for name in PREDICTORS if name not in cohort.columns]
    if missing_columns:
        raise ValueError("Predictor columns missing after joins: " + ", ".join(missing_columns))

    lines = []
    for name in PREDICTORS:
        values = cohort[name]
        missing = int(values.isna().sum())
        special_codes = SPECIAL_CODES.get(name, ())
        special_counts = [
            f"{code}: {int(values.eq(code).sum())}" for code in special_codes
        ]
        special_text = ", ".join(special_counts) if special_counts else "None specified"

        if name in NUMERIC_PREDICTORS:
            present = values.dropna()
            minimum = present.min() if not present.empty else "None"
            maximum = present.max() if not present.empty else "None"
            details = f"min={minimum}; max={maximum}"
        else:
            details = counts_with_missing(values)

        lines.append((name, missing, special_text, details))
    return lines


def build_report(tables):
    """Build the audit report using only values read from the input files."""
    ohq = tables["P_OHQ"]
    if "OHQ850" not in ohq.columns:
        raise ValueError("P_OHQ is missing the required OHQ850 outcome column")

    labels = ohq["OHQ850"]
    yes_count = int(labels.eq(1).sum())
    no_count = int(labels.eq(2).sum())
    valid_count = yes_count + no_count
    yes_share = (100 * yes_count / valid_count) if valid_count else 0
    no_share = (100 * no_count / valid_count) if valid_count else 0

    valid, cohort, join_counts = join_valid_outcomes(tables)
    age_eligible = int(cohort["RIDAGEYR"].ge(30).fillna(False).sum())
    age_values = cohort["RIDAGEYR"].dropna()
    age_min = age_values.min() if not age_values.empty else "None"
    age_max = age_values.max() if not age_values.empty else "None"

    reference_rows = []
    found_values = (
        ("P_OHQ rows", len(ohq), 14986),
        ("OHQ850 Yes (1)", yes_count, 1941),
        ("OHQ850 No (2)", no_count, 5876),
        ("OHQ850 valid (1 or 2)", valid_count, 7817),
    )
    for label, found, reference in found_values:
        reference_rows.append((label, reference, found, "MATCH" if found == reference else "MISMATCH"))

    report = [
        "# NHANES input and outcome audit",
        "",
        "This report is generated from the four local XPT files. It describes data only; it does not train a model, split data, impute values, or remove rows from the joined cohort.",
        "",
        "## Input file dimensions and SEQN checks",
        "",
        markdown_table(
            ("File", "Rows", "Columns", "Rows with duplicate SEQN", "Unique non-missing SEQN", "Missing SEQN"),
            file_audit(tables),
        ),
        "",
        "Duplicate count means the number of rows whose SEQN occurs more than once. Missing SEQN values are counted separately.",
        "",
        "## OHQ850 outcome values",
        "",
        f"- All value counts, including NaN: {counts_with_missing(labels)}",
        f"- Valid labels (1 = Yes, 2 = No): {valid_count}",
        f"- Yes (1): {yes_count} ({yes_share:.2f}% of valid labels)",
        f"- No (2): {no_count} ({no_share:.2f}% of valid labels)",
        "- Codes other than 1 and 2, including blanks, are not valid labels.",
        "",
        "## Valid-outcome cohort and left joins",
        "",
        markdown_table(("Stage", "Rows", "Unique non-missing SEQN"), join_counts),
        "",
        f"Starting valid P_OHQ rows: {len(valid)}. Rows after all three left joins: {len(cohort)}. No rows lost: **{'YES' if len(cohort) >= len(valid) else 'NO'}**. No row expansion: **{'YES' if len(cohort) == len(valid) else 'NO'}**.",
        f"Age >= 30 diagnostic count in the joined valid-label view: {age_eligible}. This is reported only; no age filter was applied.",
        "",
        "## Predictor checks in the joined valid-outcome cohort",
        "",
        markdown_table(("Predictor", "NaN count", "Special-code counts", "Categorical value counts or numeric min/max"), predictor_audit(cohort)),
        "",
        f"RIDAGEYR min/max: {age_min} / {age_max}. NHANES top-codes age 80 as 80 or older, so a displayed maximum of 80 means 80+.",
        "",
        "## Reference-count comparison",
        "",
        markdown_table(("Measure", "AGENTS.md reference", "Found", "Result"), reference_rows),
        "",
        "Any MISMATCH above is a direct difference between the documented reference and the observed file count; no discrepancy is explained away here.",
        "",
    ]
    return "\n".join(report)


def main():
    """Load inputs, build one report, and print and save identical text."""
    tables = load_files()
    report = build_report(tables)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
