# B1 generated-only exporter / verifier / authorization integration v1

2026-10-15 · vinuthan · **PASS for generated-only integration. Real-source packaging remains disabled/unverified.** Owner authorised this engineering task, not dental-image/ICC reads, actual packaging, cloud or training. No real dataset, inventory or DRAFT was opened. Existing Option A failures/limits and B1 v1/v2/trainer remain unchanged.

## Explicit new pathway and actual checks

New `src/vision/exploratory_bundle_b1.py` exposes `prepare_generated_plan`, `authorization_bindings`, `package_generated_b1` and `validate_generated_package`. Version `pp1-b1-generated-export-v1`, scope `package_generated_development_b1_v1`. There is no dispatcher or A/B fallback. Inputs are strict generated DRAFT dictionaries and fixed `GeneratedSource` recipes; no real image path/root/ICC decoder argument exists.

| Gate | Implementation / verification |
|---|---|
| Current selection | Reuse legacy `select_candidates` and `fixed_cohort`, then require914 distinct synthetic records =680 Training +53 Validation +181 reasoned holds (52 Training/129 Validation); both NP015 IDs held; exact three eligible Validation CAM IDs. Five-grade schema/provisional labels unchanged. |
| Content/Test isolation | Candidates must be singleton groups with original split unchanged; blocked/uncertain groups and needs_review rejected. Actual generated RGB SHA+geometry duplicates rejected across or within splits even if group names differ. Test/nondevelopment rows rejected before labels. No participant identity invented. |
| Trusted source plan | Each selected recipe is actually generated/converted in bounded chunks before any output, measuring RGB/profile hashes and inherited precision/range. Rebuild and compare against independently trusted plan SHA; do not accept input pass flags. Synthetic plan SHA intentionally differs from the real pinned cohort identity. Real733 membership has not been revalidated here. |
| Owner scope / freshness | Explicit opt-in and separate B1 scope; current code closure, B1 contracts, DRAFT/plan, output ID and resolved path bound. Old A scope, stale bindings, missing acknowledgements or real-packaging=true rejected. Exclusive persistent attempt marker/new private directory/no links or overwrite; failure consumes that output ID. |
| Actual export | Reuse unchanged v2 streaming conversion and verification for every generated record. Check stage source hashes/precision against preflight; preserve extended floats. Copy733 model224 NPYs and733 source receipts; only Validation00733/00734/00766 keep full canonical NPY. Other full generated arrays are temporary and removed after checked copying. |
| Actual post-write | Read/check all NPY headers,exact sizes,dtype/order,finite/range,geometry and hashes with v2 verifier primitives. Strict JSON/nested receipt/privacy schemas; source/contract/plan correlation. Retained full CAMs are resampled and compared with actual model arrays. Source colour is measured preflight/during conversion; an offline receipt/hash is not independent proof of clinical provenance. Non-CAM full arrays are no longer present for offline source-to-model remeasurement. |
| Complete package | Exact manifest membership and allowed directory ancestors; no empty Test/private directories,links or extras. All checks precede ZIP publication. ZIP entry regular-file type,size,encoding,CRC/hash and membership checked. Manifest/COMPLETE alone cannot confer validity: public verifier also requires matching final ZIP and external manifest/binding trust. Final ZIP is exclusively hard-linked from verified `.zip.partial`; no overwrite. Injected publication failure remains invalid and cannot replay. |
| Attribution / approvals | CC BY4.0 source title/creator/version,DOI10.17632/3253gj88rr.1,licence/source URLs and explicit float-colour/resize/metadata/display transformation notice retained. Notice clearly says these are generated fixtures, not Mendeley photos. Qualified labels, participant independence and final research flags remain false. |

Authorization objects in tests are explicitly named **SYNTHETIC_TEST_ONLY** and exist only inside newly generated temporary fixtures. No real owner packaging permission record was created. Gate records document scope/provenance; they do not cryptographically authenticate a human or approve clinical labels. Future real use requires a separate real-source adapter/version and genuine fresh owner decision; setting a boolean cannot enable it.

## Actual focused evidence

**48 passed,0 failed,0 errors,0 skipped**,24.55s. New suite only: `tests/test_exploratory_bundle_b1.py`. Reused prior Colab77/77 and full-resolution57/57 evidence without rerunning them; no model execution.

One complete generated run exported and independently post-verified:

- 680 Training +53 Validation records;181 holds excluded; NP015/protected groups excluded; zero Test recipes.
- **1469 payload files**:733 model NPYs +733 source receipts +3 full CAM NPYs; one additional bundle manifest in ZIP. Completion/attempt markers are control evidence outside archived payload membership.
- Actual first generated model range **-0.1315616518 to1.0068248510**, confirming no clipping.
- Generated ZIP **3746909 bytes**; SHA256 `90593a7b42024e0ca3f7feeca7250e635c7024c09be5ffba1048af9761a5a1e7`. This is synthetic test output in temporary storage, not a dental package or cloud artefact. Container hashes can vary with fresh output bindings/timestamps; canonical source/NPY conversion remains deterministic.
- Manifest SHA256 `947c68e053efcc67478d7742797472fa327ac6b8154446fe0e06cdcb09226e5b`. Detailed current source/contract hashes and test counts: [generated evidence](vision_b1_generated_export_evidence_v1.json). Transient JUnit `/tmp/rp_b1_export_integration_v1.xml`.

Negative cases cover invalid cohort/holds/CAMs,NP015/protected/review/multiple groups,actual duplicate pixels,unsupported generated ICC,wrong or stale authorization/code/contracts/output,source paths,extra recipes,private root/row/held/nested metadata,unsafe/corrupt NPY,tampering,extra files/directories,missing completion and link-type archive metadata. Rebound file hashes cannot legitimise malformed NPY or unknown nested fields. Injected conversion failure creates no manifest/ZIP; injected publication failure leaves no final ZIP and public validation rejects it. No silent exclusions,retry,threshold relaxation or A fallback.

## Separate exploratory MGI1–4 decision note

**Recorded distinction, not a model activation:** currently supported image-grade evidence is1–4, and a non-clinical PP1 supported-grade exploration is separate from the signed five-grade MGI0–4 research objective. This generated integration retains **five definitions and five model outputs**, does not fabricate MGI0, change labels, suppress/renormalize class0 scores or modify the proposal. Actual labels remain unapproved and participant independence unknown; scarce MGI1/missing whole-imageMGI0 persist.

A future **four-output exploratory model is PENDING**, requiring explicit owner methodological decision, separately versioned model/head and grade-index mapping, loss/metrics/class-support definitions, evaluation protocol, tests and training permission. It is not approved final research scope and is not silently inferred from the current task. No such configuration or model was implemented. This pending decision does not prevent generated export-gate qualification.

## Remaining real-source blockers / next single action

1. **Real JPEG/ICC compatibility unverified:** no real profile/JPEG,EXIF orientation,decoded-source geometry,colour provenance or decoder RAM measured. Existing supported generated matrix/TRC subset cannot establish compatibility for733 real files. Existing cached header/diagnostic evidence should be reused first; any actual source read requires separate scope.
2. **Real adapter and pinned-cohort integration absent:** no entry point consumes real DRAFT/inventory/images. Future adapter must preserve actual frozen identity,733/181/NP015/groups/Test safeguards,source hashes,metadata stripping/attribution/full CAM/display geometry,full-cohort precision/resource checks and fresh B1 authorization. This task proves the structural gates with generated inputs only.
3. **Actual local packaging/cloud/pilot approvals absent:** a new real-use B1 contract/owner packaging decision and full-cohort qualification are needed before a real attempt. Original training gate/clinical approvals are unchanged. Prior Option A authorization is consumed and cannot be reused.

**ONE next action:** separately authorise a **focused read-only real JPEG/ICC compatibility preflight**, reusing cached evidence first, with no export/packaging/training. Its findings determine the smallest required real-source adapter changes. Do not run that step automatically.

Teaching: `prepare_generated_plan()` measures actual generated pixels before output. `_authorize()` binds a separate scope to current code/plan/contracts/output. `validate_generated_package()` requires complete actual payloads and a trusted manifest, not a success flag. Viva: **Does a generated733-record package prove the dental cohort is ready?** இல்லை—gate/software checks மட்டும். Real source compatibility,clinical labels மற்றும் permissions தனியாகவே இருக்கின்றன.
