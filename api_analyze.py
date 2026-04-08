#!/usr/bin/env python3
"""
API: Run SUV Analysis
Esegue analisi completa e genera report
Supporta array di cartelle per analisi multi-serie
"""

import sys
import json
from suv_analyzer import SUVAnalyzer
from suv_report_generator import HTMLReportGenerator
from nema_analysis import NEMAAnalysis, calculate_nema_statistics


def run_analysis(folder_paths):
    """Esegue analisi SUV completa su array di cartelle"""
    try:
        # Analyzer unico per tutte le cartelle
        analyzer = SUVAnalyzer()
        
        # Processa ogni cartella
        for folder_path in folder_paths:
            analyzer.process_folder(folder_path)
        
        # NEMA analysis
        nema_results = {}
        
        if analyzer.pt_data:
            nema_pet = NEMAAnalysis(analyzer.pt_data, modality='PT', grid_size=15)
            slice_data, plot_combined, plot_example = nema_pet.analyze_pet_grid()
            stats = calculate_nema_statistics(slice_data, analyzer.config)
            
            nema_results['pet'] = {
                'slice_data': slice_data,
                'plot_combined': plot_combined,
                'plot_example': plot_example,
                'statistics': stats
            }
        
        if analyzer.ct_data:
            nema_ct = NEMAAnalysis(analyzer.ct_data, modality='CT')
            slice_data, plot_combined, plot_example = nema_ct.analyze_ct_circles()
            stats = calculate_nema_statistics(slice_data, analyzer.config)
            
            nema_results['ct'] = {
                'slice_data': slice_data,
                'plot_combined': plot_combined,
                'plot_example': plot_example,
                'statistics': stats
            }
        
        # Generate report
        report_gen = HTMLReportGenerator(analyzer, nema_results)
        html_report = report_gen.generate()
        
        result = {
            'success': True,
            'reportHtml': html_report,
            'stats': {
                'ptSlices': len(analyzer.pt_data) if analyzer.pt_data else 0,
                'ctSlices': len(analyzer.ct_data) if analyzer.ct_data else 0,
                'foldersProcessed': len(folder_paths)
            }
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'Missing folder path arguments'}))
        sys.exit(1)
    
    # Tutti gli argomenti dopo lo script sono folder paths
    folder_paths = sys.argv[1:]
    run_analysis(folder_paths)
