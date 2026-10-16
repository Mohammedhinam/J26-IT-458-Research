# Held Vision review: local preparation and external-release blockers

16 October 2026 · branch `vinuthan`.

**Local tracking/batch planning is complete. External RGB/annotation packaging is paused before release, as requested. No files are approved for Gemini upload yet.** Originals, clinical labels, held status, split membership and training gates are unchanged.

## Exact local locations

Root:

```text
/Users/vinuthanvinuthan/Desktop/RP-J26-IT-458/data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/gemini_review_preparation_v1_20261016T164212810635Z/
```

- `master_tracking_181.LOCAL_ONLY.csv`: all181unique development IDs, original filenames/splits, proposed batch, provisional MGI evidence, conflicts, content group, source references and blank decision provenance. All statuses pending; approved grades blank; training eligibility/upload-ready false. **Do not upload this master:** it includes nine protected-content aliases for local tracking only.
- `local_plan.json`: full local scheduling and existing cached evidence. **Not an external bundle.** It includes local references/protected tracking records.
- `preparation_summary.json` and `verification.json`: exact counts, existing-input hashes and current checks.
- Each proposed batch folder contains `manifest.LOCAL_ONLY.json`, `PROPOSED_FILES_NOT_CREATED.txt`, and `PROPOSED_UPLOAD_REQUESTS.json`. These are planning files, not upload payloads. Manifests retain all three **parsed cached caption variants** and cached TXT corroboration. They are not substitutes for the original three caption strings or original TXT text.

No original RGB/JPEG, original caption text, original TXT, ZIP, transformed image or clinical prediction was copied/generated here. Existing original source image/TXT paths for172candidates exist, checked using filesystem metadata only;344path checks. No original image/header/pixels, source CSV/TXT or Test payload was opened for this preparation.

## Membership and batches

| Disposition | Training | Validation | Total |
|---|---:|---:|---:|
| Local master tracking | 52 | 129 | 181 |
| Proposed external-review candidates, still permission/privacy blocked | 43 | 129 | 172 |
| Protected Test-content aliases: local only | 9 | 0 | 9 |

Protected aliases are Training00271,00272,00273,00275,00566,00568,00570,00571,00572. They retain local tracking rows and no external batch assignment. This is required by the owner's **“Do not include protected Test data”** boundary; an original Training folder name does not make Test-overlapping content independent. No Test grade, image or annotation was accessed. Do not later add these aliases to an upload request to reach181.

| Folder under root | Planned images |
|---|---:|
| `Training/batch_01/` | 15 |
| `Training/batch_02/` | 14 |
| `Training/batch_03/` | 14 |
| `Validation/batch_01/` | 15 |
| `Validation/batch_02/` | 15 |
| `Validation/batch_03/` | 15 |
| `Validation/batch_04/` | 14 |
| `Validation/batch_05/` | 14 |
| `Validation/batch_06/` | 14 |
| `Validation/batch_07/` | 14 |
| `Validation/batch_08/` | 14 |
| `Validation/batch_09/` | 14 |
| **12 batches** | **172** |

Batching is deterministic by split/ID for review scheduling only, not a new experiment split or claim of participant independence. Existing content-group IDs/counts/split-presence and NP015 holds remain visible; batch boundaries do not split/redefine groups. Training and Validation never share a batch. AI review must not clear NP015, infer identity or guide model fitting based on Validation conclusions.

## Concerns to resolve before actual packaging

| Concern | Verified evidence / unknown | Required action |
|---|---|---|
| Licence | Original [Mendeley record](https://data.mendeley.com/datasets/3253gj88rr/1) explicitly lists CC BY4.0 and DOI10.17632/3253gj88rr.1 | Include Duy et al.(2024)/dataset attribution, DOI, [licence link](https://creativecommons.org/licenses/by/4.0/) and any derivative/transformation notice. Licence does not itself resolve every privacy/personality right |
| Research consent / external AI | Public release exists; specific consent/institutional permission for this Gemini account/workflow is not established here | Owner confirms applicable dataset/project/institutional restrictions and permitted external processing; do not fabricate institutional or clinical approval |
| Account processing | Owner confirmed Personal Gemini web/app; account settings and applicable data-use permission remain unverified. [Google's Privacy Hub](https://support.google.com/gemini/answer/13594961?hl=en) documents collection of uploaded files/photos, some human review, and account/settings-dependent use/retention | Use the Personal Gemini Apps notice/settings, not presumed Workspace/API protections. Disabling activity is not a guarantee of zero retention or human review |
| Image metadata | Prior project export evidence found EXIF/ICC/opaque metadata in other development originals. This held172cohort has not received a new header/privacy qualification | Do not copy originals wholesale to external files. First qualify a metadata-safe, full-resolution route; never expose opaque values in logs. No confirmed GPS coordinates in this held cohort are claimed |
| Colours and filenames | ICC affects display meaning. Old bounded-sRGB route failed; B1 arrays are not ordinary Gemini-upload images | Do not strip ICC blindly, re-encode JPEG lossily, resize or silently reuse old failed colour policy. A safe JPEG metadata-only path retaining a verified non-identifying colour interpretation would need qualification. Any PNG/name/pixel-conversion alternative requires an explicit preservation-policy decision |
| Protected content | Nine Training aliases overlap Test content | Remain local-only; external package maximum172under current boundary |
| Annotation authority | AI can compare evidence, not authenticate a qualified clinical reviewer | All responses remain AI-assisted/unverified; no new approved grades, eligibility, participant IDs or training permission |

Owner consent to the workflow does not create missing third-party consent or clinical expertise. If applicable restrictions cannot be established, retain local-only preparation and do not release a package. No external service has been contacted with project data.

## Exact future upload selection — not created or authorised yet

**Upload nothing from the current preparation directory.** It contains local paths, pending plans and no actual images. `PROPOSED_UPLOAD_REQUESTS.json` in each batch names the exact proposed source filenames and ID membership for each future request; protected aliases are excluded.

After the above decisions and a verified real export, the external batch should contain:

1. Only the individually allowlisted full-resolution, colour-preserved, metadata-safe images for its IDs, with original filenames if that can be qualified without modifying originals.
2. For each sub-request, one `request_01_evidence.txt` or `request_02_evidence.txt` containing **all three exact original caption strings** and the **complete original YOLO TXT text** for just those image IDs; include class mapping, provisional evidence/conflicts/group context and source/export hashes. Do not upload the whole Training/Validation CSV: it includes unrelated/protected-alias records.
3. Only the corresponding sanitised batch manifest, attribution and review prompt. Do not upload this local master or local manifests; external versions must omit local paths, protected IDs and opaque metadata.

The [Gemini Apps upload guide](https://support.google.com/gemini/answer/14903178?hl=en-GB) documents up to10supported files per prompt, subject to availability. Each10–15image review batch therefore has two proposed requests of at most9images plus1evidence file. Paste the review instructions/attribution in the prompt to stay within that limit; do not assume a ZIP will be interpreted as a gallery or a filename list proves an image was inspected. Preserve IDs and request numbers when merging returned text; never merge independent AI opinions into approved clinical truth.

Suggested AI instruction:

> Compare only the supplied IDs and files. Report annotation agreements, count/position contradictions, missing evidence and uncertainty, with exact source references. TXT classes0/1are jaw ROIs;2–6maptoMGI0–4. TXT has no explicit FDI IDs; never infer them from line order or x-position. Distinguish cached/source annotation maximum from clinically verified whole-image grade. Do not infer absent grades as0, clinical groundtruth, participant identity, approved labels or training eligibility. Return every supplied ID with status `AI_assisted_unverified` and retain `needs_review`; no automatic relabeling. Record files actually inspected and explicitly identify unavailable evidence.

## Actual verification and provenance

- **8generated tests passed,0failed/errors/skipped**: deterministic split-separated10–15batching, protected aliases excluded, original metadata unchanged, Test/duplicate/path/approval/caption-count failures rejected. [JUnit](vision_gemini_review_plan_tests_v1.xml).
- **59saved-artifact assertions passed,0finalfailures**:181CSVIDs,52/129split,172unique proposed batch IDs,nineprotectedlocal-only,all27CSVfields round-trip including missing/zero/booleans,threecachedvariants per case,correct request membership,<=10attachments,old input hashes unchanged,noRGB/ZIPpayload. First verifier comparison used Python`False` instead of CSV`false`; corrected only the verifier's boolean normalization, not data/statuses.
- Master CSV SHA256: `621dbf1b5191a3f1066be06344aacafdbcd0c168f0e45d37951f1ab8aa46115d`. Existing held evidence SHA256:`791da6a5fa667962207b01cb7463f643e6e35fcf409351eab2f6f23366d31eac`.
- Master authored/inspected with bundled Artifact Tool; CSV exported with literal cell values and independently reread. A readable preview projection was inspected. No live Excel behaviour/formulas claimed.
- Source dataset/original resolution/colours/filenames/splits, clinical labels/holds, original manifests/reviewers and dirty work preserved. No images packaged/uploaded, clinical labels promoted, model trained, dependency installed, commit or push.

## Next concrete owner input

The owner has identified Personal Gemini web/app. Confirm permitted third-party processing and informed acceptance of its applicable retention/human-review terms; the account answer alone is not upload permission. Acknowledge that nine protected aliases must remain local-only. Then separately authorise a narrowly scoped header/privacy and lossless colour-preservation qualification for the172candidate sources, preserving originals and requiring fresh hashes. **This is not permission to upload, train or activate a final manifest.** Actual external image packaging must wait for successful privacy/colour checks; no known failed guard may be bypassed.

Tamil:181records-க்கும் tracker உண்டு;172க்கு local batch plan மட்டும்.9Test-overlapimages வெளியே போகாது. Gemini doctor அல்ல; approvalfields இன்னும் blank. CSV/manifest உருவானது actual RGB package தயாரானது என்று அர்த்தமில்லை.

Viva: **Why exclude a Training filename from an external review batch?** Its content overlaps protectedTest; split isolation follows verified groups, not folder names alone.


## Three important blocks to understand

1. `Test in group_original_split_presence`: filename Training-ல் இருந்தாலும் content Test-உடன் overlap ஆனால் external batch-ல் போகாது. அதனால்9records local tracker-ல் மட்டும் உள்ளன.
2. `balanced_batches`: original split மாறாமல்172records-ஐ10–15case review folders-ஆக பிரிக்கிறது. இது புதிய training/validation split அல்ல.
3. `upload_ready=False` மற்றும் blank approved-grade fields: திட்டமும் evidence-மும் தயாராக இருப்பது clinical approval அல்லது actual package ready என்பதல்ல. எந்த source file-ஐயும் இந்த code copy/decode செய்யாது.
