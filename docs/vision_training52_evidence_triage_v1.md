# Training-52 held-image evidence triage

Date: 2026-10-17 · Branch: `vinuthan` · Read-only review of cached evidence.

> Provisional labels; non-clinical; non-final; participant independence unverified.

## Scope and inputs

This triage reuses the existing [Training-52 review package](vision_training52_recovery_package_v1.md), specifically its ignored `training52_cached_evidence.json`, `training52_review_decisions.csv`, and `verification.json`. It does not repeat caption parsing, open original RGB images, reread original CSV/TXT files, or open Test images/labels. All 52 selected rows are original Training records. Their decisions remain pending; the cache says `labels_approved=false`, `training_ready=false`, and `activated=false`.

Input SHA-256:

- Cached evidence: `65ab81bc6ed28687b7e8ef2a5630de20fe7353212c15b3b3c83277a519b83c20`
- Decision CSV: `5e6aaaf88968fad759c38b07bd87c2271794c51bf662e3020fa08bf23b5ddaa5`
- Package verification: `13662b5b1b8ca9c2059c1cca0db83f0cfa7ec21e5789cc9296fc42da3fbc99bb`

## What the cached evidence says

| Cached finding | Count | Meaning for review |
|---|---:|---|
| Caption/TXT grade-histogram disagreement | 14 | Explicit annotation conflict; resolve first. IDs: `00025, 00052, 00097, 00122, 00224, 00277, 00289, 00298, 00358, 00469, 00575, 00576, 00649, 00709`. |
| Annotation tooth-count review | 12 | Structural/count question; no complete-caption check is recorded for these IDs: `00060, 00085, 00484, 00537, 00557, 00568, 00602, 00657, 00667, 00673, 00676, 00702`. |
| Additional declared-count / unsupported-clause issue | 1 | `00162`; the cached parser has no supported candidate maximum. |
| Incomplete-caption policy pending | 2 | `01100, 01101`; no candidate maximum is established and the optional policy is not approved. |
| Group companion / identity-only route | 5 | Four group companions plus NP015 `00591`; group or possible participant overlap remains a separate hold. |

The review queue itself is disjoint: **45 annotation referrals, 4 additional group companions, 1 NP015 identity hold, and 2 partial-caption cases = 52**. Individual issue flags can overlap and must not be added to that queue total.

### Maximum agreement is weaker than annotation agreement

Among 49 records with a parsed caption candidate maximum, that maximum matches the highest nonzero grade bin in the cached TXT histogram for **47**. It differs for **2** (`00097`, `00358`). Three have no parsed caption maximum (`00162`, `01100`, `01101`).

The cache contains complete-caption histogram checks for 40 records: all recorded checks agree for 26, while at least one check disagrees for 14. Several of the 26 still have an independent count, group, protected-content, or NP015 hold. For 12 histogram-conflict cases, the *maximum alone* matches even though the full grade histogram does not. Therefore, a matching maximum is only partial technical corroboration; it does **not** prove tooth-level correctness, clinical truth, or training eligibility.

## Suggested human review order

1. Resolve the **14 explicit caption/TXT histogram conflicts** against the original source evidence and image; preserve uncertainty if the evidence does not decide the case.
2. Review the **12 tooth-count cases** and `00162` for completeness/unsupported text. Do not infer grades from absent teeth or missing caption fields.
3. Ask the qualified reviewer/supervisor to decide whether `01100` and `01101` meet any approved incomplete-caption rule. The rule remains inactive until approved.
4. Handle the four group companions and NP015 `00591` with group/identity review. A clean caption/TXT comparison cannot clear a protected content group or establish participant independence.

Use the existing searchable `index.html` and decision CSV in the ignored Training-52 folder; do not make a second copy of its images or edit the original annotations. Record reviewer, qualification, date, evidence and decision in a new reviewed version. Until then, keep every row pending and held.

## Focused comparison — Training/00025

On 2026-10-17, the original RGB image, its three `Train_captions.csv` rows and `Labels/00025.txt` were opened read-only. The RGB source is 7286×4863. A temporary box overlay was created under `/tmp` for visual alignment only; the source image and TXT were not edited.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1, 2 and 3 (same counts) | 0 / 1 / 3 / 1 / 7 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 1 / 1 / 2 / 1 / 7 | 4 |

There are 12 captioned teeth and 12 TXT tooth boxes. Both sources support image-level maximum **4**, but the tooth-grade histogram differs by one count: captions have one more MGI 2, while TXT has one MGI 0. The single TXT MGI-0 box overlays a lower anterior tooth region; because TXT has no FDI tooth ID, it cannot be safely matched to one of the captioned lower teeth by box order. The three caption variants also repeat a malformed MGI-3 position phrase: the count says one tooth but only position `23` is explicit after a blank position. No new grade or positional correction is proposed.

The boxes generally lie over anterior tooth/gingival-margin areas; this visual check does not certify box clinical correctness or FDI identity. The photo's lighting/reflection and the subtle appearance required to distinguish MGI 0 from MGI 2 are not enough for a clinical adjudication here. Keep `00025` **pending and held** despite matching image-level maximum. Current source hashes: image `85afd4bf1e194045080eff9e65e4772cbf864b162516186e44fe89a68f70d582`; TXT `5f356ef9f8051c16126151d4a7805a05bce0a052436b7c835bfc6bb363f833e5`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00052

On 2026-10-17, only the original `Training/Images/00052.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00052.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00052-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Three captions (declared counts) | 1 / 1 / 1 / 7 / 2 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 1 / 1 / 1 / 8 / 1 | 4 |

Both sources contain 12 tooth-level entries and agree on the highest grade, MGI 4. Their grade histograms conflict: the TXT has one extra MGI 3 box and one fewer MGI 4 box than the captions. The same upper-jaw MGI-3 position text appears in all three caption variants as `13, 12, , 23`; the explicit IDs number three, and the empty position slot remains a formatting/position ambiguity. Captions state two lower MGI-4 teeth (`42, 41`), while TXT contains one class-6/MGI-4 box. The overlay places tooth boxes over anterior tooth/gingival-margin regions, but TXT has no FDI IDs, so the single MGI-4 box cannot be assigned to either captioned tooth.

This is a confirmed annotation-evidence discrepancy, not evidence of which source is clinically correct. No replacement grade is proposed. Keep `00052` **pending and held** for qualified annotation/dental review. Current image and TXT hashes match the existing 172-image review CSV; the shared captions CSV hash also matches the previously recorded source hash. Hashes: image `84e848648f93344b86edc4289b1fa4a02d01b42f9cb3e1586a888cfe451ae7f0`; TXT `0a5ca03347f9da5601c1f716ecd64c8e1639a6e1edb48081633ef4b17453a8b6`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00097

On 2026-10-17, only the original `Training/Images/00097.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00097.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00097-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (all agree) | 0 / 1 / 6 / 5 / 0 | 3 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 2 / 5 / 5 / 0 / 0 | 2 |

All three captions provide the same 12 FDI-position/grade assignments. TXT also has 12 tooth boxes, but its grade histogram differs substantially: it has two MGI-0 boxes, five MGI-1 boxes, five MGI-2 boxes, and no MGI-3 boxes; captions report five MGI-3 teeth and no MGI-0 teeth. Therefore even the maximum grade differs (caption maximum 3; mapped TXT maximum 2). The overlay shows boxes over the upper/lower anterior tooth regions, but the TXT format has no FDI IDs; box order cannot establish which captioned tooth each class represents.

This is a strong technical annotation conflict; visual appearance alone does not establish which grade source is clinically correct. No grade is suggested or changed. Keep `00097` **pending and held** for qualified annotation/dental review. Current image/TXT hashes match the existing 172-image review CSV; the captions CSV hash matches the previously recorded source. Hashes: image `4af037e1baefa5945be684d58074c037983c7c619983d0c50343e9d794b8df73`; TXT `49fda16b65270cc85e863910dba996aef21e64d3aed285fd64cb7c964eb9cdd7`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00122

On 2026-10-17, only the original `Training/Images/00122.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00122.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00122-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same grade counts) | 0 / 1 / 0 / 1 / 10 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 0 / 2 / 10 | 4 |

Both sides describe 12 tooth records and agree on the maximum MGI 4. The histogram differs: captions include one MGI 1 and one MGI 3, while TXT has two MGI 3 and no MGI 1. The overlay shows the twelve tooth boxes arranged over the upper/lower anterior tooth regions, but TXT has no FDI IDs, so it cannot establish which individual tooth's class differs. The three captions preserve the same position/grade pattern; Caption 3 has awkward generated wording but the listed positions remain readable.

This is a technical annotation discrepancy, not evidence that either source is clinically correct. No grade is proposed or changed. Keep `00122` **pending and held** for qualified review. Current image/TXT hashes match the existing 172-image review CSV; the shared captions CSV hash matches the previously recorded source. Hashes: image `6b798548b9509a3dd5ba367a41292c1dafdb4041cc63f65852b7e44bea2d4ce7`; TXT `6cc27f53beb85c6f5bb00146ce638121ee818fdd233b7faf50d5c08741defc83`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00224

On 2026-10-17, only the original `Training/Images/00224.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00224.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00224-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same assignments) | 0 / 2 / 8 / 2 / 0 | 3 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 3 / 7 / 2 / 0 | 3 |

Both sources describe 12 tooth records and agree on the maximum grade, MGI 3. The histograms differ by one count between MGI 1 and MGI 2: TXT has one more MGI 1 box and one fewer MGI 2 box. The boxes appear over anterior tooth/gingival-margin regions in both jaws; the TXT has no FDI IDs, so the differing grade cannot be assigned to a named tooth from row order. The caption variants agree on their listed positions and grades.

This is an unresolved annotation-evidence discrepancy, not a clinical correction. Keep `00224` **pending and held**; no new grade is suggested. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `1607b0589de28ee1e8a440bd4cc4a587a5320e6ea98b19fbad84f9587540331e`; TXT `3b067eab84b24632ad4474c4e799a11e87bf122c09b00cc48b8424a0d9a01533`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00277

On 2026-10-17, only the original `Training/Images/00277.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00277.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00277-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same grade counts) | 0 / 0 / 0 / 3 / 9 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 0 / 2 / 10 | 4 |

Both sources describe 12 teeth and agree on maximum MGI 4. They differ by one count between MGI 3 and MGI 4. The overlay shows boxes on anterior tooth/gingival-margin areas in both jaws; it cannot map a box to a specific FDI position because TXT contains no tooth IDs. Captions agree with each other; their upper MGI-4 position list contains an empty comma slot, although the six explicit IDs match the declared count of six.

Keep `00277` **pending and held** for qualified review; the evidence does not identify which grade assignment is correct. No new label is suggested. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `b1f224af2710552fa6975c65e0f046ad80de88e45d0cd47a9efb5c8dbd1f9c77`; TXT `feb4e11357ca512c6effd078e2d76a3f5c2a15077072920ce4f4437631c24770`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00289

On 2026-10-17, only the original `Training/Images/00289.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00289.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00289-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same grade counts) | 0 / 0 / 0 / 6 / 6 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 0 / 5 / 7 | 4 |

Both sources describe 12 teeth and agree on maximum MGI 4. One count differs between MGI 3 and MGI 4. The overlay shows the boxes over anterior tooth/gingival-margin regions; TXT has no FDI IDs, so the differing box cannot be tied to an individual caption position. Captions agree with each other; one upper MGI-3 position list contains an empty comma slot but has three explicit IDs for its declared count of three.

Keep `00289` **pending and held** pending qualified annotation review. This histogram difference does not establish a clinical mislabel or which source is correct. No replacement grade is suggested. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `b694332ec3af8e47ee456bde58789e808992b8016fc80d11bf0ab0daf8c0aab6`; TXT `98ed155b0b15ba10f980486ada88c916f2297987a578675afb5ca146c8fa69ff`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00298

On 2026-10-17, only the original `Training/Images/00298.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00298.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00298-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same grade counts) | 0 / 0 / 0 / 5 / 7 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 0 / 6 / 6 | 4 |

Both sources describe 12 teeth and agree on maximum MGI 4. Their counts differ by one between MGI 3 and MGI 4. The overlay shows boxes over anterior tooth/gingival-margin regions in both jaws; no FDI IDs are present in TXT to tie the differing class to a named position. The captions agree with one another.

Keep `00298` **pending and held** for qualified review. This is a technical histogram mismatch, not a clinical relabel. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `2547b89de75b2ec8dac01bf44b136690da6b9b3fd408cad4b68d189891e2ca86`; TXT `b5b026239589f41db9bc1a1d6b251673cef4d613960ea073af5bf58391fe66c2`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00358

On 2026-10-17, only the original `Training/Images/00358.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00358.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00358-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same assignments) | 0 / 0 / 0 / 6 / 6 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 6 / 6 / 0 | 3 |

Each source contains 12 tooth records, but six lower-jaw entries differ: captions assign them MGI 4, whereas the six lower-jaw TXT boxes are class 4, which maps to MGI 2. The other six upper boxes are TXT class 5 (MGI 3), matching the captioned upper MGI-3 group. The overlay confirms which boxes are in the lower jaw, but TXT has no tooth IDs; this supports a jaw-level localization only, not individual FDI correspondence. The image-level maximum therefore differs: captions 4, TXT 3.

This is a substantial technical annotation conflict. The visual overlay cannot adjudicate a clinical grade or show whether caption or TXT is correct. Keep `00358` **pending and held**; no grade is proposed or changed. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `fa6338f69f33f8a57fd7935bcb8bc26646abc766548ae69f34875da5ba47c9b9`; TXT `fbe0273d86a6487bcdb34c40a4ab3c7ee1b80353bf460d3a70a3568c185efa6b`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00469

On 2026-10-17, only the original `Training/Images/00469.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00469.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00469-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same assignments) | 0 / 0 / 4 / 4 / 4 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 0 / 6 / 6 | 4 |

Both sources describe 12 teeth and agree on maximum MGI 4, but the distributions differ across multiple grades: captions include four MGI-2, four MGI-3 and four MGI-4 teeth; TXT contains six MGI-3 and six MGI-4 boxes, with no MGI-2 boxes. The overlay shows boxes spanning both jaws, but TXT lacks FDI IDs and cannot map its grades to the captioned positions. The captions agree with each other.

This is a substantial unresolved annotation-evidence conflict, not a basis for clinical relabeling. Keep `00469` **pending and held**. No replacement grade is proposed. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `df41b1be2acdd70bb7fa53ed5e3a9bb52432175edda06c888a564180ae959e8f`; TXT `de4559d3a322098e1ae18b1f0b1e22836fbf6ed7bf660c39142909667d258500`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00575

On 2026-10-17, only the original `Training/Images/00575.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00575.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00575-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same assignments) | 0 / 0 / 0 / 9 / 3 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 0 / 8 / 4 | 4 |

Both sources describe 12 teeth and agree on maximum MGI 4. One count differs between MGI 3 and MGI 4. The overlay shows boxes over anterior tooth/gingival-margin regions across both jaws; TXT has no FDI IDs, so the differing box cannot be tied to one named tooth. The three caption variants agree on the grade assignments.

Keep `00575` **pending and held** until qualified review. This is a technical histogram mismatch, not a clinical relabel. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `064bce8d7a100255fc01058d08c832b19dcceb7900f71858dbf52ad83eecd2e6`; TXT `efd10c102eb125ef4ff7174ebb7b3471a81fa1caed72833026ee6025223b5143`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00576

On 2026-10-17, only the original `Training/Images/00576.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00576.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00576-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same assignments) | 0 / 0 / 0 / 9 / 3 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 0 / 10 / 2 | 4 |

Both sources describe 12 teeth and agree on maximum MGI 4. They differ by one count between MGI 3 and MGI 4. The boxes cover upper and lower anterior tooth/gingival-margin regions, but TXT has no FDI IDs to identify which tooth's grade differs. All three captions agree with each other.

Keep `00576` **pending and held** for qualified review. This discrepancy does not show which source is clinically correct; no new grade is proposed. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `c77d99fd74114a9ec615862e6f010035d5a1f764814f59c109726b8e2dfaeac9`; TXT `4e652d75bf0cead64838a694ca8a5408daa9fd948213cc50f6056635827f743b`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00649

On 2026-10-17, only the original `Training/Images/00649.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00649.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00649-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same assignments) | 0 / 0 / 1 / 8 / 3 | 4 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 0 / 2 / 7 / 3 | 4 |

Both sources describe 12 teeth and agree on maximum MGI 4. One count differs between MGI 2 and MGI 3. The overlay shows boxes distributed across the upper and lower anterior regions; TXT has no FDI IDs, so a specific tooth cannot be matched to the differing class from box order. Captions agree with each other.

Keep `00649` **pending and held** for qualified review. This count shift is not a clinical correction. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `cb67b5d63f624cb9a1249c883eef3a27d2436f561ceeb60885995ba5700e30fb`; TXT `adf9aa207e72384ded0431e0b9bade3eaf1d25211e98f1609e51f3f54f3d50c6`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused comparison — Training/00709

On 2026-10-17, only the original `Training/Images/00709.jpg`, its three rows in `Train_captions.csv`, and `Training/Labels/00709.txt` were inspected. The RGB source is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00709-TXT-overlay.png`; it did not alter the source.

| Evidence | MGI 0 / 1 / 2 / 3 / 4 counts | Highest grade |
|---|---|---:|
| Captions 1–3 (same assignments) | 0 / 0 / 12 / 0 / 0 | 2 |
| TXT after audited class mapping (classes 2–6 → MGI 0–4) | 0 / 9 / 3 / 0 / 0 | 2 |

Both sources describe 12 teeth and agree on maximum MGI 2, but most tooth-grade counts differ: captions assign all 12 as MGI 2, while TXT assigns nine boxes to MGI 1 and three to MGI 2. The overlay shows these boxes distributed over the upper/lower anterior tooth regions. TXT has no FDI IDs, so the nine specific teeth cannot be matched to caption positions using row order. All caption variants agree with one another.

This is a substantial technical grade-distribution conflict, especially relevant to the scarce MGI 1/2 boundary. It does not establish which source is clinically correct. Keep `00709` **pending and held**; no label is proposed or changed. Current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `c7a39e417089a19e3a06845674b684964c9d3fa8185962acc1dc5a766c9d16d9`; TXT `139ff34c62f1483e338f2579fbdc55c4349f54ff583d8a8a03c2ca5c7ab14c09`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Aggregate result for the 14 explicit histogram conflicts

| Training ID | Caption max | TXT max | Maxima |
|---|---:|---:|---|
| 00025 | 4 | 4 | match |
| 00052 | 4 | 4 | match |
| 00097 | 3 | 2 | differ |
| 00122 | 4 | 4 | match |
| 00224 | 3 | 3 | match |
| 00277 | 4 | 4 | match |
| 00289 | 4 | 4 | match |
| 00298 | 4 | 4 | match |
| 00358 | 4 | 3 | differ |
| 00469 | 4 | 4 | match |
| 00575 | 4 | 4 | match |
| 00576 | 4 | 4 | match |
| 00649 | 4 | 4 | match |
| 00709 | 2 | 2 | match |

All 14 caption variants agree internally on their recorded grade counts; each case has 12 captioned teeth and 12 TXT tooth boxes, and each image/TXT hash matches the existing review cache. **Two of 14 image-level maxima differ** (`00097`, `00358`); the other 12 maximum matches do not clear their grade-histogram conflicts. All 14 remain pending/held for qualified review. The comparison established technical consistency facts only, not clinical grade truth.

## Focused count review — Training/00060

On 2026-10-17, only the original `Training/Images/00060.jpg`, its three `Train_captions.csv` rows, and `Training/Labels/00060.txt` were inspected. The RGB image is 7286×4863. A temporary TXT-box overlay was written to `/tmp/RP-J26-Training-00060-TXT-overlay.png`; the source was not changed.

| Evidence | Tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 | 5 / 3 / 4 / 0 / 0 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 5 / 4 / 4 / 0 / 0 |

The three caption variants agree with one another. TXT has one more tooth box than the 12 captioned positions and one extra MGI-1 count; MGI-0 and MGI-2 counts match. The overlay confirms boxes on both jaws, but there are no TXT FDI tooth IDs to safely identify the extra record. This is a structural annotation discrepancy, not a grade correction. Keep `00060` **pending and held**. The current image/TXT hashes match the existing 172-image review CSV; captions CSV hash matches the recorded source. Hashes: image `01699ef110c4ae93e11292889366581c7183c8b364562b74b579bbe2c22a19b7`; TXT `7a16101214d802f98753b49ecb871e125a917149e0f58c07dfad49ad86207c6d`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00085

On 2026-10-17, only the original `Training/Images/00085.jpg`, its three caption rows, and `Training/Labels/00085.txt` were inspected. The RGB image is 7286×4863. A temporary TXT-box overlay was saved to `/tmp/RP-J26-Training-00085-TXT-overlay.png`; no source file changed.

| Evidence | Tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 | 2 / 8 / 2 / 0 / 0 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 2 / 9 / 2 / 0 / 0 |

Captions agree internally. TXT contains one more tooth box, reflected by one extra MGI-1 box; MGI-0 and MGI-2 counts match. The overlay shows boxes across both jaws, but TXT has no FDI identities to locate the additional box precisely. Keep `00085` **pending and held** for annotation review; this structural count discrepancy does not establish a clinical mislabel. Image/TXT hashes match the existing 172-image review CSV; the captions CSV hash matches the saved source. Hashes: image `b26647766741b0a92c9a1b86a8e9ebe0483a9074339f5bcc65f7622c8bfd6b13`; TXT `fa15d8cf3d756f1323e7f72f93927046ded6b9a95f34995a0af545747acffb7f`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00484

On 2026-10-17, only the original `Training/Images/00484.jpg`, its three caption rows, and `Training/Labels/00484.txt` were inspected. The RGB file is 7286×4863. A temporary TXT-box overlay was saved to `/tmp/RP-J26-Training-00484-TXT-overlay.png`; it did not change the source.

| Evidence | Tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 | 0 / 0 / 0 / 1 / 11 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 0 / 0 / 0 / 2 / 11 |

The captions agree internally. TXT contains one extra tooth box and one extra MGI-3 count; MGI-4 count remains 11. No FDI IDs are available in TXT to identify the extra box. A separate visual anomaly is visible in the source: hard horizontal and right-edge seams/patch boundaries. Their cause is unknown; this is a source-quality review flag, not proof of manipulation or a clinical issue. Keep `00484` **pending and held** for both annotation-count and image-integrity review. The image/TXT hashes match the cached 172-image review CSV; caption hash matches the saved source. Hashes: image `2e227fc3e4e8a8e02b6adac81d0310b7b34373575061c06bbbbe34f5e5991314`; TXT `188a5227198ca2bd652c6322a29c8f0f24c61851dc5a5740d4aaec5237a1ce0e`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Limits and verification

The TXT class histogram is evidence for annotation consistency only; it does not give reliable tooth-position identity and is not a model input. This cached-only comparison cannot decide whether a visually subtle MGI grade is clinically correct. The existing package still records **52 pending, zero newly approved, zero newly training-eligible**. The 129 held Validation cases remain in Validation; no Test payload or label was inspected.

No source image, CSV/TXT, label, split, hold, approval flag, model, or checkpoint changed. No model was trained; no Test or held Validation payload was accessed; no installation, upload, commit, or push occurred. No test suite was run because this was a read-only reconciliation of previously verified cached evidence.

Viva: **If 47/49 caption maxima match the TXT maximum, why are the records still held?** Because maximum agreement does not resolve full-histogram conflicts, missing/unsupported caption evidence, tooth-count issues, protected duplicate groups, or clinical label approval.

## Focused count review — Training/00557

On 2026-10-17, only the original `Training/Images/00557.jpg`, its three caption rows, and `Training/Labels/00557.txt` were inspected. The RGB image is 7286×4863. A temporary TXT-box overlay was saved to `/tmp/RP-J26-Training-00557-TXT-overlay.png`; no source file changed.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 0 / 10 / 2 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 11 | 0 / 0 / 0 / 9 / 2 |

All three captions agree on six upper and six lower positions, with maximum MGI 4. TXT contains 11 tooth boxes plus the two jaw ROI boxes; its mapped histogram has one fewer MGI-3 box. The overlay visually shows six upper boxes and five lower boxes. This supports a box-count coverage discrepancy but does not identify the missing FDI position or establish a clinical grade error. The TXT records no FDI IDs, so box order cannot resolve the correspondence. Keep `00557` **pending and held**. Current image/TXT SHA-256 values match the cached review record; the caption CSV hash matches the saved source. Hashes: image `f8bec32b98cc63e96ac8e96d22541bb1f50f42da3d5a550768de6f309040fe63`; TXT `c8d60a7135a4647076c1acc23ade7b5105a93917f140338ca40ca8bfe8c9833e`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00568

On 2026-10-17, only the Training alias `Training/Images/00568.jpg`, its three Training caption rows, and `Training/Labels/00568.txt` were inspected. The RGB image is 7286×4863. Its current SHA-256 matches the prior verified split-manifest hash. A temporary TXT-box overlay was saved to `/tmp/RP-J26-Training-00568-TXT-overlay.png`. The cached content-group record marks this as protected cross-split content; no Test image or label was opened or compared.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 2 / 6 / 4 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 0 / 0 / 2 / 6 / 5 |

The three captions agree on the 12 stated positions and maximum MGI 4. TXT has 13 tooth boxes plus two jaw ROI boxes; the MGI-4 count is one higher than the captions. The overlay is a spatial view of raw TXT boxes only. Since TXT has no FDI tooth IDs, it cannot establish which tooth box is additional or which source is correct. Keep `00568` **pending and held**, including its existing protected content-group hold. Image SHA-256 is `802a3ec9fb32c98915a5ebe2af29d854e8202ee1a3a1f1bdc508f7d138740b8e`; TXT SHA-256 is `0dea77f683fd04a81f6b266f654e1f69cb9bb3a02cfdc53c7dd8afae578f5481`; caption CSV SHA-256 is `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00602

On 2026-10-17, only the original `Training/Images/00602.jpg`, its three caption rows, and `Training/Labels/00602.txt` were inspected. The RGB image is 7286×4863 and its SHA-256 matches the prior verified split manifest. A temporary TXT overlay was saved to `/tmp/RP-J26-Training-00602-TXT-overlay.png`.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 0 / 6 / 6 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 0 / 0 / 0 / 7 / 6 |

The captions agree internally and state a maximum MGI 4. TXT has 13 tooth boxes plus two jaw ROI boxes, with one additional MGI-3 box relative to the caption histogram. The overlay shows six upper and seven lower boxes. This is a structural count discrepancy; without tooth IDs in TXT, it cannot establish the exact unmatched tooth or a clinical label error. Keep `00602` **pending and held**. Image SHA-256: `23b93cfad23ee3aa125fca2b03c80025dfc91a5417deb6d45529b36629004305`; TXT SHA-256: `00333b6d4faa124942f29e93513165c7d1957165bbf22f0db72218773a56d7bf`; captions CSV SHA-256: `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00657

On 2026-10-17, only the original `Training/Images/00657.jpg`, its three caption rows, and `Training/Labels/00657.txt` were inspected. The 7286×4863 image SHA-256 matches the prior verified split manifest. A temporary TXT overlay was saved to `/tmp/RP-J26-Training-00657-TXT-overlay.png`.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 1 / 7 / 4 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 0 / 0 / 1 / 8 / 4 |

The three captions agree internally and state maximum MGI 4. TXT has 13 tooth boxes plus two jaw ROI boxes, with one extra MGI-3 box relative to the caption histogram. Coordinates parsed as valid and the overlay shows box coverage; it cannot assign an FDI identity because TXT has no tooth IDs. Keep `00657` **pending and held**; this is not a supported clinical relabel. Image SHA-256: `320933a8f7dbcddf278e5ac04039d873eb535738b2b4466177b680c50092069f`; TXT SHA-256: `5220644e3e9106747a2c1af3bf3ca84efd33550c5b227237c38026a9550ced26`; captions CSV SHA-256: `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00667

On 2026-10-17, only the original `Training/Images/00667.jpg`, its three caption rows, and `Training/Labels/00667.txt` were inspected. The 7286×4863 image SHA-256 matches the prior verified split manifest. A temporary TXT overlay was saved to `/tmp/RP-J26-Training-00667-TXT-overlay.png`.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 2 / 10 / 0 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 0 / 0 / 2 / 11 / 0 |

All three captions agree on the stated sites and maximum MGI 3. TXT has 13 tooth boxes plus the two jaw ROI boxes, one more MGI-3 box than the captions. Coordinates parsed as valid; the overlay shows the extra box coverage in the lower region, but TXT has no FDI IDs and cannot identify a specific tooth. Keep `00667` **pending and held**; no clinical grade change is supported. Image SHA-256: `968e4ea95a5b1162b0a8042aabe74c805871f29b12d4565c8676284761bfe623`; TXT SHA-256: `07cb8f70e29498e6d7ff6f878d6cdb024a07700e9030b0750cf6d32cbb135019`; captions CSV SHA-256: `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00673

On 2026-10-17, only the original `Training/Images/00673.jpg`, its three caption rows, and `Training/Labels/00673.txt` were inspected. The 7286×4863 image SHA-256 matches the prior verified split manifest. A temporary TXT overlay was saved to `/tmp/RP-J26-Training-00673-TXT-overlay.png`.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 7 / 2 / 3 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 11 | 0 / 0 / 6 / 2 / 3 |

The captions agree internally and state maximum MGI 4. TXT has 11 tooth boxes plus two jaw ROI boxes, one fewer MGI-2 box than the caption histogram. Coordinates parsed as valid and the overlay shows the boxes over the visible jaws; the missing correspondence cannot be assigned to a particular tooth because TXT has no FDI IDs. Keep `00673` **pending and held**; no clinical grade correction is supported. Image SHA-256: `992726d3617d921bc131fce478cd1358f009effd400102630674b7e841413417`; TXT SHA-256: `20125cc1e313d074e96dacbc8f1425fb705cea1ce8d47467d0684c40523fd9c4`; captions CSV SHA-256: `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00676

On 2026-10-17, only the original `Training/Images/00676.jpg`, its three caption rows, and `Training/Labels/00676.txt` were inspected. The 7286×4863 image SHA-256 matches the prior verified split manifest. A temporary TXT overlay was saved to `/tmp/RP-J26-Training-00676-TXT-overlay.png`.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 0 / 8 / 4 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 11 | 0 / 0 / 0 / 7 / 4 |

All three captions agree and state maximum MGI 4. TXT has 11 tooth boxes plus two jaw ROI boxes, one fewer MGI-3 box than the caption histogram. The boxes parse within normalized bounds and the overlay confirms visual placement only; no FDI identity is encoded. Keep `00676` **pending and held** for annotation review. Image SHA-256: `01e379bdeb0b6cb9b1ffc6abf157ab9586c5c7b3ea0aa350e5fa78d096fbfe09`; TXT SHA-256: `558a024fc9c399f06a9f9343de296d611b71db4c3ef4dd5635b55bc26193a4f2`; captions CSV SHA-256: `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused count review — Training/00702

On 2026-10-17, only the original `Training/Images/00702.jpg`, its three caption rows, and `Training/Labels/00702.txt` were inspected. The 7286×4863 image SHA-256 matches the prior verified split manifest. A temporary TXT overlay was saved to `/tmp/RP-J26-Training-00702-TXT-overlay.png`.

| Evidence | Stated/boxed tooth count | MGI 0 / 1 / 2 / 3 / 4 counts |
|---|---:|---|
| Captions 1–3 | 12 stated positions | 0 / 0 / 8 / 4 / 0 |
| Mapped TXT boxes (class 2–6 → MGI 0–4) | 13 | 0 / 0 / 8 / 5 / 0 |

The captions agree internally and state maximum MGI 3. TXT has 13 tooth boxes plus the two jaw ROI boxes, one additional MGI-3 box relative to the caption histogram. Coordinates parsed as valid and the overlay shows raw box placement only; TXT contains no FDI IDs to identify the extra record. Keep `00702` **pending and held**; no clinical label correction is supported. Image SHA-256: `7a09aa65918597503b12f3ef6df7711b38d8cf439f4fc1b53604f03e6a19b7e3`; TXT SHA-256: `967a53779a92fcb880a281a2369659be20c25f51ea49f1f702167331baf74bf1`; captions CSV SHA-256: `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused unsupported-caption review — Training/00162

On 2026-10-17, only `Training/Images/00162.jpg`, its three caption rows, and `Training/Labels/00162.txt` were inspected. The 7286×4863 image SHA-256 matches the prior verified split manifest. A temporary TXT overlay was saved to `/tmp/RP-J26-Training-00162-TXT-overlay.png`.

All three caption variants list the same 12 positions at MGI 3, but also contain repeated counts for non-inflamed and MGI 1, 2, and 4 with blank/no tooth positions. The cached parser therefore reports no supported candidate maximum and flags both a declared-tooth-count mismatch and unsupported grade clauses. TXT has 12 tooth boxes, all mapped to MGI 3, plus two jaw ROI boxes; its coordinates are valid. This does not resolve whether the unsupported MGI-4 statement is true. Treat the image-level label as **unresolved**, not as MGI 3 or MGI 0; keep `00162` pending/held for qualified caption/annotation review. Hashes: image `3bbf190d3d5e78eed803124c374c2829a83b56c0f29f6c75ad8606d6e652be85`; TXT `e5eb76936d38f231cdaaf245ddf7b452663931c512a6cc1a0282548351fdb7ae`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused annotation/group review — Training/00271

On 2026-10-17, only `Training/Images/00271.jpg`, its Training captions, and `Training/Labels/00271.txt` were inspected. The 7286×4863 image SHA-256 matches the prior verified split manifest. The temporary TXT overlay is `/tmp/RP-J26-Training-00271-TXT-overlay.png`. Captions 1–3 agree on 12 stated teeth; caption and TXT MGI0–4 histograms both equal `2/1/3/4/2`, and TXT has 12 tooth boxes plus two jaw ROI boxes with valid coordinates. This confirms within-record count/histogram consistency only, not clinical correctness or tooth-by-tooth identity. Cached grouping marks this Training alias in a protected group spanning Test; no Test counterpart was opened or compared. Keep `00271` **pending and held** for group/label approval. Image SHA-256 `8768bf6823d8d95f1682483619100e33fe4adedac5e007ff78eaeeaf68a4a7f1`; TXT `4ae8238eb3b0d6fb51fbd027d1815283cd91bf752387eebacb9e5427d1d59405`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused annotation/group review — Training/00272

On 2026-10-17, only `Training/Images/00272.jpg`, its Training captions, and `Training/Labels/00272.txt` were inspected. The image is 7286×4863 and its SHA-256 matches the verified split manifest. Temporary overlay: `/tmp/RP-J26-Training-00272-TXT-overlay.png`. The three captions agree on 12 teeth; caption and TXT MGI0–4 histograms both equal `0/2/2/5/3`; TXT has 12 tooth boxes plus two jaw ROI boxes, with valid normalized coordinates. This is internal count/histogram consistency only and does not establish clinical grade correctness. The cached content group spans Test and Training; only this Training alias was read, and no Test counterpart or label was accessed. Keep `00272` **pending and held** for protected-group and label approval. Image SHA `540ec56a8764671eb8d22382837de0fc3a7939fadc6558246d583877320efbf4`; TXT SHA `6eebc87489e5cca81dd2f25561ae08eaf9893848c54dfcd75a1188782cb64ad9`; captions CSV SHA `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused annotation/group review — Training/00273

On 2026-10-17, only `Training/Images/00273.jpg`, its Training captions, and `Training/Labels/00273.txt` were inspected. The 7286×4863 image SHA-256 matches the verified split manifest. Temporary overlay: `/tmp/RP-J26-Training-00273-TXT-overlay.png`. All three captions agree on 12 stated teeth and maximum MGI 4; caption/TXT MGI0–4 histograms both equal `0/1/3/4/4`, and TXT has 12 tooth boxes plus two ROI boxes with valid coordinates. This supports within-record annotation consistency only, not clinical correctness. Cached grouping marks a cross-split protected Test group. Only the Training alias was read; no Test payload or label was opened. Keep `00273` **pending and held** for group and qualified-label approval. Image SHA `9025d3a5154c8b117bfc47819967c5287abf2d3219e822cc2e38bc2865c9cf4f`; TXT SHA `7ad4f0cc5ca040d5640591ca445d4aed3d5d33820479f68214cbd3842311130d`; captions CSV SHA `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused annotation/group review — Training/00275

On 2026-10-17, only `Training/Images/00275.jpg`, its Training captions, and `Training/Labels/00275.txt` were inspected. The 7286×4863 image SHA-256 matches the verified split manifest. Temporary overlay: `/tmp/RP-J26-Training-00275-TXT-overlay.png`. The three captions agree on 12 stated teeth and maximum MGI 3; caption/TXT MGI0–4 histograms both equal `3/2/4/3/0`. TXT has 12 tooth boxes plus two ROI boxes, with valid coordinates. This indicates within-record count/histogram agreement, not clinical grade correctness. Its cached group spans Test and Training; no Test image or label was opened. Keep `00275` **pending and held** under the protected group policy. Image SHA `dedbc86f0bf87905773562b1d3bb1e18669b1c301558aa144b0035e6a02c5554`; TXT SHA `81fb8ba6206ba5be05dc47d90401abf0966b4397b8b6a3bbf07229f69530723b`; captions CSV SHA `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.

## Focused annotation/group review — Training/00562

On 2026-10-17, only `Training/Images/00562.jpg`, its Training captions, and `Training/Labels/00562.txt` were inspected. The 7286×4863 image SHA-256 matches the verified split manifest. Temporary overlay: `/tmp/RP-J26-Training-00562-TXT-overlay.png`. All three captions agree on 12 stated teeth and maximum MGI 4; caption/TXT histograms both equal `0/0/2/4/6`, with 12 tooth boxes plus two ROI boxes and valid normalized coordinates. This is structural consistency only, not clinical validation. The cached content grouping marks it as a two-image Training group; the group identity/split policy remains pending. Keep `00562` **pending and held**. Image SHA `813cb74381ef451a1a1fec64f06198bc41075b1e95d5553b285b066ddc6b2890`; TXT `6fe5d5dd2f9d82b471ee75e9ab6844d7529c4ac7607b128aac379ec2fbd11fb9`; captions CSV `6f073e3a939e77fa076e3a8d233d45d783beeb86e5760158d13dd0852ec42f63`.
