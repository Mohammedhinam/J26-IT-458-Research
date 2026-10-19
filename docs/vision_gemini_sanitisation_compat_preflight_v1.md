# Gemini JPEG sanitiser compatibility preflight v1

Date: 2026-10-16 (Asia/Kolkata). **JPEG header/ICC/XMP structure compatible for all selected candidates; privacy release remains blocked.**

## Scope and method

This was a local, read-only preflight of the already selected **172 development candidates: 43 Training and 129 Validation**. It reused the hash-bound 172-case evidence; it did not read the master list's nine protected Test aliases. The diagnostic opened only selected JPEGs, read their compressed bytes to check the cached SHA-256, and parsed JPEG headers through the SOS marker. It did not decode RGB pixels, inspect image appearance, read captions/TXT, export, upload, or train. ICC profile data and XMP XML were parsed in memory; their private text values were not saved or printed.

## Exact results

| Check | Pass | Fail / unresolved | Result |
|---|---:|---:|---|
| Selected candidates | 172 | 0 | 43 Training + 129 Validation |
| Current JPEG SHA matches previous hash-bound preflight | 172 | 0 | Source bytes match cached values |
| Source file identity/stat unchanged during check | 172 | 0 | Read-only check preserved files |
| Header geometry matches cached 7286×4863 | 172 | 0 | No RGB decode |
| JPEG coding/header subset used by the sanitizer | 172 | 0 | Baseline RGB8 SOF0 and supported SOS/header markers |
| ICC profile bytes match the known shared 480-byte profile | 172 | 0 | One profile SHA: `2b8daf8cabe783b17f801e6687f57016b53c775a826269e21c51313083c9fefc` |
| ICC structure matches the previously supported matrix/TRC subset | 172 | 0 | Tag signatures are `wtpt`, RGB `XYZ`, RGB `TRC`, `desc`, `cprt`; RGB profile parsed successfully |
| XMP packet structure accepted by metadata-only removal rule | 172 | 0 | One standard XMP packet per candidate; no unsupported/extended schema detected |
| Protected Test aliases accessed | 0 | 9 | All nine stayed outside the selected case list |
| Personal Gemini permission confirmed | 0 | 172 | External processing remains unresolved |

The sanitizer's generated tests show it can remove metadata-only XMP while retaining image bytes and ICC. This preflight establishes that the selected XMP packet structures fit that rule. It does **not** execute the production sanitizer on real images, nor inspect post-SOS scan data for hidden trailing content; its full-file fail-closed checks remain for any separately authorized derivative run.

## Remaining blockers

1. The common ICC profile contains `desc` and `cprt` text fields. Their values were deliberately not retained or shown. A common profile hash does not prove that those fields are non-identifying. Therefore the profile is structurally compatible but **not approved for the sanitizer's trusted ICC hash allowlist**.
2. Personal Gemini data-processing risk acceptance and specific external-processing permission are still unresolved for all 172 candidates. CC BY 4.0 attribution alone does not establish those permissions.
3. No real JPEG has been sanitized or exported. The nine protected Test aliases, all source files, labels, and splits remain untouched.

## Safest next action

The owner should inspect the shared profile's `desc` and `cprt` values locally (they are not included here). If the profile is judged non-identifying, give a separate, explicit authorization to allowlist this one ICC SHA-256 **for local sanitised derivatives only**. External Gemini processing still requires its own permission/risk decision. Until both gates are resolved, keep original files local and create no upload package.

Evidence with aggregate counts and safeguards: [vision_gemini_sanitisation_compat_preflight_v1.json](vision_gemini_sanitisation_compat_preflight_v1.json). Prior generated JPEG qualification: [vision_jpeg_metadata_qualification_v1.md](vision_jpeg_metadata_qualification_v1.md).

Viva: **Why can the JPEG headers pass while upload stays blocked?** The formats can be handled safely, while the shared ICC text fields and external processing permission remain unresolved.
