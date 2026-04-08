"""
SUV NEMA Analysis Module - VERSIONE RINNOVATA
Analisi omogeneità secondo standard NEMA per PET/CT
Plot moderni e layout spaziale per immagini

Autore: Christian Bracco - S.C. Interaziendale di Fisica Sanitaria
"""

import numpy as np
import cv2
from io import BytesIO
import matplotlib
matplotlib.use('Agg')  # Backend non-interattivo
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import base64


# ============================================================================
# CONFIGURAZIONE STILE MATPLOTLIB MODERNO
# ============================================================================

def setup_modern_style():
    """Imposta stile matplotlib moderno e professionale"""
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Parametri globali
    plt.rcParams.update({
        'figure.facecolor': '#1a1a2e',
        'axes.facecolor': '#16213e',
        'axes.edgecolor': '#4FC3F7',
        'axes.labelcolor': '#e0e0e0',
        'axes.grid': True,
        'grid.color': '#2a2a4a',
        'grid.alpha': 0.5,
        'grid.linestyle': '--',
        'grid.linewidth': 0.8,
        'text.color': '#e0e0e0',
        'xtick.color': '#b0b0b0',
        'ytick.color': '#b0b0b0',
        'font.size': 11,
        'axes.titlesize': 13,
        'axes.labelsize': 11,
        'legend.facecolor': '#1a1a2e',
        'legend.edgecolor': '#4FC3F7',
        'legend.framealpha': 0.9
    })


# ============================================================================
# CLASSE PRINCIPALE NEMA ANALYSIS
# ============================================================================

class NEMAAnalysis:
    """Analisi omogeneità secondo NEMA 94 con plot moderni"""
    
    def __init__(self, results_data, modality='PT', grid_size=4):
        """
        Args:
            results_data: Lista risultati da SUVAnalyzer
            modality: 'PT' o 'CT'
            grid_size: Dimensione griglia (default 4x4, NEMA usa 15x15)
        """
        self.results_data = results_data
        self.modality = modality
        self.grid_size = grid_size
        self.slice_data = []
        
        # Setup stile moderno
        setup_modern_style()
        
    def analyze_pet_grid(self, example_slice=15):
        """
        Analisi PET con griglia NxN (default 4x4)
        
        Returns:
            slice_data: Lista statistiche per slice
            plot_combined: Plot CV e NU moderni
            plot_gallery: Galleria immagini con griglia
        """
        VMPmax = []
        VMPmin = []
        VMPmean = []
        SD = []
        CV = []
        NUmax = []
        NUmin = []
        
        # Raccolta immagini per galleria
        gallery_images = []
        
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
                img_with_grid = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            else:
                img_with_grid = img.copy()
            
            # GRIGLIA NEMA: calcola dimensioni in base al radius
            # ROI size: 1/10 del diametro del fantoccio (NEMA standard)
            roi_size = max(int(radius * 0.1), 6)  # min 6x6 pixel
            
            # Spacing: distribuisci le ROI uniformemente
            # Per grid 4x4, copri circa il 75% del diametro
            grid_span = int(radius * 1.5)  # 150% del radius = copre tutto il disco
            spacing = grid_span // self.grid_size
            
            # Centro griglia
            x_start = cx - grid_span // 2
            y_start = cy - grid_span // 2
            
            temp_means = []
            
            for j in range(self.grid_size):
                for i in range(self.grid_size):
                    x = x_start + i * spacing + spacing // 2
                    y = y_start + j * spacing + spacing // 2
                    
                    # Distanza dal centro
                    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                    
                    # Solo celle dentro il disco (con margine)
                    if dist < radius - roi_size:
                        # Disegna rettangolo ROI
                        half = roi_size // 2
                        top_left = (int(x - half), int(y - half))
                        bottom_right = (int(x + half), int(y + half))
                        cv2.rectangle(img_with_grid, top_left, bottom_right, (0, 255, 255), 1)
                        
                        # Estrai ROI cella
                        roi_cell = img[int(y - half):int(y + half), int(x - half):int(x + half)]
                        
                        # Calcola SUV
                        if roi_cell.size > 0:
                            suv_values = roi_cell * suv_scale_factor
                            cell_mean = np.mean(suv_values)
                            temp_means.append(cell_mean)
            
            # Disegna cerchio ROI
            cv2.circle(img_with_grid, (cx, cy), radius, (255, 0, 255), 2)
            
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
            
            # Salva per galleria (ogni 10 slice)
            if idx % 10 == 0 or idx == example_slice - 1:
                gallery_images.append({
                    'image': img_with_grid,
                    'instance': instance_number,
                    'cv': cv if temp_means else 0
                })
        
        # Grafici combinati
        instance_numbers = [d['instance_number'] for d in self.slice_data]
        plot_combined = self._create_combined_plot_modern(
            instance_numbers, CV, NUmax, NUmin, 'PET'
        )
        
        # Galleria immagini
        plot_gallery = self._create_image_gallery(gallery_images, 'PET')
        
        return self.slice_data, plot_combined, plot_gallery
    
    def analyze_ct_circles(self, example_slice=15):
        """
        Analisi CT con 5 cerchi concentrici (NEMA 94)
        
        Returns:
            slice_data: Lista statistiche per slice
            plot_combined: Plot CV e NU moderni
            plot_gallery: Galleria immagini con cerchi
        """
        VMPmax = []
        VMPmin = []
        VMPmean = []
        SD = []
        CV = []
        NUmax = []
        NUmin = []
        
        # Raccolta immagini per galleria
        gallery_images = []
        
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
                img_with_circles = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            else:
                img_with_circles = img.copy()
            
            # Disegna ROI principale
            cv2.circle(img_with_circles, (cx, cy), radius, (255, 0, 255), 2)
            
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
                cv2.circle(img_with_circles, (px, py), circle_radius, (0, 255, 255), 2)
                
                # Maschera cerchio
                mask_circle = np.zeros_like(img, dtype=np.uint8)
                cv2.circle(mask_circle, (px, py), circle_radius, 1, -1)
                
                # Media pixel nel cerchio
                masked_img = img * mask_circle
                mean_value = np.sum(masked_img) / np.sum(mask_circle) if np.sum(mask_circle) > 0 else 0
                
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
            
            # Salva per galleria (ogni 10 slice)
            if idx % 10 == 0 or idx == example_slice - 1:
                gallery_images.append({
                    'image': img_with_circles,
                    'instance': instance_number,
                    'cv': cv if temp_means else 0
                })
        
        # Grafici
        instance_numbers = [d['instance_number'] for d in self.slice_data]
        plot_combined = self._create_combined_plot_modern(
            instance_numbers, CV, NUmax, NUmin, 'CT'
        )
        
        # Galleria immagini
        plot_gallery = self._create_image_gallery(gallery_images, 'CT')
        
        return self.slice_data, plot_combined, plot_gallery
    
    def _create_combined_plot_modern(self, instance_numbers, CV, NUmax, NUmin, modality):
        """
        Crea plot combinato CV e NU con stile moderno
        Layout: 2 subplot affiancati con stile dark/neon
        """
        fig = plt.figure(figsize=(16, 6))
        gs = GridSpec(1, 2, figure=fig, wspace=0.3)
        
        # Colori moderni
        color_cv = '#00F2FE'  # Ciano neon
        color_nu_max = '#F093FB'  # Rosa neon
        color_nu_min = '#F5576C'  # Rosso neon
        
        # ===== SUBPLOT 1: COEFFICIENT OF VARIATION =====
        ax1 = fig.add_subplot(gs[0])
        
        # Plot scatter + linea connettrice
        ax1.plot(instance_numbers, CV, marker='o', markersize=8, 
                linestyle='-', linewidth=2, color=color_cv, 
                label='CV (%)', alpha=0.8, markerfacecolor=color_cv, 
                markeredgecolor='white', markeredgewidth=1.5)
        
        # Media line
        cv_mean = np.mean(CV)
        ax1.axhline(cv_mean, color='#FFD700', linestyle='--', 
                   linewidth=2, alpha=0.7, label=f'CV medio = {cv_mean:.2f}%')
        
        ax1.set_xlabel('Instance Number', fontsize=12, fontweight='bold')
        ax1.set_ylabel('CV (%)', fontsize=12, fontweight='bold')
        ax1.set_title(f'Coefficient of Variation - {modality} Images', 
                     fontsize=14, fontweight='bold', color='#4FC3F7', pad=15)
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)
        
        # ===== SUBPLOT 2: NON-UNIFORMITY =====
        ax2 = fig.add_subplot(gs[1])
        
        # Plot NUmax e NUmin
        ax2.plot(instance_numbers, NUmax, marker='s', markersize=7, 
                linestyle='-', linewidth=2, color=color_nu_max, 
                label='NU max (%)', alpha=0.8, markerfacecolor=color_nu_max,
                markeredgecolor='white', markeredgewidth=1.5)
        
        ax2.plot(instance_numbers, NUmin, marker='D', markersize=7, 
                linestyle='-', linewidth=2, color=color_nu_min, 
                label='NU min (%)', alpha=0.8, markerfacecolor=color_nu_min,
                markeredgecolor='white', markeredgewidth=1.5)
        
        # Linea zero
        ax2.axhline(0, color='white', linestyle=':', linewidth=1, alpha=0.5)
        
        # Limiti tolleranza (±15%)
        ax2.axhline(15, color='yellow', linestyle='--', linewidth=1.5, alpha=0.6)
        ax2.axhline(-15, color='yellow', linestyle='--', linewidth=1.5, alpha=0.6)
        
        ax2.set_xlabel('Instance Number', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Non-Uniformity (%)', fontsize=12, fontweight='bold')
        ax2.set_title(f'Non-Uniformity (NUmax & NUmin) - {modality} Images', 
                     fontsize=14, fontweight='bold', color='#4FC3F7', pad=15)
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Salva in buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, 
                   facecolor=fig.get_facecolor())
        buf.seek(0)
        plt.close()
        
        # Converti in base64
        img_b64 = base64.b64encode(buf.getvalue()).decode()
        return img_b64
    
    def _create_image_gallery(self, gallery_images, modality):
        """
        Crea galleria immagini 2x3 con slice ROI/griglia
        Layout spaziale moderno
        """
        if not gallery_images:
            return None
        
        # Prendi max 6 immagini
        images_to_show = gallery_images[:6]
        n_images = len(images_to_show)
        
        # Layout 2 righe x 3 colonne
        fig = plt.figure(figsize=(18, 12))
        gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.2)
        
        for idx, img_data in enumerate(images_to_show):
            row = idx // 3
            col = idx % 3
            ax = fig.add_subplot(gs[row, col])
            
            # Converti BGR a RGB
            img_rgb = cv2.cvtColor(img_data['image'], cv2.COLOR_BGR2RGB)
            
            ax.imshow(img_rgb)
            ax.axis('off')
            
            # Titolo con info
            title = f"Slice {img_data['instance']} | CV = {img_data['cv']:.2f}%"
            ax.set_title(title, fontsize=12, fontweight='bold', 
                        color='#4FC3F7', pad=10)
        
        # Titolo generale
        fig.suptitle(f'{modality} NEMA Analysis - ROI Gallery', 
                    fontsize=16, fontweight='bold', color='#4FC3F7', y=0.98)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Salva in buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150,
                   facecolor=fig.get_facecolor())
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
    
    if not valid_slices:
        return None
    
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
