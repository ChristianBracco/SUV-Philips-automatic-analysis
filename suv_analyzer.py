#!/usr/bin/env python3
"""
SUV Analyzer - Sistema completo per analisi quantitativa PET/CT
Genera report HTML interattivi con grafici, statistiche e analisi di qualità

Autore: Christian Bracco - S.C. Interaziendale di Fisica Sanitaria
"""

import os
import sys
import json
import base64
from datetime import datetime
from pathlib import Path
import argparse
from io import BytesIO

import numpy as np
import pydicom
from PIL import Image
import cv2


class SUVAnalyzer:
    """Analizzatore SUV per PET/CT con supporto multi-modalità"""
    
    def __init__(self):
        self.pt_data = []
        self.ct_data = []
        self.secondary_captures = []
        self.config = self._load_default_config()
        
    def _load_default_config(self):
        """Configurazione di default per analisi"""
        return {
            "roi_fraction": 0.80,  # Frazione area ROI (80%)
            "suv_tolerance_upper": 1.10,  # SUV tolerance +10%
            "suv_tolerance_lower": 0.90,  # SUV tolerance -10%
            "nu_pet_upper": 15.0,  # Non-uniformity PET max %
            "nu_pet_lower": -15.0,  # Non-uniformity PET min %
            "nu_ct_upper": 15.0,  # Non-uniformity CT max %
            "nu_ct_lower": -15.0,  # Non-uniformity CT min %
            "cv_ct_upper": 15.0,  # Coefficient of variation CT max %
            "grid_size": 15,  # Griglia 15x15 per PET
            "example_slice_pt": 15,  # Slice esempio PET
            "example_slice_ct": 15,  # Slice esempio CT
            "specialist": "Dr. Christian Bracco",
            "department": "S.C. Interaziendale di Fisica Sanitaria",
            "institution": "A.O. Ordine Mauriziano - ASL TO3"
        }
    
    def load_config_file(self, config_path):
        """Carica configurazione da file di testo"""
        if not os.path.exists(config_path):
            return
            
        with open(config_path, 'r') as f:
            for line in f:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                    # Mappa chiavi italiane
                    key_map = {
                        "Frazione area ROI": "roi_fraction",
                        "Limite superiore tolleranza SUV": "suv_tolerance_upper",
                        "Limite inferiore tolleranza SUV": "suv_tolerance_lower",
                        "Limite superiore NU PET": "nu_pet_upper",
                        "Limite inferiore NU PET": "nu_pet_lower",
                        "Limite superiore NU CT": "nu_ct_upper",
                        "Limite inferiore NU CT": "nu_ct_lower",
                        "Limite superiore CV CT": "cv_ct_upper",
                        "Specialista fisica medica": "specialist"
                    }
                    if key in key_map:
                        self.config[key_map[key]] = value
    
    def read_dicom_file(self, filepath):
        """Legge file DICOM e determina il tipo"""
        try:
            ds = pydicom.dcmread(filepath)
            
            # IMPORTANTE: Controlla PRIMA la modalità
            modality = ds.Modality if hasattr(ds, 'Modality') else None
            
            # Secondary capture SOLO se non è PET/CT
            # (alcuni CT Philips hanno ImageType='SECONDARY' ma sono comunque CT!)
            is_secondary = False
            if modality not in ['PT', 'CT']:
                is_secondary = "SECONDARY" in str(ds.ImageType) if hasattr(ds, 'ImageType') else False
            
            info = {
                'filepath': filepath,
                'modality': modality,
                'is_secondary': is_secondary,
                'manufacturer': ds.Manufacturer if hasattr(ds, 'Manufacturer') else 'Unknown',
                'model': ds.ManufacturerModelName if hasattr(ds, 'ManufacturerModelName') else 'Unknown',
                'patient_id': ds.PatientID if hasattr(ds, 'PatientID') else 'Unknown',
                'study_date': ds.StudyDate if hasattr(ds, 'StudyDate') else 'Unknown',
                'series_time': ds.SeriesTime if hasattr(ds, 'SeriesTime') else 'Unknown',
                'instance_number': int(ds.InstanceNumber) if hasattr(ds, 'InstanceNumber') else 0,
                'dicom': ds
            }
            
            return info
            
        except Exception as e:
            print(f"Errore lettura DICOM {filepath}: {e}")
            return None
    
    @staticmethod
    def convert_to_uint8(img):
        if img.dtype == np.uint16:
            img = (img / img.max() * 255).astype(np.uint8)
        elif img.dtype != np.uint8:
            img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return img    
    
    
    
    def process_secondary_capture(self, dicom_info):
        """Processa DICOM secondary capture (screenshot con valori SUV)"""
        ds = dicom_info['dicom']
        
        try:
            # Estrai pixel array
            img = ds.pixel_array
            
            # Gestione shape anomale - skippa PRIMA di processare
            # Casi: (1,1,3), (2,2), o qualsiasi dimensione < 10px
            if len(img.shape) == 2:
                # Grayscale 2D
                if img.shape[0] < 10 or img.shape[1] < 10:
                    return None
            elif len(img.shape) == 3:
                # RGB o multi-channel
                if img.shape[0] < 10 or img.shape[1] < 10:
                    return None
            elif len(img.shape) == 4:
                # Multi-frame
                if img.shape[1] < 10 or img.shape[2] < 10:
                    return None
            
            # Se multi-frame, estrai info da ogni frame
            frames = []
            if len(img.shape) == 4:  # multi-frame
                num_frames = img.shape[0]
                for i in range(num_frames):
                    frame = img[i]

                    frame = self.convert_to_uint8(frame)

                    if len(frame.shape) == 2:
                        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

                    img_pil = Image.fromarray(frame)                          
                    buffered = BytesIO()
                    img_pil.save(buffered, format="PNG")
                    img_b64 = base64.b64encode(buffered.getvalue()).decode()
                    
                    frames.append({
                        'frame_number': i,
                        'image_b64': img_b64,
                        'shape': frame.shape
                    })
            else:
                # Singolo frame
                img = self.convert_to_uint8(img)
                
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                    
                img_pil = Image.fromarray(img)
                buffered = BytesIO()
                img_pil.save(buffered, format="PNG")
                img_b64 = base64.b64encode(buffered.getvalue()).decode()
                
                frames.append({
                    'frame_number': 0,
                    'image_b64': img_b64,
                    'shape': img.shape
                })
            
            result = {
                'type': 'secondary_capture',
                'patient_id': dicom_info['patient_id'],
                'study_date': dicom_info['study_date'],
                'manufacturer': dicom_info['manufacturer'],
                'model': dicom_info['model'],
                'num_frames': len(frames),
                'frames': frames
            }
            
            self.secondary_captures.append(result)
            return result
            
        except Exception as e:
            # Silenzia errori per SC anomale (già gestite sopra)
            # print(f"Errore processing secondary capture: {e}")
            return None
    
    def calculate_roi_circular(self, image, fraction=0.8):
        """Calcola ROI circolare su immagine"""
        # Normalizza e binarizza
        img_norm = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        img_blur = cv2.GaussianBlur(img_norm, (5, 5), 0)
        _, threshold = cv2.threshold(img_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Trova contorni
        contours, _ = cv2.findContours(threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Contorno più grande
        largest_contour = max(contours, key=cv2.contourArea)
        largest_area = cv2.contourArea(largest_contour)
        
        # Centro e raggio
        M = cv2.moments(largest_contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx = image.shape[1] // 2
            cy = image.shape[0] // 2
        
        # ROI ridotta per frazione
        new_area = largest_area * fraction
        new_radius = int(np.sqrt(new_area / np.pi))
        
        # Crea maschera circolare
        mask = np.zeros_like(img_norm, dtype=np.uint8)
        cv2.circle(mask, (cx, cy), new_radius, 255, thickness=-1)
        
        return {
            'center': (cx, cy),
            'radius': new_radius,
            'area': new_area,
            'mask': mask
        }
    
    def calculate_suv_from_dicom(self, dicom_info, roi_fraction=0.8):
        """Calcola SUV da DICOM PET originale"""
        ds = dicom_info['dicom']
        
        # Estrai pixel array
        img = ds.pixel_array
        
        # Cerca SUV scale factor (tag privato Philips)
        suv_scale_factor = 1.0
        try:
            if (0x7053, 0x1000) in ds:
                suv_scale_factor = float(ds[0x7053, 0x1000].value)
        except:
            # Calcola manualmente se necessario
            if hasattr(ds, 'RadiopharmaceuticalInformationSequence'):
                radio_info = ds.RadiopharmaceuticalInformationSequence[0]
                if hasattr(radio_info, 'RadionuclideTotalDose') and hasattr(ds, 'PatientWeight'):
                    dose = float(radio_info.RadionuclideTotalDose)  # Bq
                    weight = float(ds.PatientWeight) * 1000  # g
                    
                    # Calcola decay se disponibile
                    # SUV = (pixel_value * dose) / (injected_dose * weight)
                    # Per ora usa scale factor di default
                    pass
        
        # Calcola ROI
        roi_info = self.calculate_roi_circular(img, roi_fraction)
        if not roi_info:
            return None
        
        # Estrai pixel nella ROI
        roi_pixels = img[roi_info['mask'] == 255]
        suv_values = roi_pixels * suv_scale_factor
        
        result = {
            'modality': 'PT',
            'instance_number': dicom_info['instance_number'],
            'suv_scale_factor': suv_scale_factor,
            'suv_mean': float(np.mean(suv_values)),
            'suv_std': float(np.std(suv_values)),
            'suv_max': float(np.max(suv_values)),
            'suv_min': float(np.min(suv_values)),
            'roi_center': roi_info['center'],
            'roi_radius': roi_info['radius'],
            'roi_area': roi_info['area'],
            'image': img,  # Per analisi NEMA
            'roi_mask': roi_info['mask']
        }
        
        return result
    
    def calculate_hu_from_dicom(self, dicom_info, roi_fraction=0.8):
        """Calcola Hounsfield Units da DICOM CT"""
        ds = dicom_info['dicom']
        img = ds.pixel_array
        
        # Calcola ROI
        roi_info = self.calculate_roi_circular(img, roi_fraction)
        if not roi_info:
            return None
        
        # Estrai pixel nella ROI
        roi_pixels = img[roi_info['mask'] == 255]
        
        result = {
            'modality': 'CT',
            'instance_number': dicom_info['instance_number'],
            'hu_mean': float(np.mean(roi_pixels)),
            'hu_std': float(np.std(roi_pixels)),
            'hu_max': float(np.max(roi_pixels)),
            'hu_min': float(np.min(roi_pixels)),
            'roi_center': roi_info['center'],
            'roi_radius': roi_info['radius'],
            'roi_area': roi_info['area'],
            'image': img,  # Per analisi NEMA
            'roi_mask': roi_info['mask']
        }
        
        return result
    
    def process_folder(self, folder_path):
        """Processa cartella con file DICOM"""
        files = sorted(Path(folder_path).glob('*.dcm'))
        
        print(f"Trovati {len(files)} file DICOM in {folder_path}")
        
        for filepath in files:
            print(f"Processing: {filepath.name}")
            info = self.read_dicom_file(str(filepath))
            
            if not info:
                continue
            
            # Secondary capture
            if info['is_secondary']:
                self.process_secondary_capture(info)
                continue
            
            # DICOM originali
            if info['modality'] == 'PT':
                result = self.calculate_suv_from_dicom(info, self.config['roi_fraction'])
                if result:
                    self.pt_data.append(result)
                    
            elif info['modality'] == 'CT':
                result = self.calculate_hu_from_dicom(info, self.config['roi_fraction'])
                if result:
                    self.ct_data.append(result)
        
        # Ordina per instance number
        self.pt_data.sort(key=lambda x: x['instance_number'])
        self.ct_data.sort(key=lambda x: x['instance_number'])
        
        print(f"\nProcessati: {len(self.pt_data)} PET, {len(self.ct_data)} CT, {len(self.secondary_captures)} secondary captures")
    
    def process_single_dicom(self, filepath):
        """Processa singolo file DICOM"""
        info = self.read_dicom_file(filepath)
        if not info:
            return None
        
        if info['is_secondary']:
            return self.process_secondary_capture(info)
        elif info['modality'] == 'PT':
            result = self.calculate_suv_from_dicom(info, self.config['roi_fraction'])
            if result:
                self.pt_data.append(result)
            return result
        elif info['modality'] == 'CT':
            result = self.calculate_hu_from_dicom(info, self.config['roi_fraction'])
            if result:
                self.ct_data.append(result)
            return result
        
        return None
    
    def analyze_nema_uniformity(self, example_slice_pt=15, example_slice_ct=15):
        """
        Esegue analisi omogeneità NEMA 94 completa
        
        Returns:
            dict con risultati PET e CT
        """
        from nema_analysis import NEMAAnalysis, calculate_nema_statistics
        
        results = {}
        
        # Analisi PET con griglia 15x15
        if self.pt_data:
            print("Esecuzione analisi NEMA PET (griglia 15x15)...")
            nema_pt = NEMAAnalysis(self.pt_data, modality='PT', grid_size=15)
            pt_slice_data, pt_plot, pt_example = nema_pt.analyze_pet_grid(example_slice_pt)
            pt_stats = calculate_nema_statistics(pt_slice_data, self.config)
            
            results['pet'] = {
                'slice_data': pt_slice_data,
                'plot_combined': pt_plot,
                'plot_example': pt_example,
                'statistics': pt_stats
            }
        
        # Analisi CT con 5 cerchi
        if self.ct_data:
            print("Esecuzione analisi NEMA CT (5 cerchi concentrici)...")
            nema_ct = NEMAAnalysis(self.ct_data, modality='CT')
            ct_slice_data, ct_plot, ct_example = nema_ct.analyze_ct_circles(example_slice_ct)
            ct_stats = calculate_nema_statistics(ct_slice_data, self.config)
            
            results['ct'] = {
                'slice_data': ct_slice_data,
                'plot_combined': ct_plot,
                'plot_example': ct_example,
                'statistics': ct_stats
            }
        
        return results
    
    def generate_html_report(self, output_path='suv_report.html'):
        """Genera report HTML interattivo"""
        from suv_report_generator import HTMLReportGenerator
        
        # Esegui analisi NEMA
        print("\n📊 Esecuzione analisi NEMA...")
        nema_results = self.analyze_nema_uniformity(
            example_slice_pt=self.config.get('example_slice_pt', 15),
            example_slice_ct=self.config.get('example_slice_ct', 15)
        )
        
        generator = HTMLReportGenerator(self, nema_results)
        html_content = generator.generate()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nReport HTML generato: {output_path}")
        return output_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='SUV Analyzer - Analisi quantitativa PET/CT con report HTML'
    )
    parser.add_argument('input', help='File DICOM o cartella con file DICOM')
    parser.add_argument('-o', '--output', default='suv_report.html',
                       help='File output HTML (default: suv_report.html)')
    parser.add_argument('-c', '--config', help='File configurazione')
    
    args = parser.parse_args()
    
    # Crea analyzer
    analyzer = SUVAnalyzer()
    
    # Carica config se specificato
    if args.config:
        analyzer.load_config_file(args.config)
    
    # Processa input
    if os.path.isdir(args.input):
        analyzer.process_folder(args.input)
    elif os.path.isfile(args.input):
        analyzer.process_single_dicom(args.input)
    else:
        print(f"Errore: {args.input} non trovato")
        return 1
    
    # Genera report
    analyzer.generate_html_report(args.output)
    
    print("\n✅ Analisi completata!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
