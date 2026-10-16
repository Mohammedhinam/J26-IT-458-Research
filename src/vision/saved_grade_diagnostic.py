"""Descriptive saved-OOF analysis only; no model, image, threshold or label change."""
import csv
import json
from pathlib import Path

import numpy as np

from . import frozen_feature_probe as base

CONFIDENCE_BINS = [0., .2, .4, .6, .8, 1.]


def load_oof(path, expected_sha, probability_key):
    path = Path(path)
    if path.is_symlink() or path.stat().st_size > 16 * 1024**2 or base.legacy.sha256(path) != expected_sha:
        raise ValueError('Untrusted saved OOF')
    with np.load(path, allow_pickle=False) as saved:
        return {'ids': saved['ids'], 'labels': saved['labels'], 'folds': saved['folds'],
                'probabilities': saved[probability_key]}


def analyze(models):
    """All models must describe identical immutable records, labels and folds."""
    if not models:
        raise ValueError('Saved models required')
    first = next(iter(models.values()))
    ids = first['ids']
    labels = base.pilot.checked_grades(first['labels'])
    if len(ids) != len(labels) or len(set(ids)) != len(ids):
        raise ValueError('Unique aligned IDs required')
    result, cases = {}, []
    for name, saved in models.items():
        for key in ['ids', 'labels', 'folds']:
            if not np.array_equal(saved[key], first[key]):
                raise ValueError('Saved-model membership/labels/folds differ')
        probabilities = np.asarray(saved['probabilities'], dtype=float)
        metrics = base.measure(labels, probabilities)
        ranking = np.argsort(-probabilities, axis=1, kind='stable')
        predicted = ranking[:, 0] + 1
        confidence = probabilities.max(axis=1)
        correct = predicted == labels
        true_probability = probabilities[np.arange(len(labels)), labels - 1]
        other = probabilities.copy()
        other[np.arange(len(labels)), labels - 1] = -np.inf
        best_other = other.max(axis=1)
        grades = {}
        for grade in [1, 2, 3, 4]:
            selected = labels == grade
            support = int(selected.sum())
            ranks = np.argmax(ranking[selected] == grade - 1, axis=1) + 1
            grades[str(grade)] = {
                'support': support, 'correct': int(correct[selected].sum()),
                'predicted_grade_counts': np.bincount(predicted[selected], minlength=5)[1:].tolist(),
                'true_grade_rank_counts_1to4': np.bincount(ranks, minlength=5)[1:].tolist(),
                'top2_correct': int(np.sum(ranks <= 2)),
                'mean_true_probability': float(true_probability[selected].mean()) if support else None,
                'mean_true_minus_best_other': float((true_probability - best_other)[selected].mean()) if support else None}
        reliability = []
        for low, high in zip(CONFIDENCE_BINS[:-1], CONFIDENCE_BINS[1:]):
            selected = (confidence >= low) & ((confidence <= high) if high == 1. else (confidence < high))
            n = int(selected.sum())
            reliability.append({'lower': low, 'upper': high, 'n': n,
                'mean_probability': float(confidence[selected].mean()) if n else None,
                'accuracy': float(correct[selected].mean()) if n else None})
        result[name] = {'metrics': metrics, 'grades': grades, 'reliability_bins': reliability,
            'mean_max_probability': float(confidence.mean()),
            'mean_max_probability_when_wrong': float(confidence[~correct].mean()) if (~correct).any() else None,
            'wrong_probability_ge_0_8': int(np.sum((~correct) & (confidence >= .8))),
            'wrong_probability_ge_0_9': int(np.sum((~correct) & (confidence >= .9))),
            'zero_probability_entries': int(np.sum(probabilities == 0))}
        for index in np.flatnonzero(np.isin(labels, [1, 2])):
            top = ranking[index, :2]
            cases.append({'record_id': str(ids[index]), 'provisional_grade': int(labels[index]),
                'model': name, 'predicted_grade': int(predicted[index]),
                'true_grade_probability': float(true_probability[index]),
                'top1_grade': int(top[0] + 1), 'top1_probability': float(probabilities[index, top[0]]),
                'top2_grade': int(top[1] + 1), 'top2_probability': float(probabilities[index, top[1]]),
                'winning_margin': float(probabilities[index, top[0]] - probabilities[index, top[1]]),
                'true_minus_best_other': float(true_probability[index] - best_other[index]),
                'true_grade_rank': int(np.flatnonzero(ranking[index] == labels[index] - 1)[0] + 1)})
    return {'scope': 'saved predictions only; fixed bins diagnostic, no selected operating threshold',
            'n': len(labels), 'support': np.bincount(labels, minlength=5)[1:].tolist(),
            'models': result, 'case_rows': cases, 'labels_changed': False, 'model_fits': 0}


def write_cases(path, rows):
    """Record-level evidence belongs in ignored local storage, never public docs."""
    path = Path(path)
    if path.exists() or not rows:
        raise ValueError('Fresh nonempty case output required')
    with path.open('x', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
