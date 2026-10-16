"""Synthetic cached annotations, including deliberately malformed sealed bodies."""
import io
import json

import pytest

from src.vision import held_review_workflow as review


def row(split='Training', identity='00001'):
    return {'source_record_id': split + '/' + identity, 'original_split': split,
            'image_path': 'Dataset/' + split + '/Images/' + identity + '.jpg',
            'technical_candidate': False, 'qualified_label_approved': False,
            'training_eligible': False, 'mgi_grade': None, 'participant_id': None,
            'analysis_split': None, 'draft_exclusion_reasons': ['cached_qa_requires_review'],
            'cached_qa_requires_review': True, 'cached_qa_issues': ['annotation_tooth_count_review'],
            'reconciliation_reserved_split_proposal': split, 'content_group_id': 'generated_' + identity,
            'group_source_member_count': 1, 'group_original_split_presence': [split],
            'label_provenance': {'source_reference': 'synthetic annotation'}}


def fixture_record(split, identity, body='"approved_mgi_grade": null'):
    return ('  {\n    "image_path": "Dataset/' + split + '/Images/' + identity + '.jpg",\n'
            '    "original_split": "' + split + '",\n    ' + body + '\n  }')


def test_selection_decodes_only_requested_development_records():
    text = '[\n' + ',\n'.join([
        fixture_record('Test', '99999', 'MALFORMED_TEST_BODY_MUST_NOT_DECODE'),
        fixture_record('Training', '00001'),
        fixture_record('Validation', '00733'),
        fixture_record('Validation', '00734', 'MALFORMED_UNSELECTED_BODY')]) + '\n]\n'
    wanted = {'Dataset/Training/Images/00001.jpg', 'Dataset/Validation/Images/00733.jpg'}
    assert set(review.selected_cached_records(io.StringIO(text), wanted)) == wanted


@pytest.mark.parametrize('fault', ['missing', 'duplicate', 'labels_first', 'incomplete'])
def test_bad_cache_layout_fails_closed(fault):
    text = '[\n' + fixture_record('Training', '00001') + '\n]\n'
    wanted = {'Dataset/Training/Images/00001.jpg'}
    if fault == 'missing': wanted.add('Dataset/Training/Images/00002.jpg')
    if fault == 'duplicate': text = '[\n' + fixture_record('Training', '00001') + ',\n' + fixture_record('Training', '00001') + '\n]\n'
    if fault == 'labels_first': text = text.replace('    "original_split": "Training",', '    "grade": 4,')
    if fault == 'incomplete': text = text.replace('\n  }\n]', '')
    with pytest.raises(ValueError): review.selected_cached_records(io.StringIO(text), wanted)


@pytest.mark.parametrize('split', ['Training', 'Validation'])
def test_all_human_and_grade_fields_remain_blank(split):
    original = row(split)
    before = json.dumps(original, sort_keys=True)
    output = review.pending_record(original)
    assert json.dumps(original, sort_keys=True) == before
    for key in ['reviewer', 'qualification', 'review_date', 'evidence_reference', 'proposed_grade']:
        assert output[key] == ''
    assert output['decision_status'] == 'pending'
    assert output['qualified_label_approved'] == output['training_eligible'] == 'false'


@pytest.mark.parametrize('fault', ['test', 'eligible', 'approved', 'grade', 'participant', 'split', 'path', 'candidate'])
def test_forbidden_source_or_state_rejected(fault):
    value = row()
    if fault == 'test': value = row('Test')
    if fault == 'eligible': value['training_eligible'] = True
    if fault == 'approved': value['qualified_label_approved'] = True
    if fault == 'grade': value['mgi_grade'] = 0
    if fault == 'participant': value['participant_id'] = 'invented'
    if fault == 'split': value['analysis_split'] = 'Training'
    if fault == 'path': value['image_path'] = 'Dataset/Test/Images/00001.jpg'
    if fault == 'candidate': value['technical_candidate'] = True
    with pytest.raises(ValueError): review.pending_record(value)


def test_overlap_counts_do_not_create_extra_cases():
    a, b, c, d = row(), row('Validation', '00733'), row(identity='00002'), row(identity='00003')
    a['cached_qa_issues'] = [review.PARTIAL, 'incomplete_caption_positions']
    a['group_source_member_count'] = 2
    a['group_original_split_presence'] = ['Training', 'Test']
    a['draft_exclusion_reasons'].append('protected_test_content_group')
    b['draft_exclusion_reasons'].append(review.IDENTITY)
    c['cached_qa_requires_review'] = False
    summary = review.summarize([a, b, c, d])
    assert sum(value['held'] for value in summary.values()) == 4
    assert sum(summary['Training']['primary_queue'].values()) == 3
    assert summary['Training']['qa_flags_overlap'][review.PARTIAL] == 1
    assert review.boundary_status(a) == 'protected_evaluation_group_keep_held'
    assert review.primary_queue(b) == 'identity_uncertain'
    assert review.primary_queue(c) == 'group_companion'


def test_untrusted_input_rejected_before_output_creation(tmp_path):
    draft, qa, output = tmp_path / 'draft.json', tmp_path / 'qa.json', tmp_path / 'output'
    draft.write_text('{}')
    qa.write_text('[]')
    with pytest.raises(ValueError, match='Untrusted'):
        review.build(draft, qa, output)
    assert not output.exists()
