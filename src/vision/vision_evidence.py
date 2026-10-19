"""Allowlisted aggregate display evidence; never load datasets or models here."""
from hashlib import sha256
import json
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / 'docs'
SOURCES = {
    'vision_grade2_v2_v3_diagnostic_v1.json': 'ea06ffbeaef873d9721aec2d55ae6fe19111ed320293d6d50159d2a28b18fe59',
    'vision_frozen_feature_signal_results_v1.json': '0ea11860bbf34d4db83524878631e5bcba34894e063191fd723bfabf8cca6f12',
    'vision_efficientnet_probe_results_v1.json': '13be61eb29b1922ca5f66c60e11b19daa091769a5344aaf5ba825f7aa8164eed',
    'vision_efficientnet_head_results_v1.json': 'bf4ac9f190c0541a07c86084e1d2a0c2c1cef2dae4f21772e4bd368c138154a0',
    'vision_nested_feature_probe_results_v1.json': '731dfbdc67f9cd2db6753b997c0e5e14e8ac3d819c991097cfa23e734be13c6d',
    'vision_photo_model_comparison_v1.json': 'c4ba21f3ea84980ca85c6b77f44ca4f14a5ba0818201368574a5564f396fa096'}


def card(name, metrics):
    """Only aggregate metrics cross the API; no IDs, local paths or case rows."""
    matrix = metrics['confusion_matrix']
    support = metrics['support']
    if (len(matrix) != 4 or any(len(row) != 4 for row in matrix)
            or any(type(n) is not int or n < 0 for row in matrix for n in row)
            or [sum(row) for row in matrix] != support or any(n <= 0 for n in support)):
        raise ValueError('Invalid four-grade aggregate evidence')
    n = sum(support)
    columns = [sum(row[i] for row in matrix) for i in range(4)]
    recalls = [matrix[i][i] / support[i] for i in range(4)]
    f1 = [2 * matrix[i][i] / (support[i] + columns[i]) for i in range(4)]
    return {'name': name, 'n': n, 'support': support,
            'accuracy': sum(matrix[i][i] for i in range(4)) / n,
            'macro_f1': sum(f1) / 4, 'balanced_accuracy': sum(recalls) / 4,
            'recall': recalls, 'correct_per_grade': [matrix[i][i] for i in range(4)]}


def load_evidence(root=DOCS):
    saved = {}
    for name, digest in SOURCES.items():
        path = Path(root) / name
        if path.is_symlink() or path.stat().st_size > 1024**2:
            raise ValueError('Unsafe evidence file')
        payload = path.read_bytes()
        if sha256(payload).hexdigest() != digest:
            raise ValueError('Aggregate evidence SHA mismatch')
        saved[name] = json.loads(payload)
    historical = card('ResNet last-bottleneck v3', saved['vision_grade2_v2_v3_diagnostic_v1.json']['overall']['v3'])
    resnet = saved['vision_frozen_feature_signal_results_v1.json']['metrics']
    efficient = saved['vision_efficientnet_probe_results_v1.json']['metrics']
    unweighted = saved['vision_efficientnet_head_results_v1.json']['metrics']
    nested = saved['vision_nested_feature_probe_results_v1.json']['metrics']
    model_comparison = saved['vision_photo_model_comparison_v1.json']
    if (model_comparison.get('status') != 'verified_680_image_oof_comparison'
            or [row.get('support') for row in model_comparison.get('rows', [])]
            != [[12, 84, 223, 361]] * 4):
        raise ValueError('Saved photo-model comparison population mismatch')
    probes = [card('ResNet + balanced head', resnet['linear']),
              card('EfficientNet + balanced head', efficient['efficientnet']),
              card('EfficientNet + unweighted head', unweighted['unweighted']),
              card('EfficientNet + nested-selected head', nested['linear']),
              card('Training majority baseline', resnet['majority'])]
    if historical['n'] != 53 or any(row['n'] != 680 or row['support'] != [12, 84, 223, 361] for row in probes):
        raise ValueError('Evidence population mismatch')
    return {'notice': 'Provisional labels; non-clinical; non-final; participant independence unverified.',
            'historical_validation53': historical, 'training680_oof': probes,
            'photo_model_comparison_680': model_comparison,
            'comparability': 'Different evaluation populations: do not rank the historical 53-Validation pilot against Training680 OOF.',
            'limitations': ['MGI0 has no whole-image support; definitions remain 0–4.',
                'All measured learned OOF workflows have Grade1 recall 0/12; Grade1 support is insufficient.',
                'Three fixed configurations plus one nested six-setting workflow reused development data; earlier selection optimism remains.',
                'Known content groups do not establish participant independence.',
                '181 development holds remain excluded; labels and final research manifest are unapproved.'],
            'final_model_selected': False, 'test_used': False, 'new_photo_runtime_activated': False}
