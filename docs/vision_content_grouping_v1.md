# Vision content grouping and near-duplicate screen — v1

Date: 2026-10-14. Branch: vinuthan. **PROPOSED / PENDING qualified approval.**

## Prespecified method and source evidence

Reused audit_verified/integrity_results.json cached byte/pixel SHA-256 and dHash fingerprints; no image read/decode/hash recomputation, caption audit or extraction. Exact equality uses byte or RGB pixel hashes (pixel cache includes dimensions). Every original filename, split and source row is preserved in a separate ignored proposal artifact.
dHash is the existing 9×8 luminance/Lanczos thumbnail: horizontal adjacent-pixel comparisons produce 64 bits. Luminance is used only for this fingerprint, not classifier RGB inputs. The prespecified default candidate radius is 4 bits of 64 (6.25%). No threshold tuning, label/grade filtering, model outputs, selected-pair visual judgment or outcome-based choice occurred. The threshold is configurable for a separately documented future screen, not a learned clinical criterion.
Screen unique exact-content groups first, so aliases do not multiply candidate pairs. Candidate edges and transitive review components stay separate from confirmed groups. Connected does not mean every pair is near-identical. A dHash match may be a collision or different mouth; cropped/rotated/re-encoded duplicates may be missed. Candidates require qualified visual verification.

## Actual cached overlaps and new candidates

- Source records: 1096; exact content groups: 1082.
- Known byte-duplicate groups: 14; original cross-split groups: 8.
- Test / Training: 7 known pairs.
- Training / Training: 6 known pairs.
- Training / Validation: 1 known pairs.

| Known exact pair | Original member filenames/splits |
|---|---|
| 1 | Test 00943; Training 00271 |
| 2 | Test 00944; Training 00566 |
| 3 | Test 00945; Training 00273 |
| 4 | Test 00946; Training 00568 |
| 5 | Test 00947; Training 00275 |
| 6 | Test 00948; Training 00570 |
| 7 | Test 00949; Training 00572 |
| 8 | Training 00562; Training 00719 |
| 9 | Training 00564; Training 00720 |
| 10 | Training 00574; Training 00721 |
| 11 | Training 00576; Training 00722 |
| 12 | Training 00578; Training 00723 |
| 13 | Training 00580; Training 00724 |
| 14 | Training 00590; Validation 00735 |

- Newly screened near-candidate group pairs (exact aliases excluded): 54; cross-split candidate pairs: 11.
- Involved unique exact-content groups: 94; distinct source entries: 98; non-singleton review components: 40.
- Exact/near affected source-entry overlap: 8; union of affected source entries: 118. Overlapping aliases are not counted twice.

## Hypothetical label-blind counts — no split changes

Rule fixed before screening: Test > Validation > Training reservation. Pick the lexicographically first original filename within the reserved destination, without labels or scores. Preserve all aliases; representative is only proposed, not a selected training sample.

| Scenario | Training groups | Validation groups | Test groups | Total groups |
|---|---:|---:|---:|---:|
| Exact content only | 718 | 182 | 182 | 1082 |
| IF every near edge is verified (not confirmed) | 678 | 177 | 173 | 1028 |

Pair counts are not exclusions: shared edges are combined once per hypothetical component. Do not subtract the candidate-pair count from the image total. These counts include unresolved annotations and are not final eligibility or participants.

## Deterministic near-candidate examples (not visually verified)

| Left group source members | Right group source members | Hamming distance |
|---|---|---:|
| Training 00640 | Training 00653 | 4 |
| Test 01367 | Test 01352 | 4 |
| Training 00288 | Training 00121 | 4 |
| Training 00017 | Training 00494 | 4 |
| Training 00558 | Validation 00816 | 3 |
| Training 00365 | Training 00332 | 4 |
| Training 00166 | Validation 00798 | 3 |
| Training 00166 | Training 00314 | 4 |
| Validation 00772 | Validation 00734 | 4 |
| Training 00302 | Training 00410 | 3 |

All candidate edges, member filenames/original splits, cached source evidence and proposed placements are in the separate ignored content_grouping_proposed_v1.json artifact. This report does not export a training-ready manifest.

## Annotation conflicts and independence blockers

Cached qualified-referral ledger: 14 known exact pairs; 11 with differing complete tooth maps; 3 with ambiguous/incomplete box coverage. All require joint review. Historical three maximum-disagreement pairs are a subset, not three extra groups. No labels were compared to choose grouping settings or representatives.
Near-candidate member annotations remain as cached unresolved/provisional evidence; no consensus grade or new clinical judgment is assigned. All 274 incomplete-caption candidates remain unapproved. Earlier 339 QA flags are not cleared.
Participant IDs are not documented; content grouping cannot prove participant independence or exclude repeated people with visually different photos. No participant IDs are invented from filenames, metadata or fingerprints.
Signed proposal §§3.2/3.5 (pp.17–18/22) requires preventing split overlap and a frozen participant-grouped split if overlap exists. Supervisor must approve whether reserved content grouping is an acceptable documented implementation or specify a participant-grouped partition/identity procedure. This utility does not activate a final split or create a training-ready manifest.

## Approval gates

Qualified visual verification of candidates; joint annotation adjudication; participant/group-basis limitations; label-blind placement/representative policy; final reviewed labels and frozen split/eligibility approval. Training requires separate authorization. No MGI 0–4 definitions, RGB → image maximum → Grad-CAM or independent questionnaire architecture changed.

## Verification and cached provenance

- Cached integrity JSON SHA-256: `0c420ca47fe63f6eeb0a9b613286c6329490eb0a9fecd163671a49760cd0f969`. All 1,096 original rows are retained byte-for-byte as parsed values in proposed source-record fields.
- Focused suite: **51 passed, 0 failed, 0 skipped** (16 new grouping/screen checks + 35 existing Vision safety/fingerprint checks). The prior 90 caption/policy tests are historical and were not rerun; no caption QA/image audit repeated.
- Live cached regression confirms 14 exact groups, 8 original cross-split pairs, 1,082 exact contents, 54 near edges, 11 cross-split candidate edges, 40 review components and both hypothetical count tables. Synthetic checks cover label blindness, shuffled-input determinism, preservation, byte/pixel aliases, Hamming boundaries/collisions, representative reservation, invalid cache rejection and transitive double-counting.
- Post-screen annotation metadata only: 31 of the 98 near-involved source entries are already flagged by latest cached caption QA. This metadata did not select fingerprints, edges, thresholds, representatives or placements. Other candidate entries are not automatically approved.
