# Gemini review candidates — read-only preflight v1

16 October 2026 · branch `vinuthan`.

**Source integrity, annotation association and ICC structure: PASS. External release: BLOCKED.** All 172 selected sources remain local; no upload, image export, external package, model training or approval was performed. The owner explicitly did not accept Personal Gemini's data-processing risks; acceptance/upload permission remain false.

## Scope and exact results

Selected43 Training + 129 Validation = 172 proposed review candidates from the existing local plan. All9 protected Test-content aliases were excluded before source access. No originalTest files, protected-alias JPEG/TXT or their caption fields were inspected. The shared Training/Validation CSV files were streamed by filename; only selected caption fields were parsed. No original split/group/hold decision changed.

| Check | Pass | Fail | What this establishes |
|---|---:|---:|---|
| Source JPEG SHA256 matches cached audit reference | 172 | 0 | Same source bytes as the existing verified local inventory, not independent publisher authentication |
| Source JPEG hashes/stat identities preserved before/after | 172 | 0 | Selected sources not changed during this check |
| Image filename / three caption variants / TXT association | 172 | 0 | Exactly516 selected caption variants, numbered1/2/3, with matching IDs/splits |
| Existing parser output reproduces cached caption evidence | 172 | 0 | Existing source interpretation reproduced; no new clinical labels |
| TXT histogram reproduces cached evidence | 172 | 0 | No new mismatch against cached TXT counts |
| TXT finite geometry / boxes within image | 172 | 0 | Valid numerical box geometry, not proof of correct tooth correspondence |
| One upper and one lower ROI annotation | 172 | 0 | Expected two ROI classes present |
| JPEG mode / dimensions / orientation / resource bounds | 172 | 0 | RGB JPEG headers,7286×4863,orientation1; no pixel decoding performed |
| Existing strict ICCv2 structural compatibility | 172 | 0 | Supported matrix/TRC profile family, not clinical colour fidelity |
| Originals privacy-clear for verbatim external upload | **0** | **172** | Embedded metadata prohibits treating originals as sanitised upload payloads |

All 172 TXT files and both source caption CSVs retained identical live hashes/stat evidence during inspection. A historical bytehash reference for the original annotation files was not available in the reused inventory; annotation preservation and cached semantic reproduction were verified, not archive/publisher byte authenticity. Original image hashes do have cached references.

These are check-specific results on the same172 records, not separate samples or a new full-repository test run. **14 independent saved-evidence assertions passed,0 failed.** Earlier unrelated tests, image audits and generatedICCqualification were not rerun.

## Privacy findings: presence only

| Header field / container | Sources with presence |
|---|---:|
| EXIF | 172 |
| DateTime-related tags | 172 |
| GPSInfo | 172 |
| GPS IFD contains only version field | 172 |
| GPS coordinate fields | **0** |
| Opaque MakerNote | 172 |
| XMP | 172 |
| Checked identity/serial/owner tags | 0 |
| Checked artist/description tags | 0 |
| JPEG comment / opaque APP13 | 0 / 0 |

No timestamps, GPS values, serials, MakerNote/XMP text, raw EXIF, source ICC bytes or pixel arrays were saved or printed. **GPSInfo presence is not a confirmed location leak:** no latitude/longitude fields were found in the inspected GPS IFDs. This limited header screen does not establish complete anonymity of an intraoral photograph or rule out identifying content in opaque metadata. MakerNote/XMP remain uninterpreted; their presence alone blocks a claim of metadata-safe verbatim copying.

## ICC / colour-integrity interpretation

All 172headers contain the same480-byte profile, SHA256:

`2b8daf8cabe783b17f801e6687f57016b53c775a826269e21c51313083c9fefc`

The existing qualified parser accepts its ICCv2 monitor-class RGB/matrix/single-gamma`curv`structure: gamma2.19921875perchannel,XYZD50PCS and supportedD65media-white handling. The actual172headers match this family; prior733candidate compatibility did not establish their compatibility by assumption. Missing`chad`was not treated as identity adaptation or silently repaired. Private profile text was not decoded or saved.

**No decoded-pixel colour check or source→derivative transform was performed.** Exported-display equivalence, clipping/DeltaE, clinical colour accuracy, a canonical metadata-safe ICC replacement, and a Gemini-consumable derivative remain **not evaluated**, not “172passed.” Original byte/geometry/profile integrity is established; it does not certify a future RGB export. Do not strip ICC blindly, route through failed OptionA, replace a source profile or reuse B1floatNPY as an image upload without a separately qualified pathway.

## Annotation conflicts remain unresolved

The source files match their cached evidence; this does not mean captions agree with TXT or that labels are qualified-approved. Existing overlapping flags among the172 records remain:

- 16 caption/TXT histogram discrepancies.
- 12 annotation-tooth-count reviews.
- 6 declared-tooth-count mismatches and 6 unsupported-grade-clause flags.
- 121 incomplete-caption/lower-jaw-omission flags (same cases, not 242 new records).

Group/identity holds, including NP015, remain unchanged. All review statuses are pending; zero clinical grades or training eligibility were approved. TXT does not encode explicit FDI identities. No clinical reasoning, fresh grading, relabeling or held-image recovery was attempted.

## Licence versus external-processing permission

The current [official Mendeley version1record](https://data.mendeley.com/datasets/3253gj88rr/1) confirms **CC BY4.0**, DOI10.17632/3253gj88rr.1 and contributor Duy Hoang Bao. Appropriate attribution, licence link and indication of any changes are required. The [CCBY4.0deed](https://creativecommons.org/licenses/by/4.0/) explicitly states that other privacy/publicity/moral rights may affect intended use. A public copyright licence is not a completed image-privacy or service-specific permission assessment.

Existing project permission/ethics review in `vision_development_packaging_preflight_v1.md` was reused. It documents the paper's research/IRB statements but does not supply individual consent records or evidence specifically approving this project's Personal Gemini workflow. No new doctor/institutional/source-custodian approval was found in the **reviewed relevant records**; this was not a repository-wide legal search. Whether further institutional/source permission is applicable remains unresolved, not an asserted universal requirement or proven prohibition.

Personal Gemini web/app is owner-confirmed. Its [official privacy notice](https://support.google.com/gemini/answer/13594961?hl=en), checked16October2026, covers uploaded content and some human review/retention; activity-off does not guarantee no processing or human review. Consumer terms cannot be replaced by assumed Workspace/API protections. No account setting was changed or inspected.

| Permission state for intended external review | Candidates |
|---|---:|
| Specific external-processing permission established in reviewed evidence | **0** |
| Specific permission unresolved | **172** |
| Specific refusal established | **0** |

The user's current authorization covers local read-only inspection only. PersonalGemini risk acceptance, external packaging, upload, final label approval and training remain **not authorized**. Do not infer consent from this preflight's completion or from account identification.

## Execution, preservation and evidence

Ignored local diagnostic directory:

```text
/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gemini_readonly_preflight_v1_20261016T165336458230Z/
```

Contains `owner_scope.json`, a local diagnostic script, non-sensitive per-case hashes/header-presence results, aggregate results and independent verification. It contains **no original images, ICC payloads, raw captions/TXT copies, exports, upload package or ZIP**. Public aggregate evidence: [vision_gemini_readonly_preflight_evidence_v1.json](vision_gemini_readonly_preflight_evidence_v1.json).

The diagnostic reused selective cached development hash/dimension parsing, existing caption parser and strict ICC structure mathematics. Dataset/model access was allowlisted to selected172JPEG/TXTfiles, two shared developmentCSVs and named cached artifacts. Source writes/network connections were blocked, and Pillow pixel-loading methods raised if called. Full source bytehashing reads compressed JPEG bytes without decoding pixels. Both source hashes/stat identities were checked before/after; master tracker and cached review evidence also remain hash-identical.

An initial helper setup stopped at the Validation CSV schema before image checks: it has the existing extra`Vùng`column. The selector was adjusted to that observed header; no original data, safety bounds or colour policy was altered. Initial failure evidence is retained, not hidden. The completed selected-source pass took1.309seconds; this is a measured local run, not a benchmark. No clinical dataset/model experiments, installs, external-data upload/download, commits or pushes.

## Safest next action

**Keep these172originals local and qualify a generated-image-only, lossless JPEG metadata-sanitisation / non-identifying ICC-preservation design.** It must preserve decoded content, full geometry, filenames and colour interpretation without copying private metadata or silently converting/clipping. This recommendation is not implementation/export permission; no such route is activated here. Applicable external-processing rights and separate owner acceptance/upload authorization must also be resolved before any actual release. Do not package first and seek permission afterwards.

Tamil: Source files மற்றும் caption/TXT matching சரியாக உள்ளன. ஆனால் 172 originals-லும் metadata இருப்பதால் அப்படியே upload செய்யும் அனுமதி உருவாகவில்லை. ICC structure pass என்பது exported colours validated என்று அர்த்தமில்லை. ஒன்பது Test aliases வெளியிலேயே உள்ளன. External-processing permission unresolved; Personal Gemini risks ஏற்றதாக owner முடிவு எதுவும் பதிவு செய்யப்படவில்லை.

Viva: **Why can source integrity pass while upload readiness fails?** The same intact original can contain metadata that should not leave local storage. A hash proves byte identity, not privacy or clinical truth.
