import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = (
    ROOT
    / "explainability"
    / "reports"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_JSON = (
    OUTPUT_DIR
    / "gradcam_summary.json"
)

OUTPUT_MD = (
    OUTPUT_DIR
    / "gradcam_summary.md"
)


summary = {
    "component":
        "Malocclusion Detection",

    "method":
        "Grad-CAM layer comparison",

    "architecture":
        "MobileNetV2",

    "conditions": {
        "crossbite": {
            "selected_layer":
                "block_14_expand_relu",

            "status":
                "usable_but_imperfect",

            "interpretation":
                (
                    "The intermediate MobileNetV2 layer "
                    "provided more visible activation over "
                    "the dental region than the final "
                    "convolutional layer. However, some "
                    "attention was also observed near image "
                    "boundaries."
                ),

            "report_use":
                "exploratory_only",
        },

        "crowding": {
            "selected_layer":
                "block_14_expand_relu",

            "status":
                "best_available_localization",

            "interpretation":
                (
                    "The selected intermediate layer showed "
                    "the clearest attention across the teeth "
                    "region among the tested MobileNetV2 "
                    "layers. Localization remains preliminary "
                    "and is not clinically validated."
                ),

            "report_use":
                "preliminary_explainability",
        },

        "open_bite": {
            "selected_layer":
                "block_13_expand_relu",

            "status":
                "weak_inconsistent",

            "interpretation":
                (
                    "Some activation appeared over dental "
                    "regions, but attention was inconsistent "
                    "and also appeared in image corners, lips "
                    "and boundary areas. This may indicate "
                    "shortcut learning."
                ),

            "report_use":
                "limitation_evidence",
        },
    },

    "layers_compared": [
        "block_13_expand_relu",
        "block_14_expand_relu",
        "block_15_project",
        "block_16_project",
        "Conv_1",
    ],

    "overall_finding":
        (
            "Intermediate MobileNetV2 layers produced more "
            "informative Grad-CAM visualizations than the "
            "final convolutional layer for some conditions. "
            "However, attention was not consistently limited "
            "to clinically relevant dental regions."
        ),

    "research_interpretation":
        (
            "The Grad-CAM analysis suggests possible shortcut "
            "learning and limited localization reliability. "
            "The visual explanations should therefore be used "
            "as exploratory model-inspection evidence rather "
            "than clinical explanations."
        ),

    "limitations": [
        (
            "The underlying binary models were trained using "
            "small and imbalanced datasets."
        ),
        (
            "The selected Grad-CAM layers were chosen through "
            "visual comparison rather than clinical expert "
            "validation."
        ),
        (
            "No dental expert independently verified whether "
            "highlighted regions correspond to clinically "
            "relevant malocclusion features."
        ),
        (
            "Some activation maps highlighted image borders, "
            "lips or other non-dental regions."
        ),
        (
            "Grad-CAM attention does not prove causal or "
            "clinical reasoning by the model."
        ),
    ],
}


OUTPUT_JSON.write_text(
    json.dumps(
        summary,
        indent=2
    ),
    encoding="utf-8"
)


markdown = []

markdown.append(
    "# Grad-CAM Explainability Summary\n\n"
)

markdown.append(
    "## Overview\n\n"
)

markdown.append(
    "Grad-CAM was used to inspect the image regions influencing "
    "the preliminary MobileNetV2 binary malocclusion models. "
    "Multiple intermediate and final convolutional layers were "
    "compared before selecting the most informative layer for "
    "each condition.\n\n"
)

markdown.append(
    "## Layer Comparison\n\n"
)

markdown.append(
    "| Condition | Selected Layer | Status |\n"
)

markdown.append(
    "|---|---|---|\n"
)

markdown.append(
    "| Crossbite | block_14_expand_relu | Usable but imperfect |\n"
)

markdown.append(
    "| Crowding | block_14_expand_relu | Best available localization |\n"
)

markdown.append(
    "| Open Bite | block_13_expand_relu | Weak / inconsistent |\n"
)


markdown.append(
    "\n## Crossbite\n\n"
)

markdown.append(
    "The `block_14_expand_relu` layer produced more visible "
    "attention over the dental region than the final "
    "convolutional layer. However, some activation was also "
    "observed near image boundaries. Therefore, this output "
    "is treated as exploratory explainability evidence only.\n"
)


markdown.append(
    "\n## Crowding\n\n"
)

markdown.append(
    "The `block_14_expand_relu` layer provided the clearest "
    "dental-region localization among the tested layers. "
    "The output is useful for preliminary model inspection, "
    "but it has not been clinically validated.\n"
)


markdown.append(
    "\n## Open Bite\n\n"
)

markdown.append(
    "The `block_13_expand_relu` layer provided some dental-region "
    "activation, but attention was inconsistent and also appeared "
    "in image corners, lips, and boundary regions. This may "
    "indicate shortcut learning and limited model reliability.\n"
)


markdown.append(
    "\n## Overall Interpretation\n\n"
)

markdown.append(
    "Intermediate MobileNetV2 layers produced more informative "
    "Grad-CAM visualizations than the final convolutional layer "
    "for some conditions. However, attention was not consistently "
    "restricted to clinically relevant dental regions. Therefore, "
    "the Grad-CAM results are interpreted as exploratory model "
    "inspection rather than evidence of clinical reasoning.\n"
)


markdown.append(
    "\n## Limitations\n\n"
)

for limitation in summary["limitations"]:
    markdown.append(
        f"- {limitation}\n"
    )


markdown.append(
    "\n## Research Statement\n\n"
)

markdown.append(
    "> Layer-wise Grad-CAM analysis showed that intermediate "
    "MobileNetV2 layers provided more informative localization "
    "than the final convolutional layer. However, attention was "
    "not consistently restricted to clinically relevant dental "
    "regions, especially for Open Bite, indicating possible "
    "shortcut learning and limited model reliability.\n"
)


OUTPUT_MD.write_text(
    "".join(markdown),
    encoding="utf-8"
)


print("=" * 70)
print("GRAD-CAM SUMMARY REPORT")
print("=" * 70)

print(
    "JSON:",
    OUTPUT_JSON
)

print(
    "Markdown:",
    OUTPUT_MD
)

print("\nSelected layers:")
print(
    "Crossbite: block_14_expand_relu"
)
print(
    "Crowding: block_14_expand_relu"
)
print(
    "Open Bite: block_13_expand_relu"
)

print("\nGrad-CAM summary completed.")