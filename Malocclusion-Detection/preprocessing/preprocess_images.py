from pathlib import Path
import cv2


# MobileNetV2 input size
IMAGE_SIZE = (224, 224)

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def preprocess_image(image_path: Path, output_path: Path) -> bool:
    """
    Validate and preprocess one dental/smile image.

    Steps:
    1. Read image
    2. Check that it can be decoded
    3. Resize to MobileNetV2 input size
    4. Apply light noise reduction
    5. Normalize pixel values
    6. Save the processed image
    """

    image = cv2.imread(str(image_path))

    if image is None:
        return False

    # Resize
    image = cv2.resize(image, IMAGE_SIZE, interpolation=cv2.INTER_AREA)

    # Light noise reduction while preserving important edges
    image = cv2.GaussianBlur(image, (3, 3), 0)

    # Normalize pixel values to 0–255
    image = cv2.normalize(
        image,
        None,
        alpha=0,
        beta=255,
        norm_type=cv2.NORM_MINMAX,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    return cv2.imwrite(str(output_path), image)


def process_dataset(input_dir: Path, output_dir: Path, invalid_dir: Path) -> None:
    """
    Process all supported images inside the input directory.
    Invalid or corrupted images are copied to the invalid folder.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    invalid_dir.mkdir(parents=True, exist_ok=True)

    total = 0
    processed = 0
    invalid = 0

    for image_path in input_dir.rglob("*"):
        if not image_path.is_file():
            continue

        if image_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        total += 1

        relative_path = image_path.relative_to(input_dir)
        output_path = output_dir / relative_path

        success = preprocess_image(image_path, output_path)

        if success:
            processed += 1
            print(f"[OK] {image_path}")
        else:
            invalid += 1
            print(f"[INVALID] {image_path}")

            invalid_path = invalid_dir / relative_path
            invalid_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                invalid_path.write_bytes(image_path.read_bytes())
            except OSError:
                pass

    print("\n--- Pre-processing Summary ---")
    print(f"Total images found : {total}")
    print(f"Processed images   : {processed}")
    print(f"Invalid images     : {invalid}")


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parents[1]

    INPUT_DIR = BASE_DIR / "data" / "raw"
    OUTPUT_DIR = BASE_DIR / "data" / "processed"
    INVALID_DIR = BASE_DIR / "data" / "invalid"

    process_dataset(INPUT_DIR, OUTPUT_DIR, INVALID_DIR)