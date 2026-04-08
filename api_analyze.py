#!/usr/bin/env python3
"""
API: Analyze DICOM series
Esegue analisi SUV solo sulle serie selezionate
"""

import sys
import json
from pathlib import Path
import pydicom

# Import SUV analyzer
from suv_analyzer import SUVAnalyzer

def main():
    """Main analysis function"""
    try:
        # Parse arguments
        if len(sys.argv) < 2:
            raise ValueError("Missing folder_path argument")
        
        folder_path = sys.argv[1]
        
        # Check for selected series UIDs (optional)
        selected_series = []
        if len(sys.argv) > 2:
            # Additional args are selected series UIDs
            selected_series = sys.argv[2:]
        
        print(f"Analyzing folder: {folder_path}", flush=True)
        if selected_series:
            print(f"Selected series: {len(selected_series)}", flush=True)
        
        # Filter DICOM files if series selected
        if selected_series:
            # Find only files from selected series
            all_files = list(Path(folder_path).glob('*.dcm'))
            filtered_files = []
            
            for filepath in all_files:
                try:
                    ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                    if hasattr(ds, 'SeriesInstanceUID') and ds.SeriesInstanceUID in selected_series:
                        filtered_files.append(filepath)
                except:
                    continue
            
            print(f"Found {len(all_files)} total files, {len(filtered_files)} in selected series", flush=True)
            
            # Create temp folder with filtered files
            # For now, we'll just modify process_folder to skip non-selected files
            # This is a quick hack - in production we'd copy files to temp folder
        
        # Create analyzer
        analyzer = SUVAnalyzer()
        
        # Pass selected series to analyzer
        analyzer.selected_series = set(selected_series) if selected_series else None
        
        # Process folder
        analyzer.process_folder(folder_path)
        
        # Generate report
        report_html = analyzer.generate_html_report()
        
        # Return results
        result = {
            'success': True,
            'reportHtml': report_html,
            'ptCount': len(analyzer.pt_data),
            'ctCount': len(analyzer.ct_data)
        }
        
        print(json.dumps(result), flush=True)
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), flush=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
