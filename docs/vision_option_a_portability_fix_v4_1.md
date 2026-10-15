# Option A verification artifact portability fix v4.1

2026-10-15, branch **vinuthan**. Artifact packaging fix only; the underlying v4 export policy, implementation, selected test assertions and research-training gate are unchanged. No real dental/Test payload, packaging, model execution, installation/download, commit or push.

## Confirmed cause and reproduction

The original v4 code-only ZIP/notebook contained 11 declared code/test files. All declared hashes were correct, but **`src/vision/exploratory_pilot.py` was absent**. Legacy `exploratory_bundle.source_code_hashes()` reads that file along with the bundle, model and trainer modules. Its bytes are required by the selected legacy tests even though no pilot is run. The v4 hash list had six source modules; the union of both hash lists is **seven source modules**. Together with the three selected test files and two imported fixture helpers, the required closure is **12 files**, plus `code_manifest.json`.

Fresh extraction of the original ZIP **outside the repository**, followed by actual execution of the exact 131 selected cases, reproduced the owner's result: **104 passed, 8 failed, 19 errors, 0 skipped (2.25 s)**. All 27 nonpassing cases reported the missing pilot file. This confirms a dependency omission, not a colour-policy failure.

The previous v4 report's local 131-pass run was from the full repository. Its archive check only collected tests; collection does not exercise runtime `source_code_hashes()`. Consequently that earlier evidence did not establish that the archive was executable in isolation. Original reports/artifacts remain unchanged as historical evidence; this record supplies the correction. No actual Colab failure ZIP was attached for independent inspection in this task; the provided counts were independently reproduced on the Mac.

## Minimal fix and exact changed files

New files:

- `src/vision/build_option_a_verification_bundle.py` — durable standard-library-only builder, replacing reliance on an ad hoc temporary build command. Reads both existing hash dependency declarations through AST without executing a pilot or accessing images. Their union supplies source files; selected tests and imported helpers are explicit. Fails if files are missing or versioned outputs exist.
- `docs/vision_option_a_export_code_v4_1.zip` — **63,426 bytes**; SHA-256 **`7d740888aead7bd21152bcb0ed65814e39512585ddc0cefa69cd77619867cd07`**.
- `docs/vision_option_a_export_verification_v4_1.ipynb` — new notebook with full 12-file allowlist/hashes, new archive hash, fresh working directory and versioned evidence ZIP name. Underlying export version remains v4.
- This report.

Append-only updates: `docs/diary.md`, `docs/ai_log.md`.

The original 11 bundled files are byte-identical between archives; the **only added payload dependency is `exploratory_pilot.py`**, matching its current preserved source hash. It is included for hashing, not invoked. No extra test collection, datasets, manifests, permission records, weights or unrelated modules were added. No source implementation, existing tests/assertions, old v4 ZIP/notebook/report, clinical labels, splits or approval records were modified.

## Fresh-isolation verification

| Actual selected execution | Passed | Failed | Errors | Skipped |
|---|---:|---:|---:|---:|
| Original v4 ZIP, fresh extracted root | 104 | 8 | 19 | 0 |
| New v4.1 ZIP, another fresh extracted root | **131** | **0** | **0** | **0** |

Final run: **2.05 s**; new integration tests 40, shared legacy tests 70, ICC tests 21. Supporting `test_colour_qa.py` and `test_colour_policy.py` provide imported fixtures only; their full suites were not collected or rerun. No assertion was changed to obtain this result.

Isolation used a new temporary directory outside the repository and Python **`-I -B`**, disabled pytest plugin autoload, explicit empty pytest configuration, extracted-root `--rootdir`/`--confcutdir` and generated-only temporary files. Only the extracted root was added for local imports. The existing installed pytest package path was appended after the bundled dependency runtime; no package installation occurred. Every loaded project/test module origin was checked to lie inside the extraction. Both runs verified declared source hashes before/after; no sources changed. The original archive's 11 SHA checks passed even while its tests failed, demonstrating why dependency completeness and actual execution are necessary.

Runtime: Python **3.12.14**, NumPy **2.3.5**, Pillow **12.3.0**, pytest **9.1.1**, LittleCMS **2.19**, Mac CPU. The new notebook additionally runs both real `source_code_hashes()` functions against its manifest before pytest. Its child uses `-I`, removes `PYTHONPATH`, pins pytest config/root, and records import origins. ZIP CRC, exact inventory, all 12 file hashes, notebook embedded hash/allowlist and Python cell syntax match. No Colab v4.1 success is claimed before execution there.

Ignored evidence: `data/vision/option_a_portability_v4_1_20261015/` contains original-failure and fixed-success stdout/JUnit/verification JSON, new artifact bindings and preservation record. Temporary isolated roots are recorded in those JSONs; generated fixtures remain outside the repository. Evidence contains code/runtime/test facts only, no dental pixels or labels.

## One next Colab step

Open **`vision_option_a_export_verification_v4_1.ipynb`** in a fresh **CPU** Colab runtime. Run cells in order; upload **only `vision_option_a_export_code_v4_1.zip`** when prompted. Expected: **131 passed, 0 failed/errors/skipped**, all 12 hashes unchanged and local imports confined to extracted code. Download **`vision_option_a_export_runtime_evidence_v4_1.zip`** even on failure and report its actual results. No Drive mount, dental images, package installation, weights or pilot run are needed; `RUN_PILOT=False` remains set.

This repair does not activate actual image packaging or the pilot. Fresh real-packaging authorization and previously documented data-use, privacy, source, cohort/group/Test-isolation checks remain necessary. Missing MGI 0, provisional labels, scientific approvals and the separate v4 pilot-reader integration are unchanged blockers.

## Simple explanation for the owner

1. Hash சரியாக இருப்பது, சேர்த்த files மாறவில்லை என்பதைத்தான் காட்டும். தேவையான file விட்டுப்போகவில்லை என்று அது சொல்லாது.
2. இரண்டு `source_code_hashes()` lists-ஐ union செய்வதால் அவை தேடும் code files எல்லாம் புதிய ZIP-ல் சேரும். Pilot இயக்கப்படாது.
3. `-I` மற்றும் extracted-root imports மூலம் full repo-வில் இருக்கும் missing file-ஐ test தவறுதலாக எடுத்துப் pass ஆகாமல் தடுக்கிறோம். அதே 131 tests இப்போது தனியாக pass ஆகின்றன.

Viva: **Why did collection pass but execution fail?** Collection test பெயர்களை மட்டும் கண்டுபிடித்தது. Test ஓடும்போதுதான் hash function missing file-ஐத் திறக்க முயன்றது.
