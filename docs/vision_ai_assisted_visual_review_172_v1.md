# AI-assisted visual screen of 172 held development images (local-only)

Date: 2026-10-16. This is a non-clinical visual screen to organise qualified review. It is not a dental diagnosis, label approval, or evidence of model performance.

## Scope and method

- Screened **172 held development records** in their original splits: **43 Training + 129 Validation**. The nine protected Test aliases (`00271`, `00272`, `00273`, `00275`, `00566`, `00568`, `00570`, `00571`, `00572`) were excluded; no sealed Test image or label was opened.
- Used original RGB previews, upper/lower ROI crops and YOLO overlays in **43 local contact sheets, four records per sheet**. Compared the three original caption variants with the associated TXT grade histogram and retained QA flags. Captions are primary evidence; TXT supports grade-count corroboration only and cannot verify FDI tooth identity.
- Review was at reduced contact-sheet scale on an uncalibrated display. It can flag obvious structural issues, but it cannot reliably distinguish subtle MGI 0/1/2 clinical findings. Therefore **no provisional visual grade was assigned**. Every record remains `needs_qualified_dental_review`; reviewer/date fields are blank.
- Rechecked selected source image and TXT SHA-256 values against the hash-bound preflight: **172/172 images and 172/172 TXT files matched**. This review read only selected Training/Validation files. Originals, captions, annotations, labels and split membership were not modified.

## Caption-derived candidate evidence (all pending)

These are candidates retained from captions, not visual suggestions or approved labels. The 121 lower-jaw-omission cases use matching complete Caption 1/2 evidence only as a **pending policy check**; no policy was activated.

| Original split | MGI 0 | MGI 1 | MGI 2 | MGI 3 | MGI 4 | Caption candidates | Unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|
| Training | 0 | 0 | 3 | 4 | 35 | 42 | 1 |
| Validation | 0 | 1 | 4 | 59 | 60 | 124 | 5 |
| Total | 0 | 1 | 7 | 63 | 95 | 166 | 6 |

No MGI 0 whole-image candidate appears in this reviewed set. MGI 1 is represented by one pending Validation candidate; MGI 2 by seven pending candidates. These counts do not solve class support and must not be described as approved training labels.

## Findings and overlap

| Evidence flag | Records | Interpretation |
|---|---:|---|
| Incomplete Caption 3 / lower-jaw omission pattern | 121 | The same records carry both structural flags; policy remains unapproved. |
| Caption/TXT grade-histogram disagreement | 16 | TXT has no tooth IDs; discrepancies need qualified review. |
| YOLO annotation/tooth-count review | 12 | Count/box evidence needs human inspection; no automatic correction. |
| Exact repeated YOLO annotation line(s) | 4 | `00060, 00085, 00484, 00811`; structural anomaly only, not auto-deleted. |
| Caption declared-count mismatch | 6 | These same records also have unsupported-grade-clause flags. |
| Unsupported caption grade clause | 6 | Same records as declared-count mismatch. |
| Any cached QA flag | 155 | Unique records; flag counts overlap. |
| No cached QA flag | 17 | Still pending qualified label review; no flag is not approval. |

At the viewed scale, ROI boxes generally tracked broad anterior regions; no confident per-tooth or FDI correspondence can be claimed. The 12 count-review cases and 4 exact repeated annotation-row cases remain review items. **No suspected visual mislabel was strong enough to recommend changing a grade.**

## Files and limits

- Local review CSV (ignored/private data area): `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/ai_assist_visual_review_v1_20261016/ai_assisted_visual_review_172_v1.LOCAL_ONLY.csv`
- Contact sheets: `data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/ai_assist_visual_review_v1_20261016/contact_sheets/batch_01_...` through `batch_43_...`; actual filenames are linked row-by-row in the CSV.
- This screen does not clear any `needs_review`, approve labels, change the 181-hold ledger, admit held images, alter splits, or establish participant independence. No training, inference, upload, installation, commit or push occurred.

**Next:** A qualified dental/annotation reviewer should inspect full-resolution originals for the pending MGI evidence and annotation conflicts, record reviewer identity/qualification/date and rationale in a new versioned decision record, and leave uncertain cases unresolved. Supervisor approval is separately required for an incomplete-caption policy or manifest change.

## Priority records for a qualified reviewer

These identifiers are useful for triage only; they are not visual re-grades:

- Pending MGI 1 caption candidate: `Validation/00821` (caption/TXT histogram disagreement).
- Pending MGI 2 caption candidates: `Training/00060`, `Training/00085`, `Training/00709`, `Validation/01136`, `Validation/01157`, `Validation/01193`, `Validation/01217`. `00060` and `00085` have annotation/tooth-count flags; `00709` has a caption/TXT histogram disagreement; the four Validation cases have the pending lower-jaw-omission pattern.
- Earlier example `Training/00025` remains a pending MGI 4 caption candidate with a caption/TXT histogram disagreement.

A qualified reviewer should use the full-resolution original plus caption/TXT evidence for these cases. Do not let an AI visual impression or the TXT histogram decide the clinical grade.
