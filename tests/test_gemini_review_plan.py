"""Generated review metadata only; no images, Test payloads or AI services."""
from copy import deepcopy
import pytest
from src.vision.gemini_review_plan import prepare_plan


def generated():
    rows = []
    for split, count in [('Training', 52), ('Validation', 129)]:
        for i in range(count):
            path = f'Dataset/{split}/Images/{i:05d}.jpg'
            rows.append({'draft': {'original_split': split, 'source_record_id': f'{split}/{i:05d}',
                'image_path': path, 'technical_candidate': False, 'qualified_label_approved': False,
                'training_eligible': False, 'mgi_grade': None,
                'group_original_split_presence': [split, 'Test'] if split == 'Training' and i < 9 else [split],
                'draft_exclusion_reasons': ['annotation_review'], 'content_group_id': f'group-{split}-{i}',
                'group_source_member_count': 1, 'participant_identity_status': 'unknown',
                'label_provenance': {'source_reference': 'generated.csv#' + str(i)}},
                'cached_qa': {'image_path': path, 'original_split': split, 'approved_mgi_grade': None,
                    'qa_issues': ['generated_issue'], 'original_mgi_max': None,
                    'candidate_image_maximum': None, 'csv': {'captions': [{}, {}, {}]}, 'txt': {}}})
    return {'status': 'review_only_not_approved', 'activated': False, 'training_ready': False, 'records': rows}


def test_batches_are_deterministic_split_separate_and_non_destructive():
    source = generated(); before = deepcopy(source)
    plan = prepare_plan(source)
    assert source == before and plan == prepare_plan(source)
    assert len(plan['tracking']) == 181 and len(plan['batches']) == 12
    # 43 Training uses 3 batches (15/14/14);129Validation uses9(15/15/15/14/14/14/14/14/14).
    assert sum(b['count'] for b in plan['batches']) == 172
    for batch in plan['batches']:
        assert 10 <= batch['count'] <= 15
        assert all(i.startswith(batch['original_split'] + '/') for i in batch['image_ids'])
        assert batch['upload_ready'] is False


def test_protected_aliases_only_in_local_tracker_never_proposed_upload():
    plan = prepare_plan(generated())
    blocked = [r for r in plan['tracking'] if r['external_payload_status'] == 'blocked_protected_test_alias']
    assert len(blocked) == 9 and all(not r['proposed_batch'] for r in blocked)
    assert not {r['image_id'] for r in blocked} & {i for b in plan['batches'] for i in b['image_ids']}
    assert all(r['review_status'] == 'pending' and not r['training_eligible']
               and not r['upload_ready'] and r['approved_grade'] == '' for r in plan['tracking'])


@pytest.mark.parametrize('fault', ['Test', 'duplicate', 'path', 'approved', 'two_captions', 'active'])
def test_unsafe_evidence_fails_closed(fault):
    source = generated();r = source['records'][0]
    if fault == 'Test': r['draft']['original_split'] = 'Test'
    if fault == 'duplicate': source['records'][1] = deepcopy(r)
    if fault == 'path': r['draft']['image_path'] = 'Dataset/Training/Images/../00000.jpg'
    if fault == 'approved': r['draft']['training_eligible'] = True
    if fault == 'two_captions': r['cached_qa']['csv']['captions'] = [{}, {}]
    if fault == 'active': source['activated'] = True
    with pytest.raises(ValueError): prepare_plan(source)
