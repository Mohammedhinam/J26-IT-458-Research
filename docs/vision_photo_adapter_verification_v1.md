# Local photo adapter — generated verification, 2026-10-16

`src/vision/photo_explanation.py` reuses the qualified B1 JPEG converter/model sampling, four-output exploratory model and existing Grad-CAM. No research five-class definition or original trainer changed.

**16 focused tests passed, 0 failed/skipped**, including real generated-image ResNet-50/Grad-CAM execution on both CPU and Mac MPS. Original frozen tensors unchanged, hook cleanup, four-grade mapping, finite probability checks, exact shared model input, negative/above-one values, alignment, metadata-free PNG output, hash/registration-before-decode and unsupported-input rejection checked. These tests use generated profiles/pixels and weights=None, never real dental images/checkpoints.

The React → FastAPI → PhotoRuntime → generated ResNet-50 → Grad-CAM → React flow also passed locally. The deliberately synthetic result was marked “Synthetic check · MGI 4”; all three decoded output views were 40×24. This grade has no clinical meaning.

## Boundaries and limitations

- Default real demonstration has `vision_runtime=None`: new-photo controls disabled; API returns 503 before reading a photo body. Saved v3 examples remain available.
- Future opt-in `load_v3_runtime` requires the pinned completed v3 checkpoint SHA, correct four-grade schema, explicit provisional context and separately registered new-photo hashes. No untrusted pickle, default pretrained download or file scanner.
- Only RGB JPEG, ≤8 MiB, ≤40 million pixels, identity EXIF orientation, and the previously qualified embedded ICC hash are accepted. Generated tests bind independently generated profiles explicitly. Ordinary phone photos with missing/different ICC or rotated EXIF are currently **unsupported**. Do not advertise arbitrary-photo support.
- Registered source hashes establish which input the runtime owner allowed; they do not authenticate consent, identify participants, or automatically detect all study/Test/held images. The trusted caller must enforce input provenance. No study or held input was registered here.
- Canonical model input remains extended float B1. The original-view panel is explicitly a colour-managed, display-only clipped sRGB preview; it is not a claim of original JPEG byte/pixel identity or clinical colour fidelity. Original source bytes are never rewritten.
- Only in-memory uploaded bytes/outputs are used. Source EXIF/ICC contents are not returned or stored. Display geometry is preserved; Grad-CAM refers to the predicted grade.
- No validated MGI0 support, final clinical model, or improved dental accuracy is claimed.

Next real-photo integration requires a clearly authorized non-study input with compatible profile and the pinned local v3 checkpoint. Additional colour-profile/orientation support needs separately tested engineering work; no silent sRGB assumption. No real inference or training was performed in this task.
