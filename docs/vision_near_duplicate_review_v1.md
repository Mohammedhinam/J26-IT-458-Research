# Label-blind near-duplicate visual review artifacts — v1

Date: 2026-10-14. Branch: `vinuthan`. **Human review pending: 54/54 decisions pending.**

Reused `vision_content_grouping_v1.md` and the ignored `content_grouping_proposed_v1.json`. No screening, hashing, caption QA or full dataset audit repeated. Original RGB files were opened only to create aspect-preserving display thumbnails; no enhancement, colour grading, clinical interpretation or model inference.

| Review category | Candidate pairs / contact sheets | Pending decisions |
|---|---:|---:|
| Cross-split: Training–Validation | 4 | 4 |
| Cross-split: Test–Validation | 3 | 3 |
| Cross-split: Training–Test | 4 | 4 |
| **Cross-split total, shown first** | **11** | **11** |
| Within Training | 32 | 32 |
| Within Validation | 2 | 2 |
| Within Test | 9 | 9 |
| **Within-split total** | **43** | **43** |
| **All pairs** | **54** | **54** |

Cross-split subtotal rows overlap their individual categories; do not add subtotals again. The 54 sheets show 108 image panels using 94 unique original RGB preview sources. All original aliases remain listed/linked, including 98 source entries associated with the 94 candidate-involved exact-content groups. Preview file choice reuses the prior label-blind representative; it does not select any training sample.

## Exact local artifact locations

Root:

`/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/near_duplicate_review_v1/`

| Artifact | Contents |
|---|---|
| `index.html` | Reviewer entry page: 11 cross-split pairs first, then within-split groups; full-resolution source links for both sides and every exact alias |
| `cross_split/NP*.png` | 11 side-by-side RGB sheets, filenames, original splits, component ID and cached dHash distance |
| `within_split/NP*.png` | 43 side-by-side RGB sheets, separated from cross-split review |
| `review_pairs.csv` | 54 rows; stable pair/component IDs, group IDs, source aliases, distance, sheet path; every decision pending; reviewer/date/notes blank |
| `review_pairs.json` | Same sanitized, label-blind pair evidence |
| `review_components.json` | All 40 inherited candidate components, original group IDs/source paths and pair relationships; none marked visually verified |
| `confirmed_exact_groups.json` | All 14 existing confirmed byte-duplicate groups retained exactly as cached, including original member paths/splits |
| `decision_options.json` | Permitted human decisions: pending, visually_same_content, distinct, uncertain; no clinical or participant-identity approval |
| `build_review.py` | New artifact-only rendering recipe; exclusive output creation protects existing artifacts |

All raw review artifacts remain inside ignored data/. No grade labels, caption text, TXT grades, clinical QA flags or model/test outcomes are exported into the review CSV, JSONs, sheets or viewer. Do not link the original proposal JSON as a label-blind reviewer view; it contains source annotation metadata. Use these sanitized artifacts instead.

## Review instructions and limits

Inspect image content only, using full-resolution links where needed. Record one of the four allowed decisions plus reviewer/date/notes in the review CSV. `visually_same_content` is a human content finding, not a clinical grade or participant-identity claim. Use `uncertain` when photographic correspondence cannot be established. `distinct` does not prove different people. Human decisions do not automatically merge candidate groups, change original memberships, approve labels or activate the proposed split.

The 40 components preserve the screening graph; shared component membership is not automatic content equivalence or proof that every pair is near-identical. Exact-group evidence remains separate. All 274 incomplete-caption candidates and existing clinical/annotation approvals remain pending and untouched. Final-test photographs are displayed solely for the authorized integrity review, never model development, selection or inference.

## Verification performed

- 54 unique candidate IDs, 54 RGB PNG sheets (1800×800), 54 CSV rows; 11 cross-split rows first. Every reviewer decision pending and identity/date/notes fields blank.
- All 40 component relationships and 14 cached exact-group structures match their original proposal evidence.
- All 169 viewer links resolve, including contact sheets and original image/alias files.
- Generated sheets contain no EXIF metadata. Sources are not enhanced, cropped, converted to grayscale or overwritten; only display resizing is applied.
- Three representative sheets were inspected for layout, colour presentation, filenames, alias labels and footer visibility. No duplicate or clinical judgment was assigned. Human verification of all pairs remains outstanding.
- Mechanical artifact checks passed. No new pytest suite or prior audits were rerun for this rendering task.

No installations, training, relabeling, split changes, source-manifest modification, commits or pushes. Existing tracked/untracked work and prior reports are preserved.
