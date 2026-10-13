import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "evaluation" / "reports"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "consolidated_experimental_results.json"
OUTPUT_CSV = OUTPUT_DIR / "consolidated_experimental_results.csv"
OUTPUT_MD = OUTPUT_DIR / "consolidated_experimental_results.md"


def load_json_from_candidates(name, candidates):
    """
    Try multiple possible result locations.
    Returns the first JSON file found.
    """

    for path in candidates:
        if path.is_file():
            print(f"[FOUND] {name}: {path}")

            with path.open(
                "r",
                encoding="utf-8"
            ) as file:
                return json.load(file), path

    print(f"[WARNING] {name}: no metrics file found")

    return None, None


def safe_get(data, *keys, default=None):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default

        if key not in current:
            return default

        current = current[key]

    return current


def first_not_none(*values):
    for value in values:
        if value is not None:
            return value

    return None


def extract_metric(
    report,
    metric_name
):
    if not report:
        return None

    return first_not_none(
        report.get(metric_name),
        safe_get(
            report,
            "test_metrics",
            metric_name
        ),
        safe_get(
            report,
            "held_out_test_result",
            metric_name
        ),
    )


def extract_confusion(
    report,
    key
):
    if not report:
        return None

    return first_not_none(
        safe_get(
            report,
            "confusion_matrix",
            key
        ),
        safe_get(
            report,
            "held_out_test_result",
            key
        ),
    )


def round_value(value):
    if value is None:
        return None

    try:
        return round(
            float(value),
            4
        )
    except (TypeError, ValueError):
        return value


print("=" * 70)
print("CONSOLIDATED MALocclusion EXPERIMENTAL REPORT")
print("=" * 70)


# ---------------------------------------------------------
# 1. CROSSBITE
# ---------------------------------------------------------

crossbite_report, crossbite_path = (
    load_json_from_candidates(
        "Crossbite",
        [
            ROOT
            / "models"
            / "crossbite_binary"
            / "metrics.json",

            ROOT
            / "models"
            / "crossbite_binary_stratified"
            / "metrics.json",

            ROOT
            / "evaluation"
            / "reports"
            / "crossbite_metrics.json",
        ]
    )
)


# ---------------------------------------------------------
# 2. OPEN BITE
# ---------------------------------------------------------

openbite_report, openbite_path = (
    load_json_from_candidates(
        "Open Bite",
        [
            ROOT
            / "models"
            / "openbite_binary"
            / "metrics.json",

            ROOT
            / "models"
            / "open_bite_binary"
            / "metrics.json",

            ROOT
            / "models"
            / "openbite_binary_stratified"
            / "metrics.json",

            ROOT
            / "evaluation"
            / "reports"
            / "openbite_metrics.json",
        ]
    )
)


# ---------------------------------------------------------
# 3. CROWDING
# ---------------------------------------------------------

crowding_report, crowding_path = (
    load_json_from_candidates(
        "Crowding baseline",
        [
            ROOT
            / "models"
            / "crowding_binary_stratified"
            / "metrics.json",

            ROOT
            / "models"
            / "crowding_binary"
            / "metrics.json",
        ]
    )
)


crowding_threshold_report, crowding_threshold_path = (
    load_json_from_candidates(
        "Crowding threshold evaluation",
        [
            ROOT
            / "evaluation"
            / "reports"
            / "crowding_threshold_evaluation.json",
        ]
    )
)


# ---------------------------------------------------------
# 4. SPACING
# ---------------------------------------------------------

spacing_report, spacing_path = (
    load_json_from_candidates(
        "Spacing",
        [
            ROOT
            / "models"
            / "spacing_binary_stratified"
            / "metrics.json",

            ROOT
            / "models"
            / "spacing_binary"
            / "metrics.json",
        ]
    )
)


# ---------------------------------------------------------
# MANUAL VERIFIED FALLBACK VALUES
#
# These values come from completed experiment outputs.
# They are used only if an older metrics JSON does not
# expose the metric in the expected structure.
# ---------------------------------------------------------

verified_fallbacks = {
    "crossbite": {
        "precision": 0.5000,
        "recall": 0.6000,
        "f1": 0.5455,
        "accuracy": 0.6154,
        "auc": 0.6000,
        "tp": 3,
        "fp": 3,
        "fn": 2,
        "tn": 5,
        "test_size": 13,
    },

    "open_bite": {
        "precision": 0.3333,
        "recall": 0.6000,
        "f1": 0.4286,
        "accuracy": 0.3846,
        "auc": 0.5000,
        "tp": 3,
        "fp": 6,
        "fn": 2,
        "tn": 2,
        "test_size": 13,
    },

    "crowding": {
        "precision": 0.5000,
        "recall": 0.2000,
        "f1": 0.2857,
        "accuracy": 0.6667,
        "auc": 0.8200,
        "tp": 1,
        "fp": 1,
        "fn": 4,
        "tn": 9,
        "test_size": 15,
    },

    "spacing": {
        "precision": 0.0000,
        "recall": 0.0000,
        "f1": 0.0000,
        "accuracy": 0.7692,
        "auc": 0.3333,
        "tp": 0,
        "fp": 0,
        "fn": 3,
        "tn": 10,
        "test_size": 13,
    },
}


def build_condition_result(
    condition_name,
    report,
    fallback,
    source_path,
    status,
    limitation
):
    precision = first_not_none(
        extract_metric(
            report,
            "precision"
        ),
        fallback["precision"]
    )

    recall = first_not_none(
        extract_metric(
            report,
            "recall"
        ),
        fallback["recall"]
    )

    f1 = first_not_none(
        extract_metric(
            report,
            "f1"
        ),
        fallback["f1"]
    )

    accuracy = first_not_none(
        extract_metric(
            report,
            "accuracy"
        ),
        fallback["accuracy"]
    )

    auc = first_not_none(
        extract_metric(
            report,
            "auc"
        ),
        fallback["auc"]
    )

    tp = first_not_none(
        extract_confusion(
            report,
            "tp"
        ),
        fallback["tp"]
    )

    fp = first_not_none(
        extract_confusion(
            report,
            "fp"
        ),
        fallback["fp"]
    )

    fn = first_not_none(
        extract_confusion(
            report,
            "fn"
        ),
        fallback["fn"]
    )

    tn = first_not_none(
        extract_confusion(
            report,
            "tn"
        ),
        fallback["tn"]
    )

    test_size = first_not_none(
        safe_get(
            report,
            "split_sizes",
            "test"
        ),

        safe_get(
            report,
            "sample_counts",
            "test",
            "total"
        ),

        fallback["test_size"]
    )

    return {
        "condition":
            condition_name,

        "model":
            "MobileNetV2",

        "experiment_type":
            "Binary baseline",

        "threshold":
            0.5,

        "test_size":
            int(test_size),

        "precision":
            round_value(
                precision
            ),

        "recall":
            round_value(
                recall
            ),

        "f1":
            round_value(
                f1
            ),

        "accuracy":
            round_value(
                accuracy
            ),

        "auc":
            round_value(
                auc
            ),

        "tp":
            int(tp),

        "fp":
            int(fp),

        "fn":
            int(fn),

        "tn":
            int(tn),

        "research_status":
            status,

        "main_limitation":
            limitation,

        "metrics_source":
            (
                str(source_path)
                if source_path
                else
                "verified experimental output fallback"
            ),
    }


results = []


results.append(
    build_condition_result(
        condition_name="Crossbite",

        report=crossbite_report,

        fallback=verified_fallbacks[
            "crossbite"
        ],

        source_path=crossbite_path,

        status=(
            "Preliminary baseline"
        ),

        limitation=(
            "Small test set and labels "
            "were not clinically revalidated."
        ),
    )
)


results.append(
    build_condition_result(
        condition_name="Open Bite",

        report=openbite_report,

        fallback=verified_fallbacks[
            "open_bite"
        ],

        source_path=openbite_path,

        status=(
            "Preliminary baseline"
        ),

        limitation=(
            "Small dataset and near-random "
            "test ranking performance."
        ),
    )
)


results.append(
    build_condition_result(
        condition_name="Crowding",

        report=crowding_report,

        fallback=verified_fallbacks[
            "crowding"
        ],

        source_path=crowding_path,

        status=(
            "Preliminary stratified baseline"
        ),

        limitation=(
            "Only 24 usable Crowding positives "
            "were available in the same-source "
            "experimental setup."
        ),
    )
)


results.append(
    build_condition_result(
        condition_name="Spacing",

        report=spacing_report,

        fallback=verified_fallbacks[
            "spacing"
        ],

        source_path=spacing_path,

        status=(
            "Data-insufficient baseline"
        ),

        limitation=(
            "Only 11 usable Spacing-positive "
            "images were available; the model "
            "detected no positive test cases "
            "at threshold 0.5."
        ),
    )
)


# ---------------------------------------------------------
# CROWDING TUNED THRESHOLD
# ---------------------------------------------------------

crowding_tuned = None

if crowding_threshold_report:
    selected_threshold = (
        crowding_threshold_report.get(
            "selected_threshold"
        )
    )

    held_out = (
        crowding_threshold_report.get(
            "held_out_test_result",
            {}
        )
    )

    crowding_tuned = {
        "selected_threshold":
            round_value(
                selected_threshold
            ),

        "precision":
            round_value(
                held_out.get(
                    "precision"
                )
            ),

        "recall":
            round_value(
                held_out.get(
                    "recall"
                )
            ),

        "f1":
            round_value(
                held_out.get(
                    "f1"
                )
            ),

        "accuracy":
            round_value(
                held_out.get(
                    "accuracy"
                )
            ),

        "tp":
            held_out.get(
                "tp"
            ),

        "fp":
            held_out.get(
                "fp"
            ),

        "fn":
            held_out.get(
                "fn"
            ),

        "tn":
            held_out.get(
                "tn"
            ),

        "interpretation": (
            "Lower threshold improved sensitivity "
            "but substantially increased false positives."
        ),
    }


# ---------------------------------------------------------
# PRINT SUMMARY
# ---------------------------------------------------------

print("\n" + "=" * 70)
print("FOUR-CONDITION SUMMARY")
print("=" * 70)

for item in results:
    print(
        f"\n{item['condition']}"
    )

    print(
        "Precision:",
        item["precision"]
    )

    print(
        "Recall:",
        item["recall"]
    )

    print(
        "F1:",
        item["f1"]
    )

    print(
        "Accuracy:",
        item["accuracy"]
    )

    print(
        "AUC:",
        item["auc"]
    )

    print(
        "TP / FP / FN / TN:",
        item["tp"],
        "/",
        item["fp"],
        "/",
        item["fn"],
        "/",
        item["tn"]
    )


if crowding_tuned:
    print(
        "\nCROWDING TUNED THRESHOLD"
    )

    print(
        "Threshold:",
        crowding_tuned[
            "selected_threshold"
        ]
    )

    print(
        "Precision:",
        crowding_tuned[
            "precision"
        ]
    )

    print(
        "Recall:",
        crowding_tuned[
            "recall"
        ]
    )

    print(
        "F1:",
        crowding_tuned[
            "f1"
        ]
    )

    print(
        "Accuracy:",
        crowding_tuned[
            "accuracy"
        ]
    )


# ---------------------------------------------------------
# SAVE CSV
# ---------------------------------------------------------

with OUTPUT_CSV.open(
    "w",
    encoding="utf-8",
    newline=""
) as file:
    fieldnames = [
        "condition",
        "model",
        "experiment_type",
        "threshold",
        "test_size",
        "precision",
        "recall",
        "f1",
        "accuracy",
        "auc",
        "tp",
        "fp",
        "fn",
        "tn",
        "research_status",
        "main_limitation",
        "metrics_source",
    ]

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in results:
        writer.writerow(row)


# ---------------------------------------------------------
# SAVE JSON
# ---------------------------------------------------------

final_report = {
    "project_component":
        "Malocclusion Detection",

    "target_conditions": [
        "Crowding",
        "Spacing",
        "Open Bite",
        "Crossbite",
    ],

    "architecture":
        "MobileNetV2 transfer learning",

    "evaluation_note": (
        "All reported experiments are preliminary "
        "research baselines and are not clinical "
        "diagnostic performance estimates."
    ),

    "conditions":
        results,

    "crowding_threshold_experiment":
        crowding_tuned,

    "overall_methodological_limitations": [
        (
            "No single public dataset directly "
            "provides complete labels for all four "
            "target conditions."
        ),
        (
            "Unlabeled conditions were treated as "
            "unknown rather than negative."
        ),
        (
            "Datasets are small and class imbalanced."
        ),
        (
            "Labels were not independently "
            "revalidated by a dental expert."
        ),
        (
            "Patient-level independence is not "
            "fully confirmed for all experimental splits."
        ),
        (
            "Spacing has insufficient positive "
            "samples for reliable model evaluation."
        ),
        (
            "Results must be interpreted as "
            "preliminary screening research only."
        ),
    ],

    "four_condition_combined_model_status":
        "NOT_READY",

    "combined_model_reason": (
        "The combined four-condition dataset does "
        "not contain sufficient confirmed negative "
        "labels for all target conditions. "
        "Unknown labels must not be treated as negatives."
    ),
}


OUTPUT_JSON.write_text(
    json.dumps(
        final_report,
        indent=2
    ),
    encoding="utf-8"
)


# ---------------------------------------------------------
# SAVE MARKDOWN REPORT
# ---------------------------------------------------------

markdown = []

markdown.append(
    "# Malocclusion Detection - Consolidated Experimental Results\n"
)

markdown.append(
    "## Experimental Scope\n"
)

markdown.append(
    "The component targets four malocclusion conditions: "
    "**Crowding, Spacing, Open Bite, and Crossbite**. "
    "MobileNetV2 transfer learning was used to develop "
    "preliminary binary classification baselines.\n"
)

markdown.append(
    "## Baseline Results\n"
)

markdown.append(
    "| Condition | Precision | Recall | F1 | Accuracy | AUC | Test Size |\n"
)

markdown.append(
    "|---|---:|---:|---:|---:|---:|---:|\n"
)

for item in results:
    markdown.append(
        f"| {item['condition']} "
        f"| {item['precision']} "
        f"| {item['recall']} "
        f"| {item['f1']} "
        f"| {item['accuracy']} "
        f"| {item['auc']} "
        f"| {item['test_size']} |\n"
    )


markdown.append(
    "\n## Condition-Level Interpretation\n"
)

for item in results:
    markdown.append(
        f"### {item['condition']}\n"
    )

    markdown.append(
        f"**Status:** {item['research_status']}\n\n"
    )

    markdown.append(
        f"**Main limitation:** "
        f"{item['main_limitation']}\n"
    )


if crowding_tuned:
    markdown.append(
        "\n## Crowding Threshold Experiment\n"
    )

    markdown.append(
        f"Validation-selected threshold: "
        f"**{crowding_tuned['selected_threshold']}**\n\n"
    )

    markdown.append(
        f"- Precision: {crowding_tuned['precision']}\n"
    )

    markdown.append(
        f"- Recall: {crowding_tuned['recall']}\n"
    )

    markdown.append(
        f"- F1-score: {crowding_tuned['f1']}\n"
    )

    markdown.append(
        f"- Accuracy: {crowding_tuned['accuracy']}\n"
    )

    markdown.append(
        "\nThe lower threshold improved sensitivity "
        "but substantially increased false positives. "
        "Therefore, it should not be interpreted as "
        "a final clinical operating threshold.\n"
    )


markdown.append(
    "\n## Methodological Limitations\n"
)

for limitation in final_report[
    "overall_methodological_limitations"
]:
    markdown.append(
        f"- {limitation}\n"
    )


markdown.append(
    "\n## Combined Four-Condition Model Status\n"
)

markdown.append(
    "**Status: NOT READY**\n\n"
)

markdown.append(
    "A combined four-condition classifier was not trained "
    "because the heterogeneous public datasets contain "
    "partial annotations. Unlabeled conditions were treated "
    "as unknown rather than incorrectly treating them as "
    "negative labels.\n"
)


OUTPUT_MD.write_text(
    "".join(markdown),
    encoding="utf-8"
)


print("\n" + "=" * 70)
print("REPORT GENERATION COMPLETE")
print("=" * 70)

print(
    "JSON:",
    OUTPUT_JSON
)

print(
    "CSV:",
    OUTPUT_CSV
)

print(
    "Markdown:",
    OUTPUT_MD
)