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
        self.selected_series = None  # Set of selected series UIDs (None = all)
        self.secondary_captures = []
        self.config = self._load_default_config()
        self.acquisition_metadata = {}  # Metadata acquisizione DICOM
        
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
            "grid_size": 4,  # Griglia 4x4 per PET (era 15x15)
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
            
            # Secondary capture: controlla SOP Class UID E ImageType
            # SOP Class UID 1.2.840.10008.5.1.4.1.1.7 = Secondary Capture
            sop_class = ds.SOPClassUID if hasattr(ds, 'SOPClassUID') else None
            is_secondary = sop_class == '1.2.840.10008.5.1.4.1.1.7'
            
            # Fallback: controlla ImageType se SOP Class non è Secondary Capture
            if not is_secondary and modality not in ['PT', 'CT']:
                is_secondary = "SECONDARY" in str(ds.ImageType) if hasattr(ds, 'ImageType') else False
            
            info = {
                'filepath': filepath,
                'modality': modality,
                'is_secondary': is_secondary,
                'series_uid': str(ds.SeriesInstanceUID).strip() if hasattr(ds, 'SeriesInstanceUID') else None,
                'manufacturer': ds.Manufacturer if hasattr(ds, 'Manufacturer') else 'Unknown',
                'model': ds.ManufacturerModelName if hasattr(ds, 'ManufacturerModelName') else 'Unknown',
                'patient_id': ds.PatientID if hasattr(ds, 'PatientID') else 'Unknown',
                'study_date': ds.StudyDate if hasattr(ds, 'StudyDate') else 'Unknown',
                'study_time': ds.StudyTime if hasattr(ds, 'StudyTime') else 'Unknown',
                'series_time': ds.SeriesTime if hasattr(ds, 'SeriesTime') else 'Unknown',
                'institution_name': ds.InstitutionName if hasattr(ds, 'InstitutionName') else 'Unknown',
                'instance_number': int(ds.InstanceNumber) if hasattr(ds, 'InstanceNumber') else 0,
                'dicom': ds
            }
            
            # Estrai attività radioattiva se PET
            if modality == 'PT' and hasattr(ds, 'RadiopharmaceuticalInformationSequence'):
                try:
                    radiopharma_seq = ds.RadiopharmaceuticalInformationSequence[0]
                    if hasattr(radiopharma_seq, 'RadionuclideTotalDose'):
                        # Dose in Bq, converti in MBq
                        dose_bq = float(radiopharma_seq.RadionuclideTotalDose)
                        info['injected_activity_mbq'] = dose_bq / 1e6
                    else:
                        info['injected_activity_mbq'] = None
                except (IndexError, AttributeError):
                    info['injected_activity_mbq'] = None
            else:
                info['injected_activity_mbq'] = None
            
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
            # Casi: (1,1,3), (2,2), o qualsiasi dimensione < 10px O > 10000px
            if len(img.shape) == 2:
                # Grayscale 2D
                if img.shape[0] < 10 or img.shape[1] < 10:
                    return None
                if img.shape[0] > 10000 or img.shape[1] > 10000:
                    print(f"  Skipping massive SC image: {img.shape}")
                    return None
            elif len(img.shape) == 3:
                # RGB o multi-channel
                if img.shape[0] < 10 or img.shape[1] < 10:
                    return None
                if img.shape[0] > 10000 or img.shape[1] > 10000:
                    print(f"  Skipping massive SC image: {img.shape}")
                    return None
            elif len(img.shape) == 4:
                # Multi-frame
                if img.shape[1] < 10 or img.shape[2] < 10:
                    return None
                if img.shape[1] > 10000 or img.shape[2] > 10000:
                    print(f"  Skipping massive SC multi-frame: {img.shape}")
                    return None
            
            # Se multi-frame, estrai info da ogni frame
            frames = []
            if len(img.shape) == 4:  # multi-frame
                num_frames = img.shape[0]
                for i in range(num_frames):
                    try:
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
                    except Exception as e:
                        print(f"  Skipping frame {i}: {e}")
                        continue
            else:
                # Singolo frame
                try:
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
                except Exception as e:
                    print(f"  Skipping SC processing: {e}")
                    return None
            
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
            filename = filepath.name
            print(f"Processing: {filename}")
            
            try:
                info = self.read_dicom_file(str(filepath))
                
                if not info:
                    print(f"  SKIPPED: read_dicom_file returned None")
                    continue
                
                # Skip if not in selected series
                if self.selected_series is not None:
                    file_uid = info.get('series_uid')
                    if file_uid not in self.selected_series:
                        print(f"  SKIPPED: not in selected series")
                        print(f"  [DEBUG] File UID: '{file_uid}'")
                        print(f"  [DEBUG] Expected UIDs: {list(self.selected_series)[:2]}...")
                        continue
                
                print(f"  Modality: {info['modality']}, is_secondary: {info['is_secondary']}")
                
                # Secondary capture - SKIP (non utilizzabili per SUV)
                if info['is_secondary']:
                    print(f"  SKIPPED: Secondary Capture (not usable for SUV analysis)")
                    continue
                
                # DICOM originali
                if info['modality'] == 'PT':
                    print(f"  Processing as PET...")
                    result = self.calculate_suv_from_dicom(info, self.config['roi_fraction'])
                    if result:
                        self.pt_data.append(result)
                        
                        # Salva metadata acquisizione dal primo file PET
                        if not self.acquisition_metadata:
                            self.acquisition_metadata = {
                                'institution': info.get('institution_name', 'Unknown'),
                                'study_date': info.get('study_date', 'Unknown'),
                                'study_time': info.get('study_time', 'Unknown'),
                                'injected_activity_mbq': info.get('injected_activity_mbq', None)
                            }
                        
                        print(f"  PET processed successfully")
                    else:
                        print(f"  PET processing returned None")
                        
                elif info['modality'] == 'CT':
                    print(f"  Processing as CT...")
                    result = self.calculate_hu_from_dicom(info, self.config['roi_fraction'])
                    if result:
                        self.ct_data.append(result)
                        
                        # Salva metadata acquisizione dal primo file CT se non già salvati
                        if not self.acquisition_metadata:
                            self.acquisition_metadata = {
                                'institution': info.get('institution_name', 'Unknown'),
                                'study_date': info.get('study_date', 'Unknown'),
                                'study_time': info.get('study_time', 'Unknown'),
                                'injected_activity_mbq': None  # CT non ha attività
                            }
                        
                        print(f"  CT processed successfully")
                    else:
                        print(f"  CT processing returned None")
                else:
                    print(f"  Unknown modality: {info['modality']}")
                    
            except Exception as e:
                print(f"  CRASH: {e}")
                import traceback
                traceback.print_exc()
                raise  # Re-raise per far vedere l'errore completo
        
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
        
        # Analisi PET con griglia configurabile (default 25x25 NEMA NU 2-2012)
        if self.pt_data:
            grid_size = self.config.get('grid_size', 25)  # NEMA NU 2-2012: 25x25
            print(f"Esecuzione analisi NEMA PET (griglia {grid_size}x{grid_size})...")
            nema_pt = NEMAAnalysis(self.pt_data, modality='PT', grid_size=grid_size)
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
    
    def generate_html_report(self):
        """Genera report HTML interattivo (ritorna HTML come stringa)"""
        from suv_report_generator import HTMLReportGenerator
        
        # Esegui analisi NEMA
        print("\nEsecuzione analisi NEMA...")
        nema_results = self.analyze_nema_uniformity(
            example_slice_pt=self.config.get('example_slice_pt', 15),
            example_slice_ct=self.config.get('example_slice_ct', 15)
        )
        
        generator = HTMLReportGenerator(self, nema_results)
        html_content = generator.generate()
        
        print(f"\nReport HTML generato ({len(html_content)} caratteri)")
        return html_content  # Ritorna HTML come stringa
    
    def export_json(self):
        """
        Esporta risultati analisi in formato JSON
        
        Returns:
            dict con tutti i risultati dell'analisi
        """
        import json
        from datetime import datetime
        
        # Esegui analisi NEMA
        nema_results = self.analyze_nema_uniformity(
            example_slice_pt=self.config.get('example_slice_pt', 15),
            example_slice_ct=self.config.get('example_slice_ct', 15)
        )
        
        # Costruisci JSON strutturato
        export_data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'software': 'SUV Analyzer v3.3',
                'department': self.config.get('department', ''),
                'institution': self.config.get('institution', ''),
                'specialist': self.config.get('specialist', '')
            },
            'acquisition': self.acquisition_metadata,
            'configuration': self.config,
            'data_counts': {
                'pt_slices': len(self.pt_data),
                'ct_slices': len(self.ct_data)
            },
            'nema_results': {
                'pt': nema_results.get('pt', {}),
                'ct': nema_results.get('ct', {})
            }
        }
        
        # Converti numpy a native Python types
        def convert_numpy(obj):
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(i) for i in obj]
            return obj
        
        return convert_numpy(export_data)


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
    
    print("\nAnalisi completata!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
