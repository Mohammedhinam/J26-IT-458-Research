"""Cached development review preparation only; no image reader or approval action."""
from collections import Counter
import csv
import hashlib
import html
import json
from pathlib import Path
import re

from . import exploratory_bundle as boundary

DRAFT_SHA = 'b9777bdcb1ee88b2b7ac0f0a24c9d5404a9c54f1f8c5b677ab8ed9a5fe7f27c1'
QA_SHA = '5e56facd669fee9492412bb9795c8a25cf520783148e0f651b73aa8a8e6e318f'
SPLITS = {'Training', 'Validation'}
PARTIAL = 'lower_jaw_omission_policy_pending'
IDENTITY = 'NP015_possible_participant_overlap_whole_group_hold'


def selected_cached_records(source, wanted):
    """Reuse split-first selection: skipped/Test label bodies are never decoded."""
    if source.readline().strip() != '[':
        raise ValueError('Expected cached array layout')
    inside = False
    prefix, selected, records = [], None, []
    split = image_path = None
    for line in source:
        if not inside:
            if line == '  {\n':
                inside, prefix, selected = True, [line], None
                split = image_path = None
            elif line.strip() not in ('', ']'):
                raise ValueError('Unexpected cached record boundary')
            continue
        if split is None:
            prefix.append(line)
            image = re.fullmatch(r'    "image_path": "([^"\\]+)",\n', line)
            declared = re.fullmatch(r'    "original_split": "(Training|Validation|Test)",\n', line)
            if image and len(prefix) == 2:
                image_path = image.group(1)
            elif declared and image_path is not None and len(prefix) == 3:
                split = declared.group(1)
                selected = prefix if split in SPLITS and image_path in wanted else None
                prefix = []
            else:
                raise ValueError('Split metadata must precede label fields')
            continue
        if selected is not None:
            selected.append(line)
        if line in ('  },\n', '  }\n'):
            if selected is not None:
                value = json.loads(''.join(selected).rstrip().removesuffix(','))
                if value['original_split'] not in SPLITS or value['image_path'] not in wanted:
                    raise ValueError('Unexpected selected record')
                records.append(value)
            inside = False
    if inside or len(records) != len({v['image_path'] for v in records}) or {v['image_path'] for v in records} != set(wanted):
        raise ValueError('Incomplete/duplicate cached selection')
    return {value['image_path']: value for value in records}


def primary_queue(row):
    """Disjoint work queues, not clinical labels or eligibility decisions."""
    if IDENTITY in row['draft_exclusion_reasons']:
        return 'identity_uncertain'
    if row['cached_qa_requires_review']:
        return 'partial_policy' if PARTIAL in row['cached_qa_issues'] else 'annotation_referral'
    return 'group_companion'


def boundary_status(row):
    if 'protected_test_content_group' in row['draft_exclusion_reasons']:
        return 'protected_evaluation_group_keep_held'
    if IDENTITY in row['draft_exclusion_reasons']:
        return 'NP015_keep_held'
    if row['reconciliation_reserved_split_proposal'] != row['original_split']:
        return 'other_split_reservation_keep_held'
    return 'label_group_approval_still_pending'


def pending_record(row):
    """Never populate a human identity, clinical grade or eligibility from code."""
    split = row['original_split']
    if split not in SPLITS or not row['source_record_id'].startswith(split + '/') or row['technical_candidate'] is not False:
        raise ValueError('Only held development records allowed')
    if (row['qualified_label_approved'] is not False or row['training_eligible'] is not False
            or row['mgi_grade'] is not None or row['participant_id'] is not None or row['analysis_split'] is not None):
        raise ValueError('Preserve inactive original review state')
    image = boundary.relative_path(row['image_path']).as_posix()
    if not image.startswith('Dataset/' + split + '/Images/'):
        raise ValueError('Image/split path mismatch')
    return {'record_id': row['source_record_id'], 'original_split': split,
            'primary_queue': primary_queue(row), 'boundary_status': boundary_status(row),
            'hold_reasons': '; '.join(row['draft_exclusion_reasons']),
            'qa_issues': '; '.join(row['cached_qa_issues']),
            'content_group_id': row['content_group_id'], 'group_source_members': row['group_source_member_count'],
            'image_path': image, 'caption_reference': row['label_provenance']['source_reference'],
            'reviewer': '', 'qualification': '', 'review_date': '', 'evidence_reference': '',
            'review_notes': '', 'proposed_grade': '', 'decision_status': 'pending',
            'qualified_label_approved': 'false', 'training_eligible': 'false'}


def summarize(rows):
    result = {}
    for split in sorted(SPLITS):
        selected = [r for r in rows if r['original_split'] == split]
        result[split] = {'held': len(selected), 'primary_queue': dict(Counter(primary_queue(r) for r in selected)),
                         'boundary': dict(Counter(boundary_status(r) for r in selected)),
                         'qa_flags_overlap': dict(Counter(v for r in selected for v in r['cached_qa_issues'])),
                         'group_flags_overlap': {'multi_image': sum(r['group_source_member_count'] > 1 for r in selected),
                             'cross_split': sum(len(r['group_original_split_presence']) > 1 for r in selected)}}
    return result


def build(draft_path, qa_path, output):
    """One fresh ignored review export; originals and old viewers are unchanged."""
    draft_path, qa_path, output = Path(draft_path), Path(qa_path), Path(output)
    for path, expected in [(draft_path, DRAFT_SHA), (qa_path, QA_SHA)]:
        if path.is_symlink() or boundary.sha256(path) != expected:
            raise ValueError('Untrusted cached evidence')
    boundary.new_ignored_output(output, 'data')
    if output.exists():
        raise ValueError('Fresh output required')
    draft = json.loads(draft_path.read_text())
    if draft['status'] != 'draft_not_approved' or draft['activated'] is not False or draft['training_ready'] is not False:
        raise ValueError('Preserve unapproved DRAFT')
    rows = draft['records']
    if len(rows) != 914 or any(r['original_split'] not in SPLITS for r in rows):
        raise ValueError('Development-only DRAFT required')
    held = sorted((r for r in rows if r['technical_candidate'] is False), key=lambda r: r['source_record_id'])
    if Counter(r['original_split'] for r in held) != {'Training': 52, 'Validation': 129}:
        raise ValueError('Pinned held counts mismatch')
    decisions = [pending_record(row) for row in held]
    if len({r['record_id'] for r in decisions}) != 181:
        raise ValueError('Duplicate review IDs')
    with qa_path.open() as source:
        cache = selected_cached_records(source, {row['image_path'] for row in held})
    # Preserve source evidence verbatim; source annotations are not clinical truth.
    if any(value['approved_mgi_grade'] is not None for value in cache.values()):
        raise ValueError('Unexpected cached approval')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    with (output / 'development181_review_decisions.csv').open('x', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=list(decisions[0]))
        writer.writeheader()
        writer.writerows(decisions)
    evidence = {'status': 'review_only_not_approved', 'activated': False, 'training_ready': False,
                'records': [{'draft': row, 'cached_qa': cache[row['image_path']]} for row in held]}
    (output / 'development181_cached_evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    esc = lambda value: html.escape(str(value), quote=True)
    page = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>181 held development cases — pending review</title>',
            '<style>body{font:16px system-ui;max-width:1100px;margin:24px auto;padding:0 16px;background:#f4f7fa;color:#17202a}article,header{background:white;padding:20px;margin:16px 0;border:1px solid #ccd4dd;border-radius:10px}pre,code{white-space:pre-wrap;overflow-wrap:anywhere}input,select{font:inherit;padding:8px}a{color:#0645ad}summary{cursor:pointer}</style>',
            '<header><h1>181 held development cases</h1><p><strong>52 Training +129 Validation. Every decision pending; zero approvals.</strong></p>',
            '<p>Qualified clinical/annotation decisions and supervisor grouping decisions are separate. Source maps/TXT are corroboration, not new clinical truth. Original splits and holds are preserved. No images preload.</p>',
            '<p><a href="development181_review_decisions.csv">Pending decision CSV</a> · <a href="review_instructions.md">Instructions</a> · <a href="../training_recovery_review_v1_20261015/index.html">Existing 52-Training package</a></p>',
            '<label>Search ID or issue <input id="query"></label> <label>Split <select id="split"><option value="">Both development splits</option><option>Training</option><option>Validation</option></select></label><p id="count"></p></header>']
    for row, decision in zip(held, decisions):
        qa = cache[row['image_path']]
        text = (decision['record_id'] + ' ' + decision['primary_queue'] + ' ' + decision['hold_reasons']).lower()
        page.extend(['<article data-split="' + esc(row['original_split']) + '" data-search="' + esc(text) + '"><h2>' + esc(decision['record_id']) + ' — pending</h2>',
                     '<p><b>Queue:</b> ' + esc(decision['primary_queue']) + '<br><b>Boundary:</b> ' + esc(decision['boundary_status']) + '</p>',
                     '<p><b>All hold reasons:</b> ' + esc(decision['hold_reasons']) + '</p><p><b>Proposed content group:</b> ' + esc(row['content_group_id']) + '; not participant identity.</p>',
                     '<p><a href="../' + esc(row['image_path']) + '">Open original development RGB deliberately</a> · <code>' + esc(decision['caption_reference']) + '</code></p>',
                     '<details><summary>Cached caption position evidence</summary><pre>' + esc(json.dumps(qa['csv'], indent=2)) + '</pre></details>',
                     '<details><summary>Cached TXT annotation verification</summary><pre>' + esc(json.dumps(qa['txt'], indent=2)) + '</pre></details>',
                     '<p>Reviewer, qualifications, date, evidence and proposed grade remain blank. A clinical decision cannot release protected groups or authorize training.</p></article>'])
    page.append('<script>function filter(){let q=document.querySelector("#query").value.toLowerCase(),s=document.querySelector("#split").value,n=0;document.querySelectorAll("article").forEach(a=>{a.hidden=!(a.dataset.search.includes(q)&&(!s||a.dataset.split===s));if(!a.hidden)n++;});document.querySelector("#count").textContent=n+" pending cases shown";}document.querySelector("#query").oninput=filter;document.querySelector("#split").onchange=filter;filter();</script></html>')
    (output / 'index.html').write_text('\n'.join(page))
    (output / 'review_instructions.md').write_text('''# Pending development review only

Use the split filter; keep all 181 held. Original RGB links open only on deliberate click. No Test record/grade or model prediction is included. Captions remain primary annotation evidence and TXT is corroboration, never a training input or tooth-ID ground truth.

Qualified reviewer: inspect source evidence and original image if necessary; record actual reviewer/qualification/date/source evidence and unresolved uncertainty in a NEW reviewed CSV copy. Do not edit originals or invent a grade. A partial-caption policy approval is not individual clinical-grade approval.

Supervisor/source custodian: resolve group reservation/representatives and NP015/participant limitations independently of grades/model errors. Protected evaluation aliases remain held; a label decision does not release them.

This viewer has no save/activation/import action. CSV fields do not authenticate qualifications or grant training approval. New manifest construction requires separately verified human decisions and all existing research gates. Do not infer participant IDs, resplit sources, promote records automatically or count overlapping flags as extra cases.
''')
    for path, expected in [(draft_path, DRAFT_SHA), (qa_path, QA_SHA)]:
        if boundary.sha256(path) != expected:
            raise ValueError('Cached source changed during review export')
    summary = {'status': 'pending_review_not_training_ready', 'counts': summarize(held),
               'total_held': 181, 'new_approved_labels': 0, 'new_training_eligible': 0,
               'source_images_opened': False, 'test_objects_decoded': False, 'activated': False,
               'input_sha256': {'draft': DRAFT_SHA, 'qa': QA_SHA},
               'output_sha256': {path.name: boundary.sha256(path) for path in sorted(output.iterdir())}}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary
