"""Audit the four NHANES XPT files without modelling or cleaning rows."""

from pathlib import Path
import hashlib
import platform

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

# These are documented refusal or don't-know codes for the
# individual fields. OHQ030 code 7 is a valid response, not a special code.
SPECIAL_CODES = {
    "DMDEDUC2": (7, 9),
    "DMDMARTZ": (77, 99),
    "OHQ030": (77, 99),
    "OHQ845": (7, 9),
    "OHQ860": (7, 9),
    "OHQ870": (77, 99),
    "OHQ835": (7, 9),
    "SMQ020": (7, 9),
    "SMQ040": (7, 9),
    "DIQ010": (7, 9),
}


def restore_xport_zeros(table, file_path, data_start, record_length, fields):
    """Restore two predictors' exact zero bytes misdecoded by pandas."""
    repairs = {}
    with file_path.open("rb") as source:
        for name, field in zip(table.columns, fields):
            if name not in ("INDFMPIR", "OHQ870"):
                continue
            # pandas decodes IBM's all-zero bytes as exactly 2**-260.
            # Confirm the source bytes: never round arbitrary tiny numbers.
            indices = table.index[table[name].eq(2.0**-260)]
            for index in indices:
                source.seek(data_start + int(index) * record_length + field["npos"])
                raw = source.read(field["field_length"])
                if raw != b"\x00" * field["field_length"]:
                    raise ValueError(f"Unverified tiny value in {name}; refusing to change it")
            if len(indices):
                table.loc[indices, name] = 0.0
                repairs[name] = len(indices)
    table.attrs["zero_decode_repairs"] = repairs


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
        with pd.read_sas(file_path, format="xport", iterator=True) as reader:
            data_start = reader.filepath_or_buffer.tell()
            table = reader.read()
            restore_xport_zeros(table, file_path, data_start, reader.record_length, reader.fields)
        tables[file_name] = table
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
            validate="one_to_one",
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
        if len(cohort) != before_rows:
            raise AssertionError(f"Row count changed during the {module_name} left join")
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
    predictor_rows = predictor_audit(cohort)
    age_eligible = int(cohort["RIDAGEYR"].ge(30).fillna(False).sum())
    age_below_30 = int(cohort["RIDAGEYR"].lt(30).sum())
    age_missing = int(cohort["RIDAGEYR"].isna().sum())
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

    # Separate project-range anomalies from CDC refusal/don't-know codes.
    cleaning_days = cohort["OHQ870"]
    cleaning_responses = cleaning_days.notna() & ~cleaning_days.isin(SPECIAL_CODES["OHQ870"])
    outside_range = cleaning_responses & (~cleaning_days.between(0, 7) | cleaning_days.mod(1).ne(0))
    missing_smoking = cohort["SMQ040"].isna()
    smoking_skip_no = int((missing_smoking & cohort["SMQ020"].eq(2)).sum())
    smoking_skip_special = int((missing_smoking & cohort["SMQ020"].isin((7, 9))).sum())
    smoking_missing_yes = int((missing_smoking & cohort["SMQ020"].eq(1)).sum())

    provenance = []
    decode_repairs = []
    for name, table in tables.items():
        file_path = DATA_DIR / f"{name}.xpt"
        if file_path.is_file():
            provenance.append((file_path.name, hashlib.sha256(file_path.read_bytes()).hexdigest()))
        for field, count in table.attrs.get("zero_decode_repairs", {}).items():
            decode_repairs.append((name, field, count))

    report = [
        "# NHANES input and outcome audit",
        "",
        "This report is generated from the four local XPT files. It describes data only; it does not train a model, split data, impute values, or remove rows from the joined cohort.",
        "OHQ850 means self-reported previous gum treatment; it is the outcome only, never a predictor. These are unweighted sample counts, not population estimates or disease diagnoses.",
        "",
        "## Reproduction and input identity",
        "",
        "Command: `.venv/bin/python src/tabular/audit_nhanes.py`",
        f"Python: {platform.python_version()}; pandas: {pd.__version__}.",
        "",
        markdown_table(("Input file in data/", "SHA-256"), provenance),
        "",
        "## Confirmed XPORT zero decoding correction",
        "",
        "The installed pandas XPORT reader decodes all-zero IBM float bytes as 5.397605346934028e-79. For INDFMPIR and OHQ870 only, each exact artifact is checked against the source bytes before restoring 0.0 in memory. Source files, missing values, and other numbers are unchanged; this is decoding correction, not imputation. Counts below cover full source files, before the valid-label view.",
        "",
        markdown_table(("File", "Field", "Verified zero cells restored"), decode_repairs),
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
        f"- Missing OHQ850: {int(labels.isna().sum())}; other non-missing invalid labels: {int((labels.notna() & ~labels.isin((1, 2))).sum())}; code 7: {int(labels.eq(7).sum())}; code 9: {int(labels.eq(9).sum())}.",
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
        f"Age below 30: {age_below_30}; missing age: {age_missing}. Age eligibility agrees with section 6.2: **{'YES' if age_below_30 == 0 and age_missing == 0 else 'NO'}**.",
        "",
        "## Predictor checks in the joined valid-outcome cohort",
        "",
        markdown_table(("Predictor", "NaN count", "Special-code counts", "Categorical value counts or numeric min/max"), predictor_rows),
        "",
        f"RIDAGEYR min/max: {age_min} / {age_max}. NHANES top-codes age 80 as 80 or older, so a displayed maximum of 80 means 80+.",
        "",
        "## Anomalies and skip-pattern checks",
        "",
        f"OHQ870 non-special responses outside the project's integer 0–7 rule: {int(outside_range.sum())}; values/counts: {counts_with_missing(cleaning_days.loc[outside_range])}. Refusal 77 and don't-know 99 are counted separately above. These rows are flagged and retained; no cleaning-day exclusions were applied.",
        "The CDC OHQ870 frequency table lists a released range of 0–9, while the question asks about the last seven days and AGENTS.md requires 0–7. This is a documented range discrepancy requiring review before preprocessing; 8 and 9 are not CDC refusal/don't-know codes.",
        f"SMQ040 missing total: {int(missing_smoking.sum())}. Of these, SMQ020=No: {smoking_skip_no}; SMQ020=7/9: {smoking_skip_special}; SMQ020=Yes: {smoking_missing_yes}. CDC skips SMQ040 after No/refused/don't-know answers to SMQ020. Missing smoking responses are not imputed here.",
        "The valid-label audit view is not a finalized cleaned modelling sample; handling special codes, missing predictors and flagged cleaning-day values remains future work.",
        "",
        "## Reference-count comparison",
        "",
        markdown_table(("Measure", "AGENTS.md reference", "Found", "Result"), reference_rows),
        "",
        "Any MISMATCH above is a direct difference between the documented reference and the observed file count; no discrepancy is explained away here.",
        "",
        "## Codebook sources reviewed",
        "",
        "- [CDC oral health: OHQ030, OHQ835, OHQ845, OHQ850, OHQ860, OHQ870](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_OHQ.htm)",
        "- [CDC demographics: RIDAGEYR, RIAGENDR, DMDEDUC2, DMDMARTZ, INDFMPIR](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DEMO.htm)",
        "- [CDC smoking: SMQ020, SMQ040](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_SMQ.htm)",
        "- [CDC diabetes: DIQ010 (3 = borderline is a valid category)](https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/2017/DataFiles/P_DIQ.htm)",
        "- [SAS XPORT format: IBM numeric representation](https://support.sas.com/content/dam/SAS/support/en/technical-papers/record-layout-of-a-sas-version-5-or-6-data-set-in-sas-transport-xport-format.pdf)",
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
