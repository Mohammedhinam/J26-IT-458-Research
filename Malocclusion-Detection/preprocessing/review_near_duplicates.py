
from pathlib import Path
from PIL import Image, ImageDraw
import imagehash

base = Path("data/raw")
datasets = ["crooked_detection", "crowded_teeth", "smile_spacing"]
splits = ["train", "valid", "test"]

images = []

for dataset in datasets:
    for split in splits:
        folder = base / dataset / split

        for path in folder.glob("*"):
            if path.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                continue

            with Image.open(path) as img:
                phash = imagehash.phash(img.convert("RGB"))

            images.append((dataset, split, path, phash))

matches = []

for i in range(len(images)):
    for j in range(i + 1, len(images)):
        a, b = images[i], images[j]

        if (a[0], a[1]) == (b[0], b[1]):
            continue

        distance = a[3] - b[3]

        if distance <= 5:
            matches.append((distance, a, b))

matches.sort(key=lambda x: x[0])

output = Path("data/invalid/duplicate_review")
output.mkdir(parents=True, exist_ok=True)

for index, (distance, a, b) in enumerate(matches, 1):
    canvas = Image.new("RGB", (900, 510), "white")
    draw = ImageDraw.Draw(canvas)

    for side, item in enumerate((a, b)):
        with Image.open(item[2]) as img:
            img = img.convert("RGB")
            img.thumbnail((430, 390))

            x = side * 450 + (450 - img.width) // 2
            y = 60 + (390 - img.height) // 2

            canvas.paste(img, (x, y))

        label = f"{item[0]} / {item[1]}"
        draw.text((side * 450 + 12, 15), label, fill="black")
        draw.text(
            (side * 450 + 12, 465),
            item[2].name[:52],
            fill="black"
        )

    draw.text((350, 490), f"pHash distance: {distance}", fill="black")

    canvas.save(output / f"pair_{index:02d}.jpg")

print("Pairs found:", len(matches))
print("Review images saved to:", output.resolve())
