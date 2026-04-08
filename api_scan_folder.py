#!/usr/bin/env python3
"""
API: Scan DICOM Folder
Scansiona cartella e raggruppa per serie
"""

import sys
import json
import os
import pydicom
from pathlib import Path
from collections import defaultdict


def scan_folder(folder_path):
    """Scansiona cartella DICOM e raggruppa per serie"""
    try:
        if not os.path.exists(folder_path):
            raise ValueError(f"Cartella non trovata: {folder_path}")
        
        # Trova tutti i file DICOM
        dicom_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.dcm'):
                    dicom_files.append(os.path.join(root, file))
        
        if not dicom_files:
            raise ValueError("Nessun file DICOM trovato")
        
        # Raggruppa per SeriesInstanceUID
        series_groups = defaultdict(list)
        
        for filepath in dicom_files:
            try:
                ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                
                series_uid = ds.SeriesInstanceUID if hasattr(ds, 'SeriesInstanceUID') else 'unknown'
                series_desc = ds.SeriesDescription if hasattr(ds, 'SeriesDescription') else 'Unknown Series'
                modality = ds.Modality if hasattr(ds, 'Modality') else 'Unknown'
                instance_number = int(ds.InstanceNumber) if hasattr(ds, 'InstanceNumber') else 0
                
                series_groups[series_uid].append({
                    'filepath': filepath,
                    'series_desc': series_desc,
                    'modality': modality,
                    'instance_number': instance_number,
                    'filename': os.path.basename(filepath)
                })
                
            except Exception as e:
                # Skip file non validi
                continue
        
        # Prepara output
        series_list = []
        for series_uid, file_list in series_groups.items():
            # Ordina per instance number
            file_list.sort(key=lambda x: x['instance_number'])
            
            series_list.append({
                'uid': series_uid,
                'description': file_list[0]['series_desc'],
                'modality': file_list[0]['modality'],
                'count': len(file_list)
            })
        
        result = {
            'success': True,
            'series': series_list,
            'totalFiles': len(dicom_files)
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
        print(json.dumps({'error': 'Missing folder path argument'}))
        sys.exit(1)
    
    folder_path = sys.argv[1]
    scan_folder(folder_path)
