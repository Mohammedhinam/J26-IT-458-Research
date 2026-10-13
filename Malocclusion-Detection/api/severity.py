from typing import Dict, Any

SEVERITY_FRAMEWORK = {
    "crossbite": {
        "supported": True,
        "status": "framework_defined_not_clinically_validated",
        "required_information": [
            "location of crossbite",
            "number of affected teeth",
            "anterior or posterior involvement",
            "extent of occlusal discrepancy",
        ],
        "possible_levels": [
            "mild",
            "moderate",
            "severe",
        ],
        "note": (
            "Severity must be determined using clinically "
            "supported orthodontic criteria. Model probability "
            "alone must not be used as severity."
        ),
    },

    "open_bite": {
        "supported": True,
        "status": "framework_defined_not_clinically_validated",
        "required_information": [
            "vertical separation between upper and lower teeth",
            "anterior or posterior location",
            "extent of affected region",
        ],
        "possible_levels": [
            "mild",
            "moderate",
            "severe",
        ],
        "note": (
            "Severity requires clinically meaningful bite-gap "
            "measurement or expert-supported criteria."
        ),
    },

    "crowding": {
        "supported": True,
        "status": "framework_defined_not_clinically_validated",
        "required_information": [
            "arch space discrepancy",
            "degree of tooth displacement",
            "number of crowded teeth",
            "distribution of crowding",
        ],
        "possible_levels": [
            "mild",
            "moderate",
            "severe",
        ],
        "note": (
            "Severity requires orthodontic measurements such as "
            "space discrepancy or clinically validated crowding criteria."
        ),
    },

    "spacing": {
        "supported": True,
        "status": "framework_defined_not_clinically_validated",
        "required_information": [
            "gap size",
            "number of spaced regions",
            "distribution of spacing",
        ],
        "possible_levels": [
            "mild",
            "moderate",
            "severe",
        ],
        "note": (
            "Severity requires clinically supported spacing "
            "measurements. Prediction probability is not severity."
        ),
    },
}


def get_severity_framework(
    condition: str
) -> Dict[str, Any]:

    condition = (
        condition
        .strip()
        .lower()
        .replace(" ", "_")
    )

    framework = (
        SEVERITY_FRAMEWORK
        .get(condition)
    )

    if framework is None:
        return {
            "condition": condition,
            "severity_status": "unsupported_condition",
            "severity": None,
            "message": (
                "No severity framework is available "
                "for this condition."
            ),
        }

    return {
        "condition": condition,
        "severity_status":
            framework["status"],

        "severity":
            None,

        "possible_levels":
            framework["possible_levels"],

        "required_information":
            framework["required_information"],

        "message":
            framework["note"],
    }


def assess_severity(
    condition: str,
    clinical_measurements: Dict[str, Any] | None = None
) -> Dict[str, Any]:

    framework = get_severity_framework(
        condition
    )

    if (
        framework.get(
            "severity_status"
        )
        == "unsupported_condition"
    ):
        return framework

    if not clinical_measurements:

        return {
            **framework,

            "severity":
                None,

            "severity_status":
                "not_assessed",

            "reason":
                (
                    "Required clinical measurements "
                    "or expert-supported severity criteria "
                    "were not provided."
                ),
        }

    # --------------------------------------------------
    # IMPORTANT
    # --------------------------------------------------
    #
    # Do NOT implement arbitrary severity thresholds here.
    #
    # Example of what MUST NOT be done:
    #
    # if probability > 0.80:
    #     severity = "severe"
    #
    # Prediction confidence is not a clinical severity measure.
    #
    # This section should only be implemented after:
    #
    # 1. literature-supported severity criteria are defined
    # 2. required measurements are identified
    # 3. criteria are clinically reviewed where possible
    #
    # --------------------------------------------------

    return {
        **framework,

        "severity":
            None,

        "severity_status":
            "measurement_received_but_rules_pending_validation",

        "clinical_measurements":
            clinical_measurements,

        "reason":
            (
                "Clinical measurements were supplied, "
                "but validated severity rules have not "
                "yet been implemented."
            ),
    }


def attach_severity_to_prediction(
    condition: str,
    prediction_result: Dict[str, Any]
) -> Dict[str, Any]:

    severity_result = assess_severity(
        condition=condition,
        clinical_measurements=None,
    )

    return {
        **prediction_result,

        "severity_assessment":
            severity_result,
    }


if __name__ == "__main__":

    print("=" * 60)
    print("SEVERITY FRAMEWORK TEST")
    print("=" * 60)

    for condition in [
        "crossbite",
        "open_bite",
        "crowding",
        "spacing",
    ]:
        result = assess_severity(
            condition
        )

        print(
            f"\nCondition: {condition}"
        )

        print(
            "Severity:",
            result["severity"]
        )

        print(
            "Status:",
            result[
                "severity_status"
            ]
        )

        print(
            "Required information:"
        )

        for item in result.get(
            "required_information",
            []
        ):
            print(
                "-",
                item
            )