# Grad-CAM Explainability Summary

## Overview

Grad-CAM was used to inspect the image regions influencing the preliminary MobileNetV2 binary malocclusion models. Multiple intermediate and final convolutional layers were compared before selecting the most informative layer for each condition.

## Layer Comparison

| Condition | Selected Layer | Status |
|---|---|---|
| Crossbite | block_14_expand_relu | Usable but imperfect |
| Crowding | block_14_expand_relu | Best available localization |
| Open Bite | block_13_expand_relu | Weak / inconsistent |

## Crossbite

The `block_14_expand_relu` layer produced more visible attention over the dental region than the final convolutional layer. However, some activation was also observed near image boundaries. Therefore, this output is treated as exploratory explainability evidence only.

## Crowding

The `block_14_expand_relu` layer provided the clearest dental-region localization among the tested layers. The output is useful for preliminary model inspection, but it has not been clinically validated.

## Open Bite

The `block_13_expand_relu` layer provided some dental-region activation, but attention was inconsistent and also appeared in image corners, lips, and boundary regions. This may indicate shortcut learning and limited model reliability.

## Overall Interpretation

Intermediate MobileNetV2 layers produced more informative Grad-CAM visualizations than the final convolutional layer for some conditions. However, attention was not consistently restricted to clinically relevant dental regions. Therefore, the Grad-CAM results are interpreted as exploratory model inspection rather than evidence of clinical reasoning.

## Limitations

- The underlying binary models were trained using small and imbalanced datasets.
- The selected Grad-CAM layers were chosen through visual comparison rather than clinical expert validation.
- No dental expert independently verified whether highlighted regions correspond to clinically relevant malocclusion features.
- Some activation maps highlighted image borders, lips or other non-dental regions.
- Grad-CAM attention does not prove causal or clinical reasoning by the model.

## Research Statement

> Layer-wise Grad-CAM analysis showed that intermediate MobileNetV2 layers provided more informative localization than the final convolutional layer. However, attention was not consistently restricted to clinically relevant dental regions, especially for Open Bite, indicating possible shortcut learning and limited model reliability.
