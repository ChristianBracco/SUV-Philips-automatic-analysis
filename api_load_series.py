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


def load_series(folder_path, series_uid, lut_name='Rainbow2'):
    """Carica serie DICOM e converti in base64"""
    try:
        print(f"[DEBUG] Starting load_series for {series_uid} with LUT={lut_name}", flush=True)
        
        # Trova tutti i file DICOM
        dicom_files = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith('.dcm'):
                    dicom_files.append(os.path.join(root, file))
        
        print(f"[DEBUG] Found {len(dicom_files)} DICOM files total", flush=True)
        
        # Filtra per serie richiesta
        series_files = []
        for filepath in dicom_files:
            try:
                ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                # FIX: strip whitespace da UID per match corretto
                file_uid = str(ds.SeriesInstanceUID).strip() if hasattr(ds, 'SeriesInstanceUID') else None
                if file_uid and file_uid == series_uid.strip():
                    instance_number = int(ds.InstanceNumber) if hasattr(ds, 'InstanceNumber') else 0
                    series_files.append({
                        'filepath': filepath,
                        'instance_number': instance_number
                    })
            except Exception as e:
                print(f"[DEBUG] Skipping {filepath}: {e}", flush=True)
                continue
        
        print(f"[DEBUG] Found {len(series_files)} files for series {series_uid}", flush=True)
        
        if not series_files:
            raise ValueError(f"Nessun file trovato per serie {series_uid}")
        
        # Ordina per instance number
        series_files.sort(key=lambda x: x['instance_number'])
        
        images_b64 = []
        
        for idx, file_info in enumerate(series_files):
            filename = os.path.basename(file_info['filepath'])
            print(f"[{idx+1}/{len(series_files)}] {filename}", flush=True)
            
            try:
                # Leggi DICOM completo
                ds = pydicom.dcmread(file_info['filepath'])
                img = ds.pixel_array
                
                print(f"  Shape: {img.shape}, dtype: {img.dtype}", flush=True)
                
                # SKIPPA immagini massive
                if img.shape[0] > 8192 or img.shape[1] > 8192:
                    print(f"  SKIPPED: too large", flush=True)
                    continue
                
                # Ridimensiona se necessario
                MAX_DIM = 1024
                if img.shape[0] > MAX_DIM or img.shape[1] > MAX_DIM:
                    scale = min(MAX_DIM / img.shape[0], MAX_DIM / img.shape[1])
                    new_width = int(img.shape[1] * scale)
                    new_height = int(img.shape[0] * scale)
                    img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    print(f"  Resized to: {img.shape}", flush=True)
                
                # Normalizza a uint8
                if img.dtype != np.uint8:
                    img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                
                # Applica LUT selezionata per PET
                modality = ds.Modality if hasattr(ds, 'Modality') else 'UN'
                
                if modality == 'PT':
                    # Carica LUT selezionata (path relativo)
                    lut_path = os.path.join('luts', f'{lut_name}.cm')
                    
                    if os.path.exists(lut_path):
                        try:
                            with open(lut_path, 'r') as f:
                                lut_colors = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                            
                            # Crea lookup table 256 RGB
                            lut_table = np.zeros((256, 3), dtype=np.uint8)
                            for i in range(256):
                                # Mappa valore pixel (0-255) a colore LUT
                                idx = min(int(i * (len(lut_colors) - 1) / 255.0), len(lut_colors) - 1)
                                hex_color = lut_colors[idx].lstrip('#')
                                lut_table[i, 0] = int(hex_color[0:2], 16)  # R
                                lut_table[i, 1] = int(hex_color[2:4], 16)  # G
                                lut_table[i, 2] = int(hex_color[4:6], 16)  # B
                            
                            # Applica LUT usando indexing NumPy
                            img_rgb = lut_table[img]
                        except Exception as e:
                            print(f"  LUT error: {e}, using JET fallback", flush=True)
                            img_rgb = cv2.applyColorMap(img, cv2.COLORMAP_JET)
                    else:
                        # Fallback: COLORMAP_JET
                        print(f"  LUT {lut_name} not found, using JET", flush=True)
                        img_rgb = cv2.applyColorMap(img, cv2.COLORMAP_JET)
                else:
                    # CT: converti a grayscale RGB
                    if len(img.shape) == 2:
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                    else:
                        img_rgb = img
                
                # Encode JPEG
                _, buffer = cv2.imencode('.jpg', img_rgb, [cv2.IMWRITE_JPEG_QUALITY, 90])
                img_b64 = base64.b64encode(buffer).decode('utf-8')
                data_url = f"data:image/jpeg;base64,{img_b64}"
                
                # Ritorna solo immagine (backward compatible)
                images_b64.append(data_url)
                print(f"  OK", flush=True)
                    
            except Exception as e:
                print(f"  ERROR: {e}", flush=True)
                continue
        
        result = {
            'success': True,
            'images': images_b64,
            'count': len(images_b64)
        }
        
        print(json.dumps(result), flush=True)
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), flush=True)
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Missing arguments: folder_path series_uid [lut_name]'}))
        sys.exit(1)
    
    folder_path = sys.argv[1]
    series_uid = sys.argv[2]
    lut_name = sys.argv[3] if len(sys.argv) > 3 else 'Rainbow2'
    
    load_series(folder_path, series_uid, lut_name)
