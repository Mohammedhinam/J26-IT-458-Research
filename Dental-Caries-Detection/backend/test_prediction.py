
from pathlib import Path
from app.services.caries_prediction import predict_dental_caries

# Test image location
image_path = Path(__file__).parent / "test_image.jpg"

if not image_path.exists():
    print("ERROR: test_image.jpg not found!")
else:
    print("Running dental caries detection...\n")

    results = predict_dental_caries(image_path)

    print("Image:", results["image"])
    print("Detected regions:", results["total_regions"])

    for region in results["regions"]:
        print(f"\nRegion {region['region']}")
        print("YOLO confidence:", region["detection_confidence"])
        print("MobileNetV2:", region["MobileNetV2"]["prediction"])
        print("EfficientNet-B0:", region["EfficientNetB0"]["prediction"])
        print("Status:", region["status"])
        print("Final prediction:", region["final_prediction"])

    print("\nLocal prediction test completed!")
