# Vision label adjudication options — approval required

Date: 2026-10-13. Audit only; no final mapping, relabelling, resplitting or training approved here.

## What the sources support

The supplied signed Component 2 proposal, page 17, explicitly defines the target as the highest visible MGI grade in each photograph, with grades 0–4, using reliable caption-derived labels. Page 18 requires annotation-mapping verification, and page 22 requires preserving published splits when clean. This is the project authority.

The [original dataset paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11462013/) provides per-tooth scores and three captions per image; it does not establish the project's maximum-grade image classifier. Its Table 2 associates annotation code 2 with MGI 0; normal teeth in a photo therefore do not establish an image-level maximum of 0. The paper claims one different individual per image, but that claim is distinct from verification using local participant IDs. Its code-description prose disagrees with Table 2, so mapping review remains necessary. The [Mendeley version 1 record](https://data.mendeley.com/datasets/3253gj88rr/1) identifies the captioning dataset and its licence.

No missing caption may be treated as normal. A normal tooth alongside any positive grade does not make the entire image's maximum grade 0. Annotation class IDs, caption-variant IDs and participant IDs must not be conflated.

## Proposed options, none applied

| Option | Required evidence / approval | Consequence |
|---|---|---|
| A. Keep the proposal's caption-derived maximum; adjudicate uncertain captions individually | Qualified owner/supervisor or dental reviewer inspects all variants, source image and annotation evidence; approve interpretation and retain provenance | Preserve all published memberships. Unresolved records remain needs_review; no automatic first-caption/majority/union rule |
| B. Use verified consensus tooth annotations to resolve individual caption disagreements | First verify numerical mapping, geometry and source provenance. Explicit owner approval required because captions are currently primary | Record old variants, annotation evidence and reviewer decision. Never overwrite originals or silently turn the diagnostic mapping hypothesis into labels |
| C. Address lack of image-level MGI 0 support as a feasibility/scope issue | Supervisor decision after audit/adjudication. May require a documented proposal amendment or separate approved normal-image source/protocol | Do not add normal teeth as whole-image zero examples, change maximum to minimum/mean, manufacture healthy images or promise five-class evaluation with unsupported classes |

Option A is closest to the existing proposal. It still requires review; the audit does not select an adjudication policy. If all reviewed image maxima remain positive, resolving caption text alone will not supply a grade-0 class.

## Approval and leakage safeguards

- Separate dataset-quality adjudication from model performance; never use final-test predictions to decide labels, thresholds, features or models.
- Dataset test images/metadata may be inspected only for the approved integrity/label audit. They remain outside all fitting and model selection. No NHANES participant payload is accessed.
- Local manifests preserve original split, source hash and image path; they are provisional audit inventories, not a frozen training target manifest.
- Confirm any exact/pixel/near-duplicate candidates and participant linkage before approving training. Hash/fingerprint similarity is not participant identification.
- A mapping decision, label repair, record exclusion, new grouped split or new dataset requires explicit approval and a new provenance record.
- After adjudication approval, freeze labels and a documented eligibility/split manifest. Training needs separate approval; training configurations are not proposed by this audit.

## Viva check

Question: If MGI 0 tooth annotations exist, why can image-level MGI 0 still be absent?

Answer: The target is the largest grade in the whole photo. A photo with a normal tooth and a grade-3 tooth has maximum 3. Maximum 0 requires every relevant reliably annotated tooth to be normal; it cannot be inferred from one normal tooth or a missing caption.
