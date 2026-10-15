# Owner-confirmed near-duplicate review mapping — v1

Date: 2026-10-14. Branch: `vinuthan`. **54 mapped human review records; no clinical/split/group approval activated.**

Owner Vinuthan T directly confirmed reviewing all 54 pairs in the exact top-to-bottom `index.html` order without skips, identified the first two as distinct photographs, and confirmed the RC030/RC038 corrections and RC014 uncertainty. The assistant maps recorded decisions; it does not supply substitute human judgments.

## Exact final mapped decisions

| Review bucket | Mapped pairs | distinct | visually_same_content | uncertain | pending |
|---|---:|---:|---:|---:|---:|
| Cross-split | 11 | 8 | 2 | 1 | 0 |
| Within Training | 32 | 30 | 2 | 0 | 0 |
| Within Validation | 2 | 2 | 0 | 0 | 0 |
| Within Test | 9 | 7 | 2 | 0 | 0 |
| **Total** | **54** | **47** | **6** | **1** | **0** |

All 54 decisions are mapped; 53 are definitive content dispositions and one explicitly records uncertainty. This is not 54 confirmed independent participants or 54 cleared clinical labels. The six owner-reported visually-same pairs do not increase the 14 byte-exact pairs to 20 automatically; the units/evidence differ and group relationships overlap.

Same-content pair IDs: **NP033, NP036, NP040, NP041, NP046, NP053**. Uncertain: **NP015** (RC014), Validation `00736.jpg` versus Training `00591.jpg`.

## Mapping and explicit corrections

- Spoken rows 1–54 mapped using owner-confirmed viewer order, not NP numeric order or RC-only matching. All 54 NP IDs are unique and cover the original register exactly.
- All 52 stated RC IDs agree with the corresponding viewer positions; zero mapping conflicts. First two missing RCs are owner-confirmed **NP005/RC005** and **NP007/RC007**, both `distinct`.
- **RC030 → NP037 and NP038: distinct**, per the latest direct owner correction. The original uncertain wording remains preserved in source-prefixed columns.
- **RC038 → NP046 and NP053: visually_same_content**, per the latest direct owner correction. Earlier conflicting spoken wording remains preserved, not erased.
- **RC014 → NP015: uncertain**; note: possible participant overlap, not verified. Same-mouth/different-angle wording is not converted into same-photo approval or an asserted participant identity.

## New versioned local artifacts

Directory, kept inside ignored data/:

`data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/near_duplicate_review_v1/`

- `review_pairs_reviewed_v1_20261014.csv` — original pair/group/source/split/alias metadata, mapped human decisions, reviewer/date/notes, review scope, source hashes and all uploaded spoken fields preserved under `source_` columns.
- `review_pairs_reviewed_v1_20261014_provenance.json` — owner confirmation, mapping method, corrections, input hashes, final counts and output checksum.

Original source `/Users/vinuthanvinuthan/Downloads/near_duplicate_spoken_review_corrected_20261014.csv`, original `review_pairs.csv`, original `index.html` and all existing reviewer artifacts are unchanged. The original register/viewer still show their historical pending snapshot; the **new versioned CSV is the current human decision record**, not an overwritten source file.

## Verification and scientific boundaries

Saved CSV re-parses to the prepared 54 records with every value intact. IDs, RC/order checks, source filenames/splits/aliases, corrections, owner provenance and decision totals match. Original source/register/viewer hashes are unchanged. Scientific approval flags remain false. No original RGB image, caption/TXT, QA status, cached group, split or label was edited; no image opened for a new AI adjudication, audit, hashing, model training/inference, install, commit or push.

Qualified label/clinical adjudication, incomplete-caption policy approval, exact/near-group placement, unknown participant identity, absent MGI 0 support, final frozen eligibility/manifest and training protocol remain pending. The 274 policy candidates and 339 QA records are not cleared by these human image-content decisions. Final-Test content was reviewed for dataset integrity only, not model development/selection.

Next approval issue: NP015 uncertainty/possible participant overlap, plus qualified approval of group treatment using the recorded decisions. No automatic merge, resplit, label change, exclusion or training-ready manifest is produced.
