#!/usr/bin/env python3
"""
API: Import IQCheck JSON
Valida e processa il file JSON prodotto dall'IQCheck del sistema CT.

Struttura JSON attesa:
{
  "date": "2026-04-08T15:59",
  "head": { "ct": -1.6, "uniformity": -1.2, "noise": 2.6, "low": 3.7 },
  "body": { "ct": 109.3, "uniformity": 1.4, "noise": 9.2 }
}

Limiti ricavati da iq_check.html (JavaScript):
  head → ct:[-4,4]  uniformity:[-4,4]  noise:[2.3,3.1]  low:[3,5]
  body → ct:[101,113]  uniformity:[-8,8]  noise:[7.9,10.7]
"""

import sys
import json
from datetime import datetime
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ============================================================================
# LIMITI DI ACCETTABILITÀ (modificabili senza toccare la logica)
# ============================================================================

IQCHECK_LIMITS = {
    'head': {
        'ct':         ( -4.0,   4.0),   # HU
        'uniformity': ( -4.0,   4.0),   # %
        'noise':      (  2.3,   3.1),   # %  (range atteso, non solo upper)
        'low':        (  3.0,   5.0),   # %
    },
    'body': {
        'ct':         (101.0, 113.0),   # HU assoluto (fantoccio body, non acqua)
        'uniformity': ( -8.0,   8.0),   # %
        'noise':      (  7.9,  10.7),   # %  (range atteso, non solo upper)
    }
}

# Unità di misura per display nel report
IQCHECK_UNITS = {
    'ct': 'HU',
    'uniformity': '%',
    'noise': '%',
    'low': '%',
}

# Etichette leggibili
IQCHECK_LABELS = {
    'ct': 'CT Number',
    'uniformity': 'Uniformità',
    'noise': 'Rumore',
    'low': 'Basso Contrasto',
}


# ============================================================================
# LOGICA DI VALUTAZIONE
# ============================================================================

def evaluate_value(value, limits):
    """
    Logica identica a iq_check.html:
        if val >= min && val <= max → PASS, altrimenti FAIL.
    Non esiste stato intermedio.
    """
    lo, hi = limits
    return 'pass' if lo <= value <= hi else 'fail'


def process_iqcheck(data):
    """
    Valida la struttura del JSON IQCheck e arricchisce ogni campo
    con la valutazione pass/fail (identica a iq_check.html).

    Args:
        data: dict raw dal file JSON

    Returns:
        dict con campi originali + 'evaluations', 'overall_pass', 'limits'
    """
    required_head = ['ct', 'uniformity', 'noise', 'low']
    required_body = ['ct', 'uniformity', 'noise']

    if 'head' not in data:
        raise ValueError("Campo 'head' mancante nel JSON IQCheck")
    if 'body' not in data:
        raise ValueError("Campo 'body' mancante nel JSON IQCheck")

    for field in required_head:
        if field not in data['head']:
            raise ValueError(f"Campo 'head.{field}' mancante")
    for field in required_body:
        if field not in data['body']:
            raise ValueError(f"Campo 'body.{field}' mancante")

    # Aggiungi timestamp se assente
    if 'date' not in data:
        data['date'] = datetime.now().isoformat()[:16]

    # Valutazione per ogni campo
    evaluations = {'head': {}, 'body': {}}
    all_results = []

    for field in required_head:
        ev = evaluate_value(data['head'][field], IQCHECK_LIMITS['head'][field])
        evaluations['head'][field] = ev
        all_results.append(ev)

    for field in required_body:
        ev = evaluate_value(data['body'][field], IQCHECK_LIMITS['body'][field])
        evaluations['body'][field] = ev
        all_results.append(ev)

    overall_pass = all(r == 'pass' for r in all_results)

    return {
        **data,
        'evaluations': evaluations,
        'overall_pass': overall_pass,
        'limits': IQCHECK_LIMITS,
        'units': IQCHECK_UNITS,
        'labels': IQCHECK_LABELS,
    }


# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    try:
        if len(sys.argv) < 2:
            raise ValueError("Usage: api_iqcheck.py <json_file_path>")

        json_path = sys.argv[1]
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        result = process_iqcheck(data)
        print(json.dumps({'success': True, 'iqcheck': result}), flush=True)

    except Exception as e:
        print(json.dumps({'success': False, 'error': str(e)}), flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
