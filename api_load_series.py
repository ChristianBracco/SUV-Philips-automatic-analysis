#!/usr/bin/env python3
"""
API: Load DICOM Series
Carica serie e converti immagini in base64
"""

import sys
import json
import base64
import cv2
import numpy as np
import pydicom
import os
from collections import defaultdict


def load_series(folder_path, series_uid):
    """Carica serie DICOM e converti in base64"""
    try:
        # Trova tutti i file DICOM
        dicom_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.dcm'):
                    dicom_files.append(os.path.join(root, file))
        
        # Filtra per serie richiesta
        series_files = []
        for filepath in dicom_files:
            try:
                ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                if hasattr(ds, 'SeriesInstanceUID') and ds.SeriesInstanceUID == series_uid:
                    instance_number = int(ds.InstanceNumber) if hasattr(ds, 'InstanceNumber') else 0
                    series_files.append({
                        'filepath': filepath,
                        'instance_number': instance_number
                    })
            except:
                continue
        
        if not series_files:
            raise ValueError(f"Nessun file trovato per serie {series_uid}")
        
        # Ordina per instance number
        series_files.sort(key=lambda x: x['instance_number'])
        
        images_b64 = []
        
        for file_info in series_files:
            # Leggi DICOM completo
            ds = pydicom.dcmread(file_info['filepath'])
            img = ds.pixel_array
            
            # Normalizza a uint8
            if img.dtype != np.uint8:
                img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
                img = img_norm.astype(np.uint8)
            
            # Converti a RGB
            if len(img.shape) == 2:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            else:
                img_rgb = img
            
            # Encode base64
            _, buffer = cv2.imencode('.png', img_rgb)
            img_b64 = base64.b64encode(buffer).decode('utf-8')
            data_url = f"data:image/png;base64,{img_b64}"
            
            images_b64.append(data_url)
        
        result = {
            'success': True,
            'images': images_b64,
            'count': len(images_b64)
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Missing arguments: folder_path series_uid'}))
        sys.exit(1)
    
    folder_path = sys.argv[1]
    series_uid = sys.argv[2]
    
    load_series(folder_path, series_uid)
