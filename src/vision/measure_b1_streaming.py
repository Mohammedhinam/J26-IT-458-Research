"""Fresh-process generated-only stress measurement; no real input or packaging."""
import json
import platform
import resource
import shutil
import sys
import tempfile
import time
from pathlib import Path

from src.vision import colour_b1_streaming as full
from src.vision.gamut_mapping_feasibility import _generated_profile  # Load dependencies before baseline.


def peak_rss_bytes():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform == "darwin":
        return int(value)
    if sys.platform.startswith("linux"):
        return int(value * 1024)
    raise RuntimeError("Unsupported RSS reporting units; no guessed measurement")


def measure(width, height):
    if (width, height) not in {(1024, 768), (4096, 3072)}:
        raise ValueError("Only fixed generated engineering stress sizes authorised")
    source = full.GeneratedSource(width, height, "mixed", "wide_red")
    expected_disk = width * height * 12 + 1024**2
    if shutil.disk_usage(tempfile.gettempdir()).free < expected_disk * 2:
        raise RuntimeError("Insufficient scratch disk; no stress output created")
    scratch = Path(tempfile.mkdtemp(prefix="b1_generated_stress_"))
    before = peak_rss_bytes()
    start = time.perf_counter()
    try:
        result = full.convert_generated_full(source, scratch / "generated")
        verified = full.verify_generated_outputs(result["directory"], result["receipt_sha256"])
        after = peak_rss_bytes()
        receipt = verified["receipt"]
        return {"generated_only": True, "dimensions_wh": [width,height], "pixels": width*height,
                "full_payload_bytes": width*height*12,
                "baseline_post_import_peak_rss_bytes": before, "peak_rss_bytes": after,
                "incremental_high_water_bytes": max(0,after-before),
                "rss_units": "ru_maxrss bytes on macOS, KiB converted to bytes on Linux",
                "rss_scope": "process peak incl Python/imports; not current baseline RSS",
                "wall_seconds": time.perf_counter()-start,
                "memory_budget_pass": after <= full.CONTRACT["stress_peak_rss_limit_bytes"],
                "tile_pixel_cap": full.TILE_PIXELS, "numeric":receipt["numeric"],
                "full_array_evidence":receipt["files"]["full_rgb.npy"],
                "model_array_evidence":receipt["files"]["model_rgb.npy"],
                "original_size_wh": [width,height], "valid_box":receipt["valid_box"],
                "normalized_shape":list(verified["normalized_chw"].shape),
                "verified":True, "real_data_accessed":False}
    finally:
        # Remove only this function's newly created generated scratch files.
        shutil.rmtree(scratch)


if __name__ == "__main__":
    if len(sys.argv)!=3:
        raise SystemExit("Usage: measure_b1_streaming WIDTH HEIGHT (fixed generated sizes only)")
    print(json.dumps(measure(int(sys.argv[1]),int(sys.argv[2])),indent=2,allow_nan=False))
