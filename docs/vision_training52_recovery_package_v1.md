# Training-52 recovery review package

2026-10-15 · branch `vinuthan`. **Review preparation is complete; every label and eligibility decision remains pending.** No training permission or final research approval is created here. Existing dirty work is preserved.

## Open the package

The local, ignored directory is:

`data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/training_recovery_review_v1_20261015/`

| File | Purpose |
|---|---|
| `index.html` | Searchable 52-case viewer with cached caption maps, TXT corroboration, retained hold reasons and deliberate links to Training originals. Images are not preloaded. |
| `training52_review_decisions.csv` | The exact 52 Training IDs, review routes and blank reviewer/date/grade fields. Every decision is pending. |
| `development121_partial_policy_links.csv` | Two Training and 119 Validation partial-caption cases. No Test rows or policy clearances. |
| `training52_cached_evidence.json` | Selected cached Training evidence and unchanged draft metadata; not a training manifest. |
| `reviewer_instructions.md` | Human roles, evidence requirements and instructions to save a separate reviewed copy. |
| `verification.json` | Input/output hashes, exact counts and nine passing artifact checks. |
| `build_review_recipe.py` | Reproducible cached-only recipe. It refuses to overwrite the existing output. |
| `external_metadata_research.json` | Safe public metadata for the external MIO lead; no dataset payload. |

Only the existing 914-record development draft and 52 selected Training QA objects were deserialized. The reader checks split metadata before label fields and discards Test/unselected bodies before JSON decoding. A malformed Test-body fixture verified this boundary. No original RGB, CSV, TXT, image header, checkpoint or Test label was opened. All 104 source links and the Training-caption link exist, verified using file metadata only. Original cached input hashes remain unchanged.

## Exact queue

| Disjoint primary queue | Count | Meaning |
|---|---:|---|
| Partial-caption flags | 2 | Training 01100 and 01101; technical flags, not clinical approval. |
| Other QA referrals | 45 | 14 histogram issues, 12 tooth-count issues, one count/unsupported-clause case, and 18 historical duplicate/near flags. |
| Additional group companions | 4 | 00272, 00571, 00584 and 00728. Individual consistency cannot clear group disputes. |
| NP015 | 1 | Training 00591, with an unresolved possible participant relation to Validation 00736. |
| **Total** | **52** | **All remain held; zero new eligible records.** |

An empty new QA-issue array does not clear the 18 records with historical/group flags. All 52 retain null approved grades, participant IDs and activated splits; qualified approval and training eligibility remain false. The draft has no explicit optional-policy eligibility field. The two partial-pattern IDs must be checked against existing policy evidence before any decision.

Overlapping flags cover 25 multi-image sources, 10 cross-split sources and nine protected-Test aliases. These are not additional exclusions.

## Conditional recovery bound

Eleven sources remain outside Training under the existing protection proposal:

- Nine protected-Test aliases: 00271, 00272, 00273, 00275, 00566, 00568, 00570, 00571 and 00572.
- Training 00590 shares content reserved for Validation under the proposal.
- Training 00591 is the unresolved NP015 source.

The remaining **41 sources represent 33 proposed content groups**: 26 single-source groups and seven multi-source groups containing 15 sources. If the proposed reservations/NP015 holds remain, all necessary label/identity/group approvals are obtained, and one representative per group is approved, 33 is the conditional maximum additional Training content units from this queue. They are **not 33 approved images or proven independent participants**. Current Training 680 would reach 713 only under that fully approved hypothetical scenario. Actual newly eligible count today is zero; some groups may remain unusable.

The wider partial-caption queue has 121 development sources, but only two are Training and 119 are Validation. Recovery mainly expands Validation coverage; it does not add 121 Training examples or create whole-image MGI 0. All 181 development holds and the separate 182 original Test images remain unchanged.

## Human help needed

1. A qualified dental/annotation reviewer resolves source disagreements and group companions jointly, checks partial-caption evidence, and records actual label provenance or retains uncertainty.
2. A supervisor/source custodian decides group reservation/representatives, NP015/global participant evidence and methodological limitations. Content-group IDs cannot become invented participant IDs.
3. Dataset creators may clarify consensus annotations, caption versions and anonymized source grouping. An [unsent request draft](vision_reviewer_source_requests_draft_v1.md) is ready; no message was sent.

The owner can organize filenames and evidence, but must not be presented as a qualified clinical reviewer without that qualification. A policy decision alone does not approve every clinical grade. A resolved grade alone does not release protected evaluation content or authorize training.

## Research alternatives

| Primary source | Verified finding | Remaining limitation |
|---|---|---|
| [Original dataset paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11462013/) | Expert per-tooth MGI annotations and captions. Best source for annotation/provenance clarification. | Our local evidence still lacks supported whole-image MGI 0. Author clarification is not automatic relabeling. |
| [MIO v2](https://zenodo.org/records/22047269), 21 August 2026 | Advertises 765 photos with Healthy/Gingivitis/Periodontitis categories. Its [public API metadata](https://zenodo.org/api/records/22047269) explicitly reports `license.id=cc-by-4.0` and `access_right=open`. | Not an MGI 0–4 schema. Healthy-category membership alone does not establish maximum-visible MGI 0. Qualified grading, compatible field of view, provenance, independence and approval remain required. Camera/source confounding must be considered. No payload downloaded. |
| [Wen et al., 2024](https://www.nature.com/articles/s41598-024-70311-y) | Studies photograph-level MGI 0–4. | Images are not public because of patient privacy. The availability statement offers the design/algorithm on request, not promised dataset access. Maximum-over-teeth equivalence is not explicit. |

The MIO v2 link and explicit licence metadata resolve the earlier HTML-only uncertainty. They do not establish an eligible external cohort. No external whole-image MGI-0 cohort has been qualified for this project. Existing healthy tooth crops remain a different task unit and cannot validate healthy whole-image predictions.

## Verification and next step

**Nine focused artifact checks passed; no model tests were rerun.** Checks cover selective Test non-deserialization, 52-case coverage, the queue partition, overlapping boundary counts, pending-field CSV round-trip, 121 development-only rows, 52 HTML cards without image preloading, inactive approval flags and unchanged cached inputs. A separate read-only count review agreed with the partition and overlap counts. Original data, source annotations, labels, splits, approvals and training gates are unchanged. No install, dataset download/upload, model run, commit or push.

Three points to defend:

- Select held Training records using `technical_candidate=false`, not `training_eligible=false`: all 914 draft records have the latter false.
- Count proposed content groups before discussing hypothetical extra examples; aliases do not create new content units.
- Keep reviewer fields blank and eligibility false until genuine decisions and the remaining gates are satisfied.

Viva: **Why 41 sources but only 33 possible content units?** Some are aliases in seven groups. One approved representative avoids duplicate counting, but participant independence remains unverified.

**Next human step:** obtain a qualified reviewer/source-custodian route for this prepared package. No Colab is needed now. Do not repeat the 54-pair review or previous colour/runtime qualification. No automatic seed-43 run, manifest expansion, packaging or retraining. The existing v3 pilot is provisional MGI 1–4 evidence; original five-grade research definitions and final gates remain intact.
