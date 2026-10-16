"""Local-only review scheduling; no image reads, packaging or cloud actions."""
from collections import Counter
from copy import deepcopy
from pathlib import PurePosixPath

SPLITS = ('Training', 'Validation')
CLASS_MAPPING = {'0': 'upper jaw ROI', '1': 'lower jaw ROI',
                 '2': 'MGI 0', '3': 'MGI 1', '4': 'MGI 2', '5': 'MGI 3', '6': 'MGI 4'}


def balanced_batches(rows):
    """Use 10–15 records per batch without mixing original splits."""
    if len(rows) < 10:
        raise ValueError('Too few records for a 10-image batch')
    count = (len(rows) + 14) // 15
    size, extra = divmod(len(rows), count)
    if size < 10:
        raise ValueError('Cannot satisfy batch size without an explicit exception')
    result, offset = [], 0
    for index in range(count):
        length = size + (index < extra)
        result.append(rows[offset:offset + length])
        offset += length
    return result


def prepare_plan(cached):
    """Build draft tracking from existing evidence; never manufacture approvals."""
    if (cached['activated'] is not False or cached['training_ready'] is not False
            or cached['status'] != 'review_only_not_approved'):
        raise ValueError('Inactive review evidence required')
    records = deepcopy(cached['records'])
    if Counter(r['draft']['original_split'] for r in records) != {'Training': 52, 'Validation': 129}:
        raise ValueError('Expected exactly 52 Training and 129 Validation holds')
    ids = [r['draft']['source_record_id'] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate record ID')
    tracking, batches, local = [], [], []
    for record in sorted(records, key=lambda r: r['draft']['source_record_id']):
        row, qa = record['draft'], record['cached_qa']
        split, identity = row['original_split'], row['source_record_id']
        filename = PurePosixPath(row['image_path']).name
        expected = f'Dataset/{split}/Images/{filename}'
        if (split not in SPLITS or row['image_path'] != expected
                or identity != split + '/' + PurePosixPath(filename).stem
                or qa['image_path'] != expected or qa['original_split'] != split
                or '..' in PurePosixPath(row['image_path']).parts):
            raise ValueError('Unsafe or inconsistent source identity/path')
        if (row['technical_candidate'] is not False or row['qualified_label_approved'] is not False
                or row['training_eligible'] is not False or row['mgi_grade'] is not None
                or qa['approved_mgi_grade'] is not None):
            raise ValueError('Existing unapproved held state must be preserved')
        if len(qa['csv']['captions']) != 3:
            raise ValueError('Expected all three cached caption variants')
        protected = ('Test' in row['group_original_split_presence']
                     or 'protected_test_content_group' in row['draft_exclusion_reasons'])
        item = {'image_id': identity, 'filename': filename, 'original_split': split,
                'proposed_batch': '', 'review_status': 'pending',
                'external_payload_status': 'blocked_protected_test_alias' if protected else 'pending_privacy_colour_owner_review',
                'content_group_id': row['content_group_id'],
                'group_source_member_count': row['group_source_member_count'],
                'group_splits': ';'.join(row['group_original_split_presence']),
                'participant_identity_status': row['participant_identity_status'],
                'hold_reasons': ';'.join(row['draft_exclusion_reasons']),
                'annotation_conflicts': ';'.join(qa['qa_issues']),
                'cached_provisional_mgi_max': qa['original_mgi_max'],
                'candidate_mgi_max': qa['candidate_image_maximum'],
                'caption_variant_count': 3,
                'source_image_reference': expected,
                'source_caption_reference': row['label_provenance']['source_reference'],
                'source_txt_reference': f'Dataset/{split}/Labels/{PurePosixPath(filename).stem}.txt',
                'reviewer': '', 'review_date': '', 'ai_service_model': '',
                'ai_response_reference': '', 'qualified_reviewer': '', 'approved_grade': '',
                'qualified_label_approved': False, 'training_eligible': False,
                'upload_ready': False}
        # Existing parsed variants are evidence, not reconstructed original captions.
        local.append({'tracking': item, 'cached_caption_variants': qa['csv']['captions'],
                      'cached_txt_evidence': qa['txt']})
        tracking.append(item)
    for split in SPLITS:
        selected = [r for r in tracking if r['original_split'] == split
                    and r['external_payload_status'] != 'blocked_protected_test_alias']
        for index, rows in enumerate(balanced_batches(selected), 1):
            batch = f'{split}/batch_{index:02d}'
            for row in rows:
                row['proposed_batch'] = batch
            batches.append({'batch_id': batch, 'original_split': split, 'count': len(rows),
                            'status': 'LOCAL_PLAN_ONLY_NOT_UPLOAD_READY',
                            'image_ids': [r['image_id'] for r in rows],
                            'original_rgb_copied': False, 'original_caption_text_copied': False,
                            'original_txt_copied': False, 'upload_ready': False})
    return {'status': 'LOCAL_PLAN_ONLY_NOT_UPLOAD_READY', 'tracking': tracking,
            'batches': batches, 'local_cached_evidence': local, 'class_mapping': CLASS_MAPPING,
            'source_labels_changed': False, 'training_eligibility_changed': False,
            'external_upload_authorized': False}
