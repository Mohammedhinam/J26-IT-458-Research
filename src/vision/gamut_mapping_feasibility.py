"""Generated-only study. No image paths, export hooks or approval authority."""
from hashlib import sha256
import json
import struct

import numpy as np
from PIL import Image, ImageCms, __version__ as PILLOW_VERSION, features

from src.vision import colour_policy as policy
from src.vision import colour_qa as qa
from src.vision import exploratory_bundle as legacy


INTENTS = {"relative": 1, "perceptual": 0, "saturation": 2, "absolute": 3}
METHODS = (*INTENTS, "lab_search")
SEARCH_STEPS = (8, 4, 2, 1)
SEARCH_SWEEPS = 2
# Fixed before execution: gamma, red/blue matrix expansion, layout, spot count.
CASES = {
    "identity": (None, 0, "interior", 0),
    "interior": (1.8, 0, "interior", 0),
    "shadows": (2.2, 0, "shadows", 0),
    "red_weak_1": (2.2, 2**-12, "spots", 1),
    "red_medium_1": (2.2, 2**-10, "spots", 1),
    "red_strong_1": (2.2, 2**-6, "spots", 1),
    "red_strong_10": (2.2, 2**-6, "spots", 10),
    "red_strong_11": (2.2, 2**-6, "spots", 11),
    "red_dense": (2.2, 2**-8, "red_palette", 0),
    "mixed": (2.2, 2**-8, "mixed", 100),
}


def _generated_profile(gamma, strength):
    """Generate known matrix/TRC bytes, never read a device/source profile."""
    raw = bytearray(ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes())
    # Fix generated creation bytes so repeated fixtures are byte-reproducible.
    raw[24:36] = struct.pack(">6H", 2026, 1, 1, 0, 0, 0)
    raw[84:100] = bytes(16)
    tags = {}
    for index in range(int.from_bytes(raw[128:132], "big")):
        start = 132 + index * 12
        tag = bytes(raw[start:start + 4])
        offset = int.from_bytes(raw[start + 4:start + 8], "big")
        tags[tag] = offset
        if gamma is not None and tag in (b"rTRC", b"gTRC", b"bTRC"):
            raw[start + 8:start + 12] = (16).to_bytes(4, "big")
            raw[offset:offset + 16] = b"para" + bytes(8) + struct.pack(">i", round(gamma * 65536))
    matrix = np.column_stack([np.array(struct.unpack(">3i", raw[tags[t] + 8:tags[t] + 20])) / 65536
                              for t in (b"rXYZ", b"gXYZ", b"bXYZ")])
    expansion = np.array([[1 + strength, 0, -strength], [0, 1, 0],
                          [-strength, 0, 1 + strength]])
    matrix = np.rint(matrix @ expansion * 65536) / 65536
    if not np.isfinite(matrix).all() or (matrix <= 0).any():
        raise ValueError("Generated fixture has invalid colourants")
    for channel, tag in enumerate((b"rXYZ", b"gXYZ", b"bXYZ")):
        raw[tags[tag] + 8:tags[tag] + 20] = struct.pack(">3i", *np.rint(matrix[:, channel] * 65536).astype(int))
    return bytes(raw), matrix


def make_fixture(name):
    """Only fixed generated cases are accepted; no paths, images or ICC inputs."""
    if type(name) is not str or name not in CASES:
        raise ValueError("Unknown generated fixture")
    gamma, strength, layout, spots = CASES[name]
    raw, matrix = _generated_profile(gamma, strength)
    interior = np.array([[64, 96, 128], [96, 128, 160], [128, 160, 192],
                         [80, 120, 160], [160, 100, 80]], dtype=np.uint8)
    red = np.array([[r, g, b] for r in (160, 208, 240)
                    for g in (16, 64) for b in (0, 16)], dtype=np.uint8)
    if layout in ("shadows", "mixed"):
        gray = np.arange(10000, dtype=np.uint16) % 32
        pixels = np.repeat(gray[:, None], 3, axis=1).astype(np.uint8)
    elif layout == "red_palette":
        pixels = np.resize(red, (10000, 3))
    elif layout == "interior":
        pixels = np.resize(interior, (10000, 3))
    else:
        pixels = np.full((10000, 3), 128, dtype=np.uint8)
    if layout == "spots":
        pixels[:spots] = [224, 48, 0]
    elif layout == "mixed":
        pixels[:spots] = np.resize(red, (spots, 3))
    image = Image.fromarray(pixels.reshape(100, 100, 3))
    image.info["icc_profile"] = raw
    return {"name": name, "image": image, "matrix": matrix, "gamma": gamma,
            "strength": strength, "provenance": "fixed_generated_only"}


def _pixels_only(image):
    clean = Image.frombytes("RGB", image.size, image.tobytes())
    clean.info["srgb"] = 1
    return clean


def _convert_intent(source, intent):
    source_profile = legacy.check_source_colour(source)
    destination = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB"))
    if not (ImageCms.isIntentSupported(source_profile, intent, 0) == 1
            and ImageCms.isIntentSupported(destination, intent, 1) == 1):
        raise ValueError("Requested intent unsupported; no fallback")
    converted = ImageCms.profileToProfile(source, source_profile, destination,
                                         outputMode="RGB", renderingIntent=intent, flags=0)
    return _pixels_only(converted)


def _local_search(source, baseline):
    """Bounded study-only Lab-error search; no optimality/clinical guarantee."""
    legacy.check_source_colour(source)
    values = np.asarray(source)
    unique, first, inverse = np.unique(values.reshape(-1, 3), axis=0,
                                      return_index=True, return_inverse=True)
    # Map the same source code consistently; never use spatial or label masks.
    codes = np.asarray(baseline).reshape(-1, 3)[first].copy()
    engine = qa._Transforms(source.info["icc_profile"])
    try:
        original = unique[None, ...]
        extended = qa._finite_transform(engine, engine.extended_srgb, original.astype(float) / 255, np.float64)[0]
        active = ((extended < -qa.GAMUT_EPSILON) | (extended > 1 + qa.GAMUT_EPSILON)).any(axis=1)
        selected = codes[active].copy()
        if not selected.size:
            return _pixels_only(baseline)
        target_lab = qa._finite_transform(engine, engine.source_lab, original, np.float64)[0, active]
        for step in SEARCH_STEPS:
            for _ in range(SEARCH_SWEEPS):
                for channel in range(3):
                    # Centre first makes equal-error updates deterministic/no-op.
                    candidates = np.repeat(selected[:, None, :], 3, axis=1)
                    candidates[:, 1, channel] = np.maximum(selected[:, channel].astype(int) - step, 0)
                    candidates[:, 2, channel] = np.minimum(selected[:, channel].astype(int) + step, 255)
                    labs = qa._finite_transform(engine, engine.output_lab,
                                                candidates.reshape(1, -1, 3), np.float64)
                    distances = np.linalg.norm(labs.reshape(-1, 3, 3) - target_lab[:, None, :], axis=2)
                    selected = candidates[np.arange(len(selected)), distances.argmin(axis=1)]
        codes[active] = selected
    finally:
        engine.close()
    return _pixels_only(Image.fromarray(codes[inverse].reshape(values.shape)))


def _measure(source, output):
    # Always retain ORIGINAL intrinsic relative-sRGB gamut evidence. Mapping a
    # bounded output cannot legitimately turn source excursions into zeros.
    report = qa.diagnose_forward_colour(source, output)
    verdict = policy.evaluate_option_a(report)
    checks = {k: v for k, v in verdict["checks"].items() if k != "prerequisites"}
    delta, gamut = report["forward_delta_e76_D50"], report["gamut"]
    return {"mean_delta_e": delta["mean"], "p99_9_upper": delta["percentile_bounds"]["99.9"][1],
            "max_delta_e": delta["max"], "source_gamut_pixels": gamut["pixels_outside"],
            "source_gamut_fraction": gamut["pixels_outside"] / report["pixels"],
            "source_max_excursion": gamut["max_excursion_normalized"],
            "reverse_rgb_max": report["reverse_rgb"]["per_pixel_max"]["max"],
            "frozen_numeric_checks": checks, "frozen_colour_budget_pass": all(checks.values()),
            "failed_numeric_checks": [k for k, passed in checks.items() if not passed],
            "production_eligible": False, "export_authorized": False,
            "output_bounded_rgb": output.mode == "RGB", "qa": report}


def evaluate_fixture(name):
    fixture = make_fixture(name)
    source = fixture["image"]
    before = source.tobytes(), dict(source.info)
    baseline = _convert_intent(source, 1)
    results = []
    for method in METHODS:
        try:
            output = (_local_search(source, baseline) if method == "lab_search"
                      else baseline if method == "relative" else _convert_intent(source, INTENTS[method]))
        except ValueError as error:
            if str(error) != "Requested intent unsupported; no fallback":
                raise
            results.append({"method": method, "status": "unsupported", "production_eligible": False})
            continue
        measured = _measure(source, output)
        measured.update(method=method, status="measured", pixels=10000,
                        rendering_intent=INTENTS.get(method), flags=0,
                        changed_pixels_from_baseline=int((np.asarray(output) != np.asarray(baseline)).any(axis=2).sum()),
                        output_rgb_sha256=sha256(output.tobytes()).hexdigest())
        results.append(measured)
    if (source.tobytes(), source.info) != before:
        raise ValueError("Generated source mutated")
    return {"fixture": name, "generated_only": True, "source_unchanged": True,
            "source_rgb_sha256": sha256(source.tobytes()).hexdigest(), "methods": results}


def negative_controls():
    """Reject invalid profiles and measure an intentionally wrong interpretation."""
    rejected = {}
    for case in ("malformed", "non_rgb", "unsupported_class"):
        fixture = make_fixture("interior")
        if case == "malformed":
            fixture["image"].info["icc_profile"] = b"not-an-icc-profile"
        else:
            raw = bytearray(fixture["image"].info["icc_profile"])
            raw[16:20] = b"GRAY" if case == "non_rgb" else raw[16:20]
            if case == "unsupported_class":
                raw[12:16] = b"prtr"
            fixture["image"].info["icc_profile"] = bytes(raw)
        try:
            _convert_intent(fixture["image"], 1)
        except ValueError:
            rejected[case] = "rejected_before_measurement"
        else:
            raise ValueError("Invalid generated control was accepted")
    source = make_fixture("interior")["image"]
    # Deliberate negative control: ignore the actual generated source profile.
    srgb = ImageCms.createProfile("sRGB")
    wrong = ImageCms.profileToProfile(source, srgb, srgb, outputMode="RGB", renderingIntent=1, flags=0)
    return {"invalid_profiles": rejected, "wrong_profile": _measure(source, _pixels_only(wrong))}


def run_study():
    return {"scope": "generated_only_non_production", "runtime": {"pillow": PILLOW_VERSION,
            "numpy": np.__version__, "lcms": features.version("littlecms2")},
            "fixtures": [evaluate_fixture(name) for name in CASES],
            "negative_controls": negative_controls(), "production_active": False,
            "real_data_accessed": False, "clinical_validation": False}


if __name__ == "__main__":
    print(json.dumps(run_study(), indent=2, allow_nan=False))
