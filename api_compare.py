#!/usr/bin/env python3
"""
API: Compare QC Sessions
Confronta multiple sessioni QC per analisi trend
"""

import sys
import json
from qc_database import QCDatabase
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
import base64


def generate_comparison_chart(sessions_data, metric='cv_mean', modality='pt'):
    """
    Genera grafico comparativo
    
    Args:
        sessions_data: lista sessioni con metriche
        metric: metrica da comparare
        modality: 'pt' o 'ct'
        
    Returns:
        base64 encoded PNG
    """
    fig, ax = plt.subplots(figsize=(12, 6), dpi=150)
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#16213e')
    
    # Estrai dati
    timestamps = []
    values = []
    colors = []
    
    for session in sessions_data:
        metrics_key = f'{modality}_metrics'
        if metrics_key in session and session[metrics_key]:
            timestamps.append(session['timestamp'][:16])
            values.append(session[metrics_key].get(metric, 0))
            
            # Colore in base a PASS/FAIL
            is_pass = session[metrics_key].get('overall_pass', False)
            colors.append('#4CAF50' if is_pass else '#F44336')
    
    # Plot
    x = np.arange(len(timestamps))
    bars = ax.bar(x, values, color=colors, alpha=0.8, edgecolor='white', linewidth=1.5)
    
    # Etichette
    ax.set_xlabel('Sessione QC', fontsize=12, color='white')
    ax.set_ylabel(metric.replace('_', ' ').title(), fontsize=12, color='white')
    ax.set_title(f'Comparazione {metric} - {modality.upper()}', 
                 fontsize=14, color='#4FC3F7', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(timestamps, rotation=45, ha='right', fontsize=9)
    ax.tick_params(colors='white')
    
    # Griglia
    ax.grid(True, alpha=0.3, linestyle='--', color='#4FC3F7')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#4FC3F7')
    ax.spines['bottom'].set_color('#4FC3F7')
    
    # Legenda
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#4CAF50', label='PASS'),
        Patch(facecolor='#F44336', label='FAIL')
    ]
    ax.legend(handles=legend_elements, loc='upper right', 
             facecolor='#1a1a2e', edgecolor='#4FC3F7')
    
    plt.tight_layout()
    
    # Converti a base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', facecolor='#1a1a2e', edgecolor='none')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    return f"data:image/png;base64,{img_base64}"


def compare_sessions(session_ids):
    """
    Confronta multiple sessioni QC
    
    Args:
        session_ids: lista ID sessioni da comparare
        
    Returns:
        dict con dati comparativi
    """
    db = QCDatabase()
    
    # Recupera dati sessioni
    sessions = []
    for sid in session_ids:
        session = db.get_session_details(sid)
        if session:
            sessions.append(session)
    
    if len(sessions) < 2:
        raise ValueError("Servono almeno 2 sessioni per comparazione")
    
    # Genera grafici comparativi
    charts = {
        'pt_cv_mean': generate_comparison_chart(sessions, 'cv_mean', 'pt'),
        'pt_nu_max': generate_comparison_chart(sessions, 'nu_max_mean', 'pt'),
        'ct_cv_mean': generate_comparison_chart(sessions, 'cv_mean', 'ct'),
        'ct_nu_max': generate_comparison_chart(sessions, 'nu_max_mean', 'ct')
    }
    
    # Tabella comparativa
    comparison_table = []
    for session in sessions:
        pt_metrics = session.get('pt_metrics', {})
        ct_metrics = session.get('ct_metrics', {})
        
        comparison_table.append({
            'id': session['id'],
            'timestamp': session['timestamp'],
            'scanner': session['scanner_name'],
            'pt_cv_mean': pt_metrics.get('cv_mean', 0) if pt_metrics else 0,
            'pt_nu_max': pt_metrics.get('nu_max_mean', 0) if pt_metrics else 0,
            'pt_pass': pt_metrics.get('overall_pass', False) if pt_metrics else False,
            'ct_cv_mean': ct_metrics.get('cv_mean', 0) if ct_metrics else 0,
            'ct_nu_max': ct_metrics.get('nu_max_mean', 0) if ct_metrics else 0,
            'ct_pass': ct_metrics.get('overall_pass', False) if ct_metrics else False,
            'html_url': session['report_html_path'],
            'json_url': session['report_json_path']
        })
    
    # Calcola statistiche comparative
    pt_cv_values = [row['pt_cv_mean'] for row in comparison_table]
    ct_cv_values = [row['ct_cv_mean'] for row in comparison_table]
    
    statistics = {
        'sessions_count': len(sessions),
        'pt_cv_trend': 'stable' if np.std(pt_cv_values) < 1.0 else 'variable',
        'ct_cv_trend': 'stable' if np.std(ct_cv_values) < 1.0 else 'variable',
        'pt_pass_rate': sum(1 for row in comparison_table if row['pt_pass']) / len(comparison_table) * 100,
        'ct_pass_rate': sum(1 for row in comparison_table if row['ct_pass']) / len(comparison_table) * 100
    }
    
    return {
        'success': True,
        'sessions': sessions,
        'comparison_table': comparison_table,
        'charts': charts,
        'statistics': statistics
    }


def main():
    """Main entry point"""
    try:
        if len(sys.argv) < 2:
            raise ValueError("Usage: api_compare.py <session_id_1> <session_id_2> [session_id_3...]")
        
        # Parse session IDs
        session_ids = [int(sid) for sid in sys.argv[1:]]
        
        # Compare sessions
        result = compare_sessions(session_ids)
        
        print(json.dumps(result), flush=True)
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
