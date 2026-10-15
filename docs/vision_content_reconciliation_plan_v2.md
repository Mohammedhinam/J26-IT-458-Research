# Vision content reconciliation and manifest plan — v2

Date: 2026-10-14. Branch: `vinuthan`. **PROPOSED — no group/split/label/manifest activation.**

Authority: AGENTS.md §§3, 6.1, 13; signed Component 2 proposal §§3.2/3.5, pp.17–18/22. Preserve RGB → maximum visible MGI 0–4 → Grad-CAM and the independent questionnaire branch. Content grouping is not participant identification or clinical label approval.

## Evidence and provenance verified

Reused cached `content_grouping_proposed_v1.json`, the 14 `confirmed_exact_groups.json` entries and `review_pairs_reviewed_v1_20261014.csv` with its provenance sidecar. Reviewer **Vinuthan T**, date **2026-10-14**, recorded scope **manual visual image-content review**. CSV checksum agrees with the provenance sidecar; original spoken CSV/register/viewer checksums remain unchanged. All 54 NP IDs, source group IDs and preview paths match existing candidate evidence; 47 distinct / six visually_same_content / one uncertain are preserved verbatim in the new proposal JSON.

No re-extraction, dHash screening, image hashing/decoding, label audit or model inference. Only cached group IDs, filenames, original splits and owner-confirmed content decisions feed the graph/placement. Cached annotation fields, Test grades and model outcomes do not feed it. New deterministic proposed group IDs hash cached IDs, not image files.

## Exact counts from this reconciliation

| Quantity | Count | Meaning |
|---|---:|---|
| Original source image records | 1,096 | All retained with original membership |
| Existing exact duplicate pairs/groups | 14 | Confirmed byte/pixel evidence unchanged |
| Cached exact content groups including singletons | 1,082 | Before new human same-content edges |
| Human same-content pair edges added to proposal | 6 | Owner findings; no uncertain/distinct edge added |
| Components joining formerly separate exact groups | 5 | One three-node chain plus four two-node joins |
| **Reconciled proposed content groups** | **1,076** | Six independent component reductions, not 20 duplicate groups |
| Non-singleton proposed groups | 16 | 12 two-source groups and four three-source groups |
| Source records in non-singleton groups | 36 | No double-counting |
| Singleton content groups | 1,060 | Content singletons, not proven distinct participants |
| Redundant source records under one-representative scenario | 20 | 1,096 − 1,076; no source deletion |
| Original cross-split reconciled content groups | 8 | Seven Training–Test, one Training–Validation; 18 source members |
| Distinct-content decisions retained | 47 | Zero same-content-closure contradictions; not participant independence |
| Uncertain pair / separate unresolved groups | 1 / 2 | NP015 remains separate, never merged or assumed independent |

The two cross-split same-content findings extend existing cross-split exact groups. They are not two additional independent cross-split groups; **eight remains eight**, with expanded membership.

### Human-edge transitivity and exact-group aliases

| Human edge(s) | Source members in resulting proposal component | Proposed reservation |
|---|---|---|
| NP033 | Test 00949; Training 00571, 00572 | Test |
| NP036 | Test 00945; Training 00272, 00273 | Test |
| NP040 | Training 00575, 00576, 00722 | Training |
| NP041 | Training 00584, 00728 | Training |
| NP046 + NP053 | Test 01308, 01311, 01310 | Test |

NP046/NP053 share Test 01311. Their two edges form **one three-image component**, not two unrelated pairs. NP033/NP036/NP040 each extend a cached exact pair; every exact alias is retained. No cycle/redundant human edge was found. None of the 47 distinct edges has endpoints inside the same reconciled content component.

## Actual original cross-split content conflicts

| Original Training aliases | Original evaluation source | Human extension | PROPOSED handling |
|---|---|---|---|
| 00271 | Test 00943 | — | Reserve complete group for Test |
| 00273, 00272 | Test 00945 | NP036 adds 00272 | Same; both Training aliases stay out of development |
| 00275 | Test 00947 | — | Reserve complete group for Test |
| 00566 | Test 00944 | — | Reserve complete group for Test |
| 00568 | Test 00946 | — | Reserve complete group for Test |
| 00570 | Test 00948 | — | Reserve complete group for Test |
| 00572, 00571 | Test 00949 | NP033 adds 00571 | Same; both Training aliases stay out of development |
| 00590 | Validation 00735 | — | Reserve complete group for Validation |

This is content overlap, not a participant census. NP015 adds **one unresolved possible Training–Validation participant-overlap relation**, not a ninth confirmed content conflict.

## Label-blind proposed handling and counts

Reuse the previously proposed deterministic rule **Test > Validation > Training**. Reserve every complete verified-content component to its highest-priority original split; choose the lexicographically first original path within that destination as a proposed single representative. No selection based on grades, image severity, class balance, validation scores or Test outcomes. Preserve every alias and original split as provenance; physical files/membership are never moved or rewritten.

| Scenario — not activated | Training content groups | Validation content groups | Test content groups | Total |
|---|---:|---:|---:|---:|
| Prior exact-only proposal | 718 | 182 | 182 | 1,082 |
| Exact + six human-same edges, before NP015 resolution | **714** | **182** | **180** | **1,076** |
| IF both entire NP015 groups are held pending review | **713** | **181** | **180** | **1,074** |

All counts include unapproved labels and unknown participant identity. They are **content-group arithmetic, not a final eligible cohort or permission to train**. Compared with original 732/182/182 sources, one-representative proposal omits 18 Training aliases and two within-Test aliases from the hypothetical representative list; originals remain intact. The original Test contains 182 source images, while the hypothetical content-independent Test units number 180. Supervisor must approve this evaluation-unit change and its relation to proposal §3.5.

NP015 is Validation `00736.jpg` versus Training `00591.jpg`, RC014: owner retained **uncertain**, possible same participant/different angle, identity unverified. Both currently correspond to separate singleton exact-content groups. Recommended conservative option is to **hold both complete groups from every analysis partition** until qualified resolution, retaining the unresolved link separately. This option is not activated. Do not merge them into a confirmed content group, choose one by its grade, or keep both in different splits as if independence were proven.

Quarantine would address this known unresolved relation only. It cannot prove global participant independence. Likewise, 47 different-photograph decisions do not prove 47 different people.

## Proposed final-manifest construction sequence

1. Supervisor reviews the six content-equivalence findings/closure, eight confirmed cross-split groups and NP015 handling. Approve the identity/grouping basis, reservation/representative policy and original-Test protection, or specify a participant-grouped alternative with fixed rules. Do not choose a policy using final-Test labels/outcomes.
2. Qualified dental/annotation reviewer adjudicates caption/TXT conflicts and label provenance jointly across source aliases. Preserve source labels; no automatic maximum across disputed variants, majority label, healthy-class substitution or reviewer impersonation. The 274 policy candidates and 339 QA records remain unapproved/uncleared.
3. Resolve missing image-level MGI 0 support and scarce MGI 1 feasibility while retaining the signed five-grade definitions. Any revised scientific protocol needs explicit supervisor approval; this proposal changes none.
4. After those approvals, build a **new versioned draft** from approved eligible records only, with original filename/split, cached hashes, reviewed content group, verified participant identity/provenance, approved analysis split, final image-level label/provenance, reviewer/date, explicit exclusions/holds and all source references. Leave absent evidence unresolved; do not invent participant IDs or grades. If eligibility changes representatives, apply a separately approved label-blind deterministic rule and log it; do not silently choose a conveniently labelled alias.
5. Verify group/participant disjointness, all alias reservations, Test sealing, source coverage/exclusion accounting and per-grade support; obtain qualified final label/split/manifest signature and checksum freeze. Freeze the training protocol and obtain separate training authorisation. No final manifest or eligible-label list is generated here.

Current trainer requires real verified participant IDs and externally authenticated label/split/protocol evidence. **A content-group ID is not a participant ID**, and supervisor acknowledgement of unknown identities does not satisfy the current code gate automatically. If evidence cannot meet that requirement, stop for a documented proposal-aligned resolution and separately authorised interface change; never bypass it with placeholders or always-true callbacks.

## Versioned outputs and verification

New ignored detail artifact:

`data/vision/gingivitis/staging-16669f74665ff0deca6ddd25feb0d233e52fdc2313265465bf91731af1e8956b/content_reconciliation_proposed_v2_20261014.json`

It contains all 1,076 proposed groups with original source membership, all 54 untouched manual decision records, the 14 preserved exact-group entries, the five human-joined components, eight actual cross-split groups, NP015 unresolved link, source hashes and both hypothetical scenarios. Every placement has `activated=false`; labels/participant/manifest/training approvals are false and `training_ready_manifest=false`. Existing v1 artifacts remain unchanged.

Focused analysis checks passed: reviewer/date/input checksums; 54-candidate correspondence; exact-group membership; independent image-path graph versus cached-group graph; deterministic reversal and repeated-edge invariance; no distinct/same transitive contradictions; full 1,096-source coverage; NP015 separation; label-blind reservation; JSON readback and all inactive flags. Initial JSON readback assertion compared integer histogram keys with JSON string keys; corrected the verification to normalise key types, with no change to data/counts. No modelling/previous audit test suites rerun, package installation, commit or push.

Teaching: same-content edges connect cached groups, transitivity prevents counting a chain twice, and highest-priority split reservation protects evaluation content without consulting labels. This document proposes handling; it does not grant human/clinical approval.

Viva: Why are there eight cross-split groups rather than ten? The two human cross-split edges add Training aliases to two already existing Training–Test exact groups; they do not create two separate cross-split groups.
