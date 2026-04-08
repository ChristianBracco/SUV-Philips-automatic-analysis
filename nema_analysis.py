"""
SUV NEMA Analysis Module
Analisi omogeneità secondo standard NEMA per PET/CT
"""

import numpy as np
import cv2
from io import BytesIO
import matplotlib.pyplot as plt
import base64
from PIL import Image


class NEMAAnalysis:
    """Analisi omogeneità secondo NEMA 94"""
    
    def __init__(self, results_data, modality='PT', grid_size=15):
        """
        Args:
            results_data: Lista risultati da SUVAnalyzer
            modality: 'PT' o 'CT'
            grid_size: Dimensione griglia (default 15x15 per PET)
        """
        self.results_data = results_data
        self.modality = modality
        self.grid_size = grid_size
        self.slice_data = []
        
    def analyze_pet_grid(self, example_slice=15):
        """
        Analisi PET con griglia 15x15 (NEMA 94)
        
        Returns:
            slice_data: Lista statistiche per slice
            plot_combined: Plot CV e NU combinati
            plot_example: Immagine esempio con griglia
        """
        VMPmax = []
        VMPmin = []
        VMPmean = []
        SD = []
        CV = []
        NUmax = []
        NUmin = []
        
        example_img = None
        
        for idx, result in enumerate(self.results_data):
            # Estrai dati
            radius = result['roi_radius']
            center = result['roi_center']
            img = result['image']
            mask = result['roi_mask']
            instance_number = result['instance_number']
            suv_scale_factor = result.get('suv_scale_factor', 1.0)
            
            cx, cy = center
            
            # Converti in BGR per disegnare
            if len(img.shape) == 2:
                if img.dtype != np.uint8:
                    image = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                else:
                    image = img
                img_with_circle = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                img_with_grid = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                img_with_circle = img.copy()
                img_with_grid = img.copy()
            
            # Disegna cerchio ROI
            cv2.circle(img_with_circle, (cx, cy), radius, (255, 0, 0), 2)
            
            # Griglia 15x15 con celle 4x4
            temp_means = []
            cell_size = 4
            x = cx - radius
            y = cy - radius
            
            for j in range(self.grid_size):
                for i in range(self.grid_size):
                    # Distanza dal centro
                    m = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    
                    # Solo celle dentro ROI
                    if m < radius - 4:
                        # Disegna rettangolo
                        top_left = (x - 2, y - 2)
                        bottom_right = (x + 2, y + 2)
                        cv2.rectangle(img_with_grid, top_left, bottom_right, (0, 0, 255), 1)
                        
                        # Estrai ROI cella
                        roi_cell = img[int(y - 2):int(y + 2), int(x - 2):int(x + 2)]
                        
                        # Calcola SUV
                        if roi_cell.size > 0:
                            suv_values = roi_cell * suv_scale_factor
                            cell_mean = np.mean(suv_values)
                            temp_means.append(cell_mean)
                    
                    x += cell_size
                
                # Prossima riga
                x = cx - radius
                y += cell_size
            
            # Statistiche slice
            if temp_means:
                vmp_max = np.max(temp_means)
                vmp_min = np.min(temp_means)
                vmp_mean = np.mean(temp_means)
                sd = np.std(temp_means)
                
                VMPmax.append(vmp_max)
                VMPmin.append(vmp_min)
                VMPmean.append(vmp_mean)
                SD.append(sd)
                
                # NEMA metrics
                cv = 100 * sd / vmp_mean if vmp_mean > 0 else 0
                nu_max = 100 * (vmp_max - vmp_mean) / vmp_mean if vmp_mean > 0 else 0
                nu_min = -100 * (vmp_mean - vmp_min) / vmp_mean if vmp_mean > 0 else 0
                
                CV.append(cv)
                NUmax.append(nu_max)
                NUmin.append(nu_min)
                
                self.slice_data.append({
                    'instance_number': instance_number,
                    'VMPmax': vmp_max,
                    'VMPmin': vmp_min,
                    'VMPmean': vmp_mean,
                    'SD': sd,
                    'CV': cv,
                    'NUmax': nu_max,
                    'NUmin': nu_min
                })
            
            # Salva esempio
            if idx == example_slice - 1:
                example_img = (img_with_circle, img_with_grid)
        
        # Grafici combinati
        instance_numbers = [d['instance_number'] for d in self.slice_data]
        plot_combined = self._create_combined_plot(instance_numbers, CV, NUmax, NUmin, 'PET')
        plot_example = self._create_example_plot(example_img, example_slice) if example_img else None
        
        return self.slice_data, plot_combined, plot_example
    
    def analyze_ct_circles(self, example_slice=15):
        """
        Analisi CT con 5 cerchi concentrici (NEMA 94)
        
        Returns:
            slice_data: Lista statistiche per slice
            plot_combined: Plot CV e NU combinati
            plot_example: Immagine esempio con cerchi
        """
        VMPmax = []
        VMPmin = []
        VMPmean = []
        SD = []
        CV = []
        NUmax = []
        NUmin = []
        
        example_img = None
        
        for idx, result in enumerate(self.results_data):
            # Estrai dati
            radius = result['roi_radius']
            center = result['roi_center']
            img = result['image']
            area_80 = result['roi_area']
            instance_number = result['instance_number']
            
            cx, cy = center
            
            # Converti in BGR
            if len(img.shape) == 2:
                if img.dtype != np.uint8:
                    image = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                else:
                    image = img
                img_with_circle = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
                img_with_circles = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                img_with_circle = img.copy()
                img_with_circles = img.copy()
            
            # Disegna ROI principale
            cv2.circle(img_with_circle, (cx, cy), radius, (255, 0, 0), 2)
            
            # 5 cerchi al 5% dell'area ROI
            area_circle = 0.05 * area_80
            circle_radius = int(np.sqrt(area_circle / np.pi))
            
            # Posizioni: centro, 12h, 3h, 6h, 9h
            positions = {
                'center': (cx, cy),
                'top': (cx, cy - radius // 2),
                'right': (cx + radius // 2, cy),
                'bottom': (cx, cy + radius // 2),
                'left': (cx - radius // 2, cy)
            }
            
            temp_means = []
            circle_means_dict = {}
            
            for pos_name, (px, py) in positions.items():
                # Disegna cerchio
                cv2.circle(img_with_circles, (px, py), circle_radius, (0, 0, 255), 2)
                
                # Maschera cerchio
                mask = np.zeros_like(img, dtype=np.uint8)
                cv2.circle(mask, (px, py), circle_radius, 1, -1)
                
                # Media pixel nel cerchio
                masked_img = img * mask
                mean_value = np.sum(masked_img) / np.sum(mask) if np.sum(mask) > 0 else 0
                
                temp_means.append(mean_value)
                circle_means_dict[pos_name] = mean_value
            
            # Statistiche
            if temp_means:
                vmp_max = np.max(temp_means)
                vmp_min = np.min(temp_means)
                vmp_mean = np.mean(temp_means)
                sd = np.std(temp_means)
                
                VMPmax.append(vmp_max)
                VMPmin.append(vmp_min)
                VMPmean.append(vmp_mean)
                SD.append(sd)
                
                # NEMA metrics
                cv = 100 * sd / vmp_mean if vmp_mean > 0 else 0
                nu_max = 100 * (vmp_max - vmp_mean) / vmp_mean if vmp_mean > 0 else 0
                nu_min = -100 * (vmp_mean - vmp_min) / vmp_mean if vmp_mean > 0 else 0
                
                CV.append(cv)
                NUmax.append(nu_max)
                NUmin.append(nu_min)
                
                self.slice_data.append({
                    'instance_number': instance_number,
                    'circle_means': circle_means_dict,
                    'VMPmax': vmp_max,
                    'VMPmin': vmp_min,
                    'VMPmean': vmp_mean,
                    'SD': sd,
                    'CV': cv,
                    'NUmax': nu_max,
                    'NUmin': nu_min
                })
            
            # Salva esempio
            if idx == example_slice - 1:
                example_img = (img_with_circle, img_with_circles)
        
        # Grafici
        instance_numbers = [d['instance_number'] for d in self.slice_data]
        plot_combined = self._create_combined_plot(instance_numbers, CV, NUmax, NUmin, 'CT')
        plot_example = self._create_example_plot(example_img, example_slice) if example_img else None
        
        return self.slice_data, plot_combined, plot_example
    
    def _create_combined_plot(self, instance_numbers, CV, NUmax, NUmin, modality):
        """Crea plot combinato CV e NU"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Plot CV
        ax1.plot(instance_numbers, CV, marker='o', linestyle='None', color='b', label='CV')
        ax1.set_xlabel('Instance Number')
        ax1.set_ylabel('CV (%)')
        ax1.set_title(f'CV vs Instance Number ({modality} images)')
        ax1.grid(True)
        ax1.legend()
        
        # Plot NU
        ax2.plot(instance_numbers, NUmax, marker='o', linestyle='None', color='g', label='NUmax')
        ax2.plot(instance_numbers, NUmin, marker='o', linestyle='None', color='r', label='NUmin')
        ax2.set_xlabel('Instance Number')
        ax2.set_ylabel('Non Uniformity (%)')
        ax2.set_title(f'NUmax and NUmin vs Instance Number ({modality} images)')
        ax2.grid(True)
        ax2.legend()
        
        plt.tight_layout()
        
        # Salva in buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        plt.close()
        
        # Converti in base64
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        return img_b64
    
    def _create_example_plot(self, images, slice_num):
        """Crea plot esempio con ROI e griglia/cerchi"""
        img_circle, img_overlay = images
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        ax1.imshow(cv2.cvtColor(img_circle, cv2.COLOR_BGR2RGB))
        ax1.set_title(f'ROI Contour (Slice {slice_num})')
        ax1.axis('off')
        
        ax2.imshow(cv2.cvtColor(img_overlay, cv2.COLOR_BGR2RGB))
        title = 'Grid in ROI' if self.modality == 'PT' else 'Circles in ROI'
        ax2.set_title(f'{title} (Slice {slice_num})')
        ax2.axis('off')
        
        plt.tight_layout()
        
        # Salva in buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        plt.close()
        
        # Converti in base64
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        return img_b64


def calculate_nema_statistics(slice_data, config):
    """
    Calcola statistiche NEMA complete
    
    Args:
        slice_data: Lista dati slice
        config: Configurazione con limiti
        
    Returns:
        dict con statistiche e valutazioni QC
    """
    if not slice_data:
        return None
    
    # Escludi prime 5 e ultime 5 slices
    n_slices = len(slice_data)
    valid_slices = slice_data[5:n_slices-5] if n_slices > 10 else slice_data
    
    # Estrai metriche
    cv_values = [s['CV'] for s in valid_slices]
    nu_max_values = [s['NUmax'] for s in valid_slices]
    nu_min_values = [s['NUmin'] for s in valid_slices]
    
    # Statistiche globali
    stats = {
        'cv_mean': np.mean(cv_values) if cv_values else 0,
        'cv_std': np.std(cv_values) if cv_values else 0,
        'cv_max': np.max(cv_values) if cv_values else 0,
        'cv_min': np.min(cv_values) if cv_values else 0,
        'nu_max_mean': np.mean(nu_max_values) if nu_max_values else 0,
        'nu_min_mean': np.mean(nu_min_values) if nu_min_values else 0,
        'nu_max_max': np.max(nu_max_values) if nu_max_values else 0,
        'nu_min_min': np.min(nu_min_values) if nu_min_values else 0
    }
    
    # Valutazione QC
    cv_pass = all(cv < config.get('cv_ct_upper', 15.0) for cv in cv_values)
    nu_pass = all(
        config.get('nu_pet_lower', -15.0) < nu_min < nu_max < config.get('nu_pet_upper', 15.0)
        for nu_min, nu_max in zip(nu_min_values, nu_max_values)
    )
    
    stats['cv_pass'] = cv_pass
    stats['nu_pass'] = nu_pass
    stats['overall_pass'] = cv_pass and nu_pass
    
    return stats
