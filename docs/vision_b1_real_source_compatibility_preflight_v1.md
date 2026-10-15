# B1 real-source JPEG/ICC compatibility preflight v1

Date: 2026-10-15 · Branch: `vinuthan` · Result: **FAIL — current B1 profile contract mismatch**

Scope: one read-only compatibility preflight of the pinned 733 provisional development candidates. No RGB decoding, image transformations, Test payload/label access, packaging or model execution.

## Coverage and result

| Evidence coverage | Compatible | Incompatible | Unknown |
|---|---:|---:|---:|
| Newly inspected JPEG/ICC headers: 679 Training + 53 Validation | 0 | 732 | 0 |
| Cached hash-bound detailed diagnosis: Training/00004 | 0 | 1 | 0 |
| **All 680 Training + 53 Validation** | **0** | **733** | **0** |

“Incompatible” means unsupported by the **current frozen B1 parser/contract**, not damaged images or clinically invalid colours. Zero unknown classifications does not establish real-source conversion readiness.

## Cached evidence reused first

- Prior packaging evidence recorded **733/733 full-source SHA-256 matches** and 733 passed source-header checks. These were not fresh full-file hash checks today.
- All 733 selected inventory path/hash/dimension records matched the pinned source plan. Existing evidence covers 181 excluded development records, NP015/protected/uncertain holds, zero selected Test records and zero known cross-split content collisions.
- Training/00004's existing detailed diagnosis already establishes unsupported `curv` single-gamma TRCs. It was **not reopened**. Its ICC identity with the other 732 sources was not assumed.
- Earlier Option A ICC acceptance is broader than the frozen B1 support contract and cannot establish B1 compatibility.

Relevant existing evidence: [source diagnosis](vision_colour_diagnostic_00004_v1.md), [B1 generated contract](vision_option_b1_generated_prototype_v1.md), [streaming qualification](vision_b1_full_resolution_qualification_v2.md), [generated exporter integration](vision_b1_generated_export_integration_v1.md).

## Minimum additional inspection

Because the cached inventory lacked the remaining candidates' B1-specific ICC structure, 732 development JPEG headers were inspected. Parsing stopped at the first Start of Scan; **zero entropy-coded scan bytes and zero RGB pixels were read**. Image decoder/export entry points were blocked during this check.

All 732 contain one byte-identical 480-byte ICC profile:
`2b8daf8cabe783b17f801e6687f57016b53c775a826269e21c51313083c9fefc`.

| Profile requirement | Observed in all newly inspected 732 | Current B1 outcome |
|---|---|---|
| ICC version | v2; monitor-class RGB / XYZ PCS | Frozen parser requires v4 |
| Channel transfer curves | Three `curv` tags, count 1, gamma 2.19921875 | Supports `para` types 0/3 only |
| Chromatic adaptation | No `chad` tag | Required by current contract |
| White-point semantics | D50 header illuminant; approximately D65 `wtpt`; matrix row sums approximately D50 | Does not meet required D50 `wtpt` contract |

The actual frozen parser rejected all 732 with first error `Unsupported ICC header/PCS`. The other support mismatches were established by separate header/tag inspection. Matrix tags were present and stable; no disallowed extra tag signatures were found. These observations do **not** justify treating missing adaptation evidence as identity or merely removing checks.

## JPEG, geometry and privacy findings

- All 732 new headers: baseline sequential JPEG (SOF 0xC0), 8-bit, three components, orientation 1. This is ordinary JPEG framing; real decoding through a B1 adapter remains untested.
- New header geometry matched the cache. Whole-cohort cached dimensions: 731 images at 7286×4863 and two at 6969×4641; within the existing 16384-side / 40-million-pixel bounds.
- All 732 report EXIF ColorSpace 65535 (uncalibrated). Embedded ICC interpretation remains necessary; do not assume untagged sRGB.
- EXIF, DateTime, GPS IFD, MakerNote and XMP presence were recorded for all 732. No malformed EXIF structures, JPEG comments or opaque APP13 segments were found.
- Private metadata values were not extracted or logged. GPS IFD contents/coordinates were not traversed. **Presence of GPSInfo does not establish a location leak.**
- Future derivatives still require the existing metadata-safe encoding and provenance checks. No derivative was made here.

## Preservation and limitations

All 733 selected source stat identities (device/inode/size/mtime/ctime) remained unchanged. All 732 newly inspected header digests matched on a second read. First-pass header bytes: **18,770,890**; the same headers were reread for preservation. There were no source writes.

Current preservation evidence is **cached whole-source SHA results plus live stat/header checks**, not a new cryptographic rehash of the unread JPEG scan payloads.

No source code, frozen policy, Option A safeguards, labels, manifests or authorization gates were changed. No tests or previous audits were rerun. Only this report and its [aggregate evidence](vision_b1_real_source_compatibility_evidence_v1.json) were created; existing diary/log/handoff files were preserved under this task's two-artifact limit.

## One next action

**Request separate authorization for a generated-only, explicitly versioned ICCv2 matrix/single-gamma support qualification**, including independently verified D50/D65/adaptation semantics. Preserve the existing contract and fail closed on other profiles; do not add fallback or silently loosen checks.

The existing exporter accepts generated recipes, not a qualified real JPEG adapter. After that narrow qualification, real decoder integration, full-cohort colour precision/memory checks and a fresh packaging authorization would still be required. This preflight grants no clinical, label, final-training or packaging approval.
