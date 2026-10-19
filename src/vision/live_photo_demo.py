"""Explicit local demo registration; no dataset scanning, training or downloads.

A hash-bound registry records which exact bytes may reach the existing photo
adapter. It records an owner's source declaration, not clinical approval or
proof of consent. Never register study, held, sealed Test or unknown-source
images. Generated verification is a separate, visibly synthetic scope.
"""

from dataclasses import replace
from datetime import date
from hashlib import sha256
import json
from pathlib import Path

from . import photo_explanation as photo


VERSION = "pp1-live-photo-registration-v1"
MAX_REGISTRY_BYTES = 64 * 1024


def _unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate registration field")
        result[key] = value
    return result


def load_registration(path, trusted_sha256):
    """Verify bytes before trusting scope, model, profile or input membership."""
    path = Path(path)
    if (not photo._digest(trusted_sha256) or path.is_symlink()
            or not path.is_file() or not 0 < path.stat().st_size <= MAX_REGISTRY_BYTES):
        raise ValueError("A bounded regular registration file and trusted SHA are required")
    with path.open("rb") as handle:
        raw = handle.read(MAX_REGISTRY_BYTES + 1)
    if len(raw) > MAX_REGISTRY_BYTES or sha256(raw).hexdigest() != trusted_sha256:
        raise ValueError("Registration SHA/size mismatch")

    def reject_constant(_):
        raise ValueError("Non-finite registration field")

    record = json.loads(raw, object_pairs_hook=_unique_fields, parse_constant=reject_constant)
    fields = {"version", "scope", "checkpoint_sha256", "profile_sha256", "inputs", "provenance"}
    if not isinstance(record, dict) or set(record) != fields or record["version"] != VERSION:
        raise ValueError("Unknown registration version or fields")
    if record["scope"] not in ("generated_verification", "local_nonstudy_demo"):
        raise ValueError("Unsupported live-demo scope")
    if record["checkpoint_sha256"] != photo.V3_CHECKPOINT_SHA:
        raise ValueError("Registration does not bind the verified v3 checkpoint")
    if not photo._digest(record["profile_sha256"]):
        raise ValueError("A qualified profile hash is required")
    generated = record["scope"] == "generated_verification"
    origin = "generated" if generated else "owner_supplied_nonstudy"
    inputs = record["inputs"]
    if (not isinstance(inputs, dict) or not inputs
            or any(not photo._digest(key) or value != origin for key, value in inputs.items())):
        raise ValueError("Invalid input registration provenance")
    provenance = record["provenance"]
    if not isinstance(provenance, dict):
        raise ValueError("Source provenance is required")
    if generated:
        if provenance != {"kind": "generated"}:
            raise ValueError("Generated verification cannot claim human approval")
    else:
        if record["profile_sha256"] != photo.QUALIFIED_PROFILE_SHA:
            raise ValueError("Real-photo profile is not qualified by this version")
        expected = {"kind", "reviewer", "date", "evidence_reference"}
        if (set(provenance) != expected or provenance["kind"] != origin
                or any(not isinstance(provenance[key], str) or not provenance[key].strip()
                       for key in ("reviewer", "date", "evidence_reference"))):
            raise ValueError("Owner source declaration/reviewer/date/reference are missing")
        if date.fromisoformat(provenance["date"]).isoformat() != provenance["date"]:
            raise ValueError("Source decision date must be ISO YYYY-MM-DD")
    return record


def build_runtime(checkpoint, registry, trusted_sha256):
    """No fallback: bad bindings stop startup before a photo can be decoded."""
    record = load_registration(registry, trusted_sha256)
    generated = record["scope"] == "generated_verification"
    runtime = photo.load_v3_runtime(checkpoint, record["inputs"], synthetic_only=generated)
    if generated:
        # Generated fixtures have their own explicit profile; real scope stays pinned.
        runtime = replace(runtime, allowed_inputs=dict(runtime.allowed_inputs),
                          profile_sha256=record["profile_sha256"])
    return runtime
