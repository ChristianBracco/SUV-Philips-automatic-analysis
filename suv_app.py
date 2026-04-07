#!/usr/bin/env python3
"""
SUV Analyzer - Web Application
Interfaccia grafica completa per analisi quantitativa PET/CT

Esegui: python3 suv_app.py
Poi apri: http://localhost:7860

Autore: Dr. Christian Bracco
S.C. Interaziendale di Fisica Sanitaria - A.O. Mauriziano / ASL TO3
"""

import os
import sys
import gradio as gr
import numpy as np
import pydicom
from PIL import Image
import cv2
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
import json
import base64
from io import BytesIO
import logging
from collections import defaultdict

# Import moduli custom
from suv_analyzer import SUVAnalyzer
from nema_analysis import NEMAAnalysis

# Setup logging migliorato
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


# 🎨 CSS Custom
CUSTOM_CSS = """
.gradio-container {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
}

.header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 30px;
    border-radius: 15px;
    color: white;
    text-align: center;
    margin-bottom: 20px;
}

.header h1 {
    font-size: 2.5em;
    margin-bottom: 10px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

.status-box {
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    font-weight: bold;
}

.status-success {
    background: #d4edda;
    border-left: 5px solid #28a745;
    color: #155724;
}

.status-error {
    background: #f8d7da;
    border-left: 5px solid #dc3545;
    color: #721c24;
}

.status-info {
    background: #d1ecf1;
    border-left: 5px solid #17a2b8;
    color: #0c5460;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    margin: 10px 0;
}

.metric-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    margin: 10px;
}

.metric-value {
    font-size: 2em;
    font-weight: bold;
    margin: 10px 0;
}

.metric-label {
    font-size: 0.9em;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 1px;
}
"""
gr.HTML("""
<script>
document.addEventListener("wheel", function(e) {
    const el = document.querySelector("#mouse_event input");
    if (!el) return;

    el.value = e.deltaY;

    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
});
</script>
""")

class SUVAnalyzerApp:
    """Applicazione web SUV Analyzer"""
    
    def __init__(self):
        self.analyzer = None
        self.dicom_files = []
        self.series_groups = {}  # Raggruppa per serie
        self.temp_dir = None
        self.current_analysis_results = None
        self.window_center = 40  # W/L default
        self.window_width = 400
        logger.info("SUVAnalyzerApp inizializzata")
        
    def scan_dicom_folder(self, folder_path, progress=gr.Progress()):
        """Scansiona cartella DICOM e raggruppa per serie"""
        
        logger.info(f"🔍 Scansione cartella: {folder_path}")
        
        if not folder_path or not os.path.exists(folder_path):
            logger.error("Cartella non trovata")
            return (
                "❌ Cartella non trovata!",
                gr.update(choices=[], value=[]),
                gr.update(choices=[])
            )
        
        progress(0, desc="🔍 Ricerca file DICOM...")
        
        # Trova file DICOM
        dicom_files = sorted(Path(folder_path).glob('*.dcm'))
        
        if not dicom_files:
            logger.warning("Nessun file DICOM trovato")
            return (
                "❌ Nessun file DICOM trovato!",
                gr.update(choices=[], value=[]),
                gr.update(choices=[])
            )
        
        logger.info(f"Trovati {len(dicom_files)} file DICOM")
        
        # Raggruppa per serie
        series_dict = defaultdict(list)
        pt_count = ct_count = sc_count = 0
        
        for idx, filepath in enumerate(dicom_files):
            progress((idx + 1) / len(dicom_files), desc=f"Lettura {filepath.name}...")
            
            try:
                ds = pydicom.dcmread(str(filepath), stop_before_pixels=True)
                
                modality = ds.Modality if hasattr(ds, 'Modality') else 'Unknown'
                is_secondary = 'SECONDARY' in str(ds.ImageType) if hasattr(ds, 'ImageType') else False
                instance = int(ds.InstanceNumber) if hasattr(ds, 'InstanceNumber') else idx
                series_uid = ds.SeriesInstanceUID if hasattr(ds, 'SeriesInstanceUID') else f'series_{modality}_{idx}'
                series_desc = ds.SeriesDescription if hasattr(ds, 'SeriesDescription') else f'{modality} Series'
                
                # Icona e conteggio - priorità alla modalità
                if modality == 'PT':
                    icon = '🔬'
                    pt_count += 1
                    series_key = f'PT_{series_desc}'
                elif modality == 'CT':
                    icon = '🏥'
                    ct_count += 1
                    series_key = f'CT_{series_desc}'
                elif is_secondary:
                    icon = '📸'
                    sc_count += 1
                    series_key = f'SC_{series_desc}'
                else:
                    icon = '📄'
                    series_key = f'{modality}_{series_desc}'
                
                file_info = {
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'modality': modality,
                    'instance': instance,
                    'is_secondary': is_secondary,
                    'series_uid': series_uid,
                    'series_desc': series_desc,
                    'series_key': series_key,
                    'icon': icon
                }
                
                series_dict[series_key].append(file_info)
                
            except Exception as e:
                logger.error(f"Errore lettura {filepath.name}: {e}")
        
        # Ordina file dentro ogni serie per instance
        for series_key in series_dict:
            series_dict[series_key] = sorted(series_dict[series_key], key=lambda x: x['instance'])
        
        self.series_groups = dict(series_dict)
        self.dicom_files = [f for files in series_dict.values() for f in files]
        
        logger.info(f"✅ Trovate {len(self.series_groups)} serie: {pt_count} PET, {ct_count} CT, {sc_count} SC")
        
        # Crea summary
        summary = f"""
✅ **Scansione Completata**

📊 **Statistiche:**
- 🔬 File PET: **{pt_count}**
- 🏥 File CT: **{ct_count}**
- 📸 Secondary Captures: **{sc_count}**
- 📁 Totale file: **{len(self.dicom_files)}**
- 📦 Serie trovate: **{len(self.series_groups)}**

📂 **Cartella:** `{folder_path}`
"""
        
        # Crea checkbox raggruppati per serie
        series_checkboxes = []
        series_choices = []
        
        # Ordina serie: prima PT, poi CT, poi SC
        sorted_series = sorted(
            self.series_groups.keys(),
            key=lambda x: (0 if x.startswith('PT') else 1 if x.startswith('CT') else 2, x)
        )
        
        for series_key in sorted_series:
            files = self.series_groups[series_key]
            icon = files[0]['icon']
            modality = files[0]['modality']
            series_desc = files[0]['series_desc']
            
            label = f"{icon} {series_desc} ({len(files)} slices) - {modality}"
            series_checkboxes.append(label)
            series_choices.append(series_key)
        
        logger.info(f"Creati {len(series_checkboxes)} gruppi serie")
        
        return (
            summary,
            gr.update(choices=series_checkboxes, value=series_checkboxes),  # Tutti selezionati
            gr.update(choices=sorted_series, value=sorted_series[0] if sorted_series else None)
        )
    
    def apply_window_level(self, img, window_center, window_width):
        """Applica window/level all'immagine"""
        img = img.astype(np.float32)
        img_min = window_center - window_width // 2
        img_max = window_center + window_width // 2
        
        img_windowed = np.clip(img, img_min, img_max)
        img = (img - img_min) / (img_max - img_min) * 255.0
        
        return img.astype(np.uint8)
    def handle_mouse(self, delta, mode, slice_idx, wc, ww, zoom):
        if delta is None:
            return slice_idx, wc, ww, zoom

        step = -1 if delta > 0 else 1

        if mode == "Slice":
            slice_idx = max(0, slice_idx + step)

        elif mode == "W/L":
            wc += step * 5
            ww += step * 10
            ww = max(1, ww)

        elif mode == "Zoom":
            zoom += step * 0.1
            zoom = max(0.5, min(3.0, zoom))

        return slice_idx, wc, ww, zoom
        
    def convert_to_uint8(self, img):
        img = np.asarray(img)

        # Se già uint8 → ok
        if img.dtype == np.uint8:
            return img

        # Evita divisioni strane
        img = img.astype(np.float32)

        # Normalizzazione robusta
        min_val = np.min(img)
        max_val = np.max(img)

        if max_val - min_val == 0:
            return np.zeros_like(img, dtype=np.uint8)

        img = (img - min_val) / (max_val - min_val) * 255.0

        return img.astype(np.uint8) 


    
    def preview_dicom(self, selected_series, series_dropdown, slice_index, window_center, window_width, zoom_factor):
        """Preview DICOM con W/L e zoom"""
        
        if not self.series_groups or series_dropdown not in self.series_groups:
            logger.warning("Nessuna serie selezionata")
            return None, "❌ Seleziona una serie", window_center, window_width
        
        files = self.series_groups[series_dropdown]
        
        # Clamp slice_index al range valido
        max_idx = len(files) - 1
        if slice_index > max_idx:
            slice_index = max_idx
        if slice_index < 0:
            slice_index = 0
        
        info = files[slice_index]
        
        # Log per debug
        logger.info(f"Preview slice {slice_index}/{max_idx}: {info['filename']}")
        
        try:
            # Leggi DICOM
            ds = pydicom.dcmread(info['filepath'])
            img = ds.pixel_array
            img = self.convert_to_uint8(img)
            
            # 👉 split mosaic 3x3 (Philips tipico)
            if len(img.shape) == 3 and img.shape[2] == 3:
                h, w = img.shape[:2]
                tile_h, tile_w = h // 3, w // 3

                slices = []
                for r in range(3):
                    for c in range(3):
                        slices.append(img[r*tile_h:(r+1)*tile_h, c*tile_w:(c+1)*tile_w])

                img = slices[slice_index % len(slices)]            
            
            
            # Gestisci multi-frame
            if len(img.shape) == 4:
                img = img[0]  # Primo frame
            elif len(img.shape) == 3 and img.shape[0] < 10:  # Probabilmente frames
                img = img[0]
            
            # Applica W/L se grayscale
            if len(img.shape) == 2:
                # Grayscale - Auto W/L se default
                if window_center == 40 and window_width == 400:
                    # Cerca W/L in DICOM
                    if hasattr(ds, 'WindowCenter') and hasattr(ds, 'WindowWidth'):
                        wc = ds.WindowCenter
                        ww = ds.WindowWidth
                        # Se array, prendi primo valore
                        if isinstance(wc, (list, pydicom.multival.MultiValue)):
                            wc = float(wc[0])
                        if isinstance(ww, (list, pydicom.multival.MultiValue)):
                            ww = float(ww[0])
                        window_center = int(wc)
                        window_width = int(ww)
                    else:
                        # Auto-detect da modalità
                        modality = ds.Modality if hasattr(ds, 'Modality') else 'Unknown'
                        if modality == 'PT':
                            # PET: usa range SUV tipico
                            window_center = int(img.max() / 2)
                            window_width = int(img.max())
                        elif modality == 'CT':
                            # CT: soft tissue window
                            window_center = 40
                            window_width = 400
                
                img_windowed = self.apply_window_level(img, window_center, window_width)
                img_rgb = cv2.cvtColor(img_windowed, cv2.COLOR_GRAY2RGB)
            else:
                # RGB - Secondary Capture o già a colori
                # NON applicare W/L, mostra direttamente
                if img.dtype != np.uint8:
                    img_rgb = (img / img.max() * 255).astype(np.uint8)
                else:
                    img_rgb = img.copy()
            
            # Applica zoom
            if zoom_factor != 1.0:
                h, w = img_rgb.shape[:2]
                new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
                img_rgb = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                
                # Crop al centro se zoom > 1
                if zoom_factor > 1.0:
                    start_y = (new_h - h) // 2
                    start_x = (new_w - w) // 2
                    img_rgb = img_rgb[start_y:start_y+h, start_x:start_x+w]
            
            # UPSCALE per riempire viewer (minimo 800px)
            h, w = img_rgb.shape[:2]
            min_size = 800
            if h < min_size or w < min_size:
                scale = min_size / min(h, w)
                new_h, new_w = int(h * scale), int(w * scale)
                img_rgb = cv2.resize(img_rgb, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

            
            # Info text
            modality = info['modality']
            instance = info['instance']
            
            # Info aggiuntive
            series_desc = info['series_desc']
            
            info_text = f"""
### 📄 {info['filename']}

**Serie:** {series_desc}  
**Modalità:** {modality}  
**Instance:** {instance}  
**Slice:** {slice_index + 1} / {len(files)}  
**Dimensioni:** {img.shape}  
**Secondary:** {'✅ Sì' if info['is_secondary'] else '❌ No'}

**Window/Level:**  
- Center: {window_center}  
- Width: {window_width}

**Zoom:** {zoom_factor:.1f}x

**Slice {slice_index + 1} / {len(files)}**
"""
            
            logger.info(f"Preview: {info['filename']} - W/L: {window_center}/{window_width}, Zoom: {zoom_factor}x")
            
            return img_rgb, info_text, window_center, window_width
            
        except Exception as e:
            logger.error(f"Errore preview DICOM: {e}")
            return None, f"❌ Errore lettura DICOM: {e}", window_center, window_width
    
    def run_analysis(self, selected_series, config_text, output_folder, progress=gr.Progress()):
        """Esegue analisi SUV completa con NEMA"""
        
        if not selected_series or not self.series_groups:
            logger.error("Nessuna serie selezionata")
            return (
                "❌ Nessuna serie selezionata!",
                None, None, None, None,
                "❌ Seleziona almeno una serie"
            )
        
        logger.info("🚀 Avvio analisi SUV")
        progress(0, desc="🚀 Inizializzazione...")
        
        # Crea analyzer
        self.analyzer = SUVAnalyzer()
        
        # Salva config temp
        config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        config_file.write(config_text)
        config_file.close()
        self.analyzer.load_config_file(config_file.name)
        os.unlink(config_file.name)
        
        # Raccogli file dalle serie selezionate
        files_to_process = []
        for series_label in selected_series:
            # Trova series_key corrispondente
            for series_key, files in self.series_groups.items():
                icon = files[0]['icon']
                modality = files[0]['modality']
                series_desc = files[0]['series_desc']
                label = f"{icon} {series_desc} ({len(files)} slices) - {modality}"
                
                if label == series_label:
                    files_to_process.extend(files)
                    break
        
        logger.info(f"Processamento {len(files_to_process)} file da {len(selected_series)} serie")
        
        # Processa file
        for idx, info in enumerate(files_to_process):
            progress((idx + 1) / len(files_to_process), desc=f"📄 {Path(info['filepath']).name}")
            
            try:
                self.analyzer.process_single_dicom(info['filepath'])
            except Exception as e:
                logger.error(f"Errore processamento {info['filepath']}: {e}")
        
        progress(1.0, desc="✅ Analisi completata!")
        
        logger.info(f"✅ Processati: {len(self.analyzer.pt_data)} PET, {len(self.analyzer.ct_data)} CT, {len(self.analyzer.secondary_captures)} SC")
        
        # Genera summary e grafici
        import matplotlib.pyplot as plt
        plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans']
        
        summary = f"""
# 📊 Risultati Analisi

✅ **Processamento completato**

## 📈 Statistiche Acquisizione
"""
        
        figures = []
        
        # === PET Analysis ===
        if self.analyzer.pt_data:
            instances = [d['instance_number'] for d in self.analyzer.pt_data]
            suv_means = [d['suv_mean'] for d in self.analyzer.pt_data]
            suv_stds = [d['suv_std'] for d in self.analyzer.pt_data]
            
            summary += f"""
### 🔬 PET
- **Slices:** {len(self.analyzer.pt_data)}
- **SUV medio:** {np.mean(suv_means):.3f} ± {np.std(suv_means):.3f}
- **SUV range:** {np.min(suv_means):.3f} - {np.max(suv_means):.3f}
- **CV:** {np.std(suv_means) / np.mean(suv_means) * 100:.2f}%
"""
            
            # Grafici PET
            fig_pet, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
            
            ax1.errorbar(instances, suv_means, yerr=suv_stds,
                        fmt='o-', capsize=5, color='#3498db', linewidth=2, markersize=6)
            ax1.set_xlabel('Instance Number', fontsize=12)
            ax1.set_ylabel('SUV Mean', fontsize=12)
            ax1.set_title('PET - SUV Mean per Slice', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            
            ax2.hist(suv_means, bins=20, color='#e74c3c', alpha=0.7, edgecolor='black')
            ax2.axvline(np.mean(suv_means), color='#2c3e50', linestyle='--', linewidth=2,
                       label=f'Media: {np.mean(suv_means):.3f}')
            ax2.set_xlabel('SUV', fontsize=12)
            ax2.set_ylabel('Frequenza', fontsize=12)
            ax2.set_title('PET - Distribuzione SUV', fontsize=14, fontweight='bold')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            figures.append(('PET', fig_pet))
        
        # === CT Analysis ===
        if self.analyzer.ct_data:
            instances = [d['instance_number'] for d in self.analyzer.ct_data]
            hu_means = [d['hu_mean'] for d in self.analyzer.ct_data]
            hu_stds = [d['hu_std'] for d in self.analyzer.ct_data]
            
            summary += f"""
### 🏥 CT
- **Slices:** {len(self.analyzer.ct_data)}
- **HU medio:** {np.mean(hu_means):.1f} ± {np.std(hu_means):.1f}
- **HU range:** {np.min(hu_means):.1f} - {np.max(hu_means):.1f}
- **CV:** {np.std(hu_means) / np.mean(hu_means) * 100:.2f}%
"""
            
            # Grafico CT
            fig_ct, ax = plt.subplots(figsize=(10, 5))
            ax.errorbar(instances, hu_means, yerr=hu_stds,
                       fmt='s-', capsize=5, color='#9b59b6', linewidth=2, markersize=6)
            ax.set_xlabel('Instance Number', fontsize=12)
            ax.set_ylabel('HU Mean', fontsize=12)
            ax.set_title('CT - HU Mean per Slice', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            
            figures.append(('CT', fig_ct))
        
        # === NEMA Analysis ===
        nema_fig = None
        nema_ct_fig = None
        
        # NEMA PET
        if self.analyzer.pt_data and len(self.analyzer.pt_data) > 10:
            logger.info("🔬 Esecuzione analisi NEMA PET...")
            progress(0.8, desc="🔬 Analisi NEMA PET...")
            
            try:
                nema = NEMAAnalysis(self.analyzer.pt_data)
                slice_data, plot_combined, plot_example = nema.analyze_pet_grid()
                
                if plot_combined:
                    summary += f"\n### 🎯 Analisi NEMA PET (Griglia 15×15)\n"
                    summary += f"- **Slices analizzate:** {len(slice_data)}\n"
                    
                    if slice_data:
                        cv_values = [d['CV'] for d in slice_data]
                        nu_max = [d['NUmax'] for d in slice_data]
                        nu_min = [d['NUmin'] for d in slice_data]
                        
                        summary += f"- **CV medio:** {np.mean(cv_values):.2f}%\n"
                        summary += f"- **NU max medio:** {np.mean(nu_max):.2f}%\n"
                        summary += f"- **NU min medio:** {np.mean(nu_min):.2f}%\n"
                    
                    nema_fig = plot_combined
                    
            except Exception as e:
                logger.error(f"Errore analisi NEMA PET: {e}")
                summary += f"\n⚠️ Errore analisi NEMA PET: {e}\n"
        
        # NEMA CT
        if self.analyzer.ct_data and len(self.analyzer.ct_data) > 10:
            logger.info("🏥 Esecuzione analisi NEMA CT...")
            progress(0.9, desc="🏥 Analisi NEMA CT...")
            
            try:
                nema_ct = NEMAAnalysis(self.analyzer.ct_data, modality='CT')
                slice_data_ct, plot_combined_ct, plot_example_ct = nema_ct.analyze_ct_circles()
                
                if plot_combined_ct:
                    summary += f"\n### 🎯 Analisi NEMA CT (5 Cerchi)\n"
                    summary += f"- **Slices analizzate:** {len(slice_data_ct)}\n"
                    
                    if slice_data_ct:
                        cv_values = [d['CV'] for d in slice_data_ct]
                        nu_max = [d['NUmax'] for d in slice_data_ct]
                        nu_min = [d['NUmin'] for d in slice_data_ct]
                        
                        summary += f"- **CV medio:** {np.mean(cv_values):.2f}%\n"
                        summary += f"- **NU max medio:** {np.mean(nu_max):.2f}%\n"
                        summary += f"- **NU min medio:** {np.mean(nu_min):.2f}%\n"
                    
                    nema_ct_fig = plot_combined_ct
                    
            except Exception as e:
                logger.error(f"Errore analisi NEMA CT: {e}")
                summary += f"\n⚠️ Errore analisi NEMA CT: {e}\n"
        
        # Secondary Captures
        if self.analyzer.secondary_captures:
            summary += f"""
### 📸 Secondary Captures
- **File:** {len(self.analyzer.secondary_captures)}
"""
        
        summary += f"\n\n✅ **Analisi completata!** Vai al tab 'Report HTML' per generare il report completo."
        
        self.current_analysis_results = {
            'summary': summary,
            'figures': figures,
            'nema_fig': nema_fig
        }
        
        logger.info("✅ Analisi completata con successo")
        
        # Return: summary, pet_fig, ct_fig, nema_fig, status
        pet_fig = figures[0][1] if len(figures) > 0 and figures[0][0] == 'PET' else None
        ct_fig = figures[1][1] if len(figures) > 1 and figures[1][0] == 'CT' else None
        if not ct_fig and len(figures) > 0 and figures[0][0] == 'CT':
            ct_fig = figures[0][1]
        
        return (
            summary,
            pet_fig,
            ct_fig,
            nema_fig,
            "✅ Analisi completata! Genera il report HTML per vedere tutti i dettagli."
        )
    
    def generate_html_report(self, report_name, output_folder, progress=gr.Progress()):
        """Genera report HTML con path corretto"""
        
        if self.analyzer is None:
            logger.error("Analyzer non inizializzato")
            return "❌ Esegui prima l'analisi!", None
        
        logger.info(f"📄 Generazione report: {report_name}")
        progress(0, desc="📄 Generazione report HTML...")
        
        # Path corretto per Windows/Linux
        if not output_folder or not os.path.exists(output_folder):
            output_folder = os.getcwd()  # Directory corrente
        
        output_path = os.path.join(output_folder, report_name)
        
        try:
            progress(0.5, desc="🔬 Analisi NEMA in corso...")
            
            # Genera report
            self.analyzer.generate_html_report(output_path)
            
            progress(1.0, desc="✅ Report generato!")
            
            file_size = os.path.getsize(output_path) / 1024
            
            logger.info(f"✅ Report generato: {output_path} ({file_size:.1f} KB)")
            
            result = f"""
✅ **Report generato con successo!**

📄 **File:** `{output_path}`  
📊 **Dimensione:** {file_size:.1f} KB  
🕐 **Data:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

**Il report include:**
- ✅ Analisi SUV/HU completa
- ✅ Griglia NEMA 15×15 (PET)
- ✅ 5 cerchi NEMA (CT)
- ✅ Grafici interattivi Chart.js
- ✅ Tabelle con status QC
- ✅ Tutto embedded in HTML standalone
"""
            
            return result, output_path
            
        except Exception as e:
            logger.error(f"Errore generazione report: {e}")
            return f"❌ Errore: {e}", None
    
    def visualize_roi(self, modality_choice, slice_idx, window_center, window_width, zoom_factor):
        """Visualizza ROI con griglia/cerchi NEMA, zoom e W/L"""
        
        if self.analyzer is None:
            logger.warning("Analyzer non inizializzato")
            return None, "❌ Esegui prima l'analisi!"
        
        # Scegli dataset
        if modality_choice == 'PET':
            data = self.analyzer.pt_data
        elif modality_choice == 'CT':
            data = self.analyzer.ct_data
        elif modality_choice == 'Secondary Capture':
            data = self.analyzer.secondary_captures
        else:
            return None, f"❌ Modalità {modality_choice} non supportata"
        
        if not data or slice_idx >= len(data):
            return None, f"❌ Nessun dato {modality_choice} disponibile (slice {slice_idx})"
        
        slice_data = data[slice_idx]
        
        try:
            img = slice_data.get('image', None)
            
            if img is None:
                return None, "❌ Immagine non disponibile"
            
            # Gestisci dimensioni
            if len(img.shape) == 4:
                img = img[0]
            elif len(img.shape) == 3 and img.shape[0] < 10:
                img = img[0]
            
            # Converti in BGR per overlay
            if len(img.shape) == 2:
                # Applica W/L
                img_wl = self.apply_window_level(img, window_center, window_width)
                img_overlay = cv2.cvtColor(img_wl, cv2.COLOR_GRAY2BGR)
            else:
                if img.max() > 255:
                    img = (img / img.max() * 255).astype(np.uint8)
                img_overlay = img.copy()
            
            # Solo per PET/CT disegna ROI
            if modality_choice in ['PET', 'CT']:
                mask = slice_data.get('roi_mask')
                center = slice_data.get('roi_center')
                radius = slice_data.get('roi_radius')
                
                if center and radius:
                    cx, cy = center
                    
                    # Disegna cerchio ROI
                    cv2.circle(img_overlay, (cx, cy), radius, (255, 0, 0), 2)
                    
                    if modality_choice == 'PET':
                        # Griglia 15x15 centrata
                        cell_size = 4
                        grid_extent = 15 * cell_size
                        start_x = cx - (grid_extent // 2)
                        start_y = cy - (grid_extent // 2)
                        
                        for j in range(15):
                            for i in range(15):
                                cell_cx = start_x + i * cell_size + cell_size // 2
                                cell_cy = start_y + j * cell_size + cell_size // 2
                                
                                dist = np.sqrt((cell_cx - cx)**2 + (cell_cy - cy)**2)
                                
                                if dist < (radius - cell_size):
                                    top_left = (cell_cx - cell_size//2, cell_cy - cell_size//2)
                                    bottom_right = (cell_cx + cell_size//2, cell_cy + cell_size//2)
                                    cv2.rectangle(img_overlay, top_left, bottom_right, (0, 0, 255), 1)
                    
                    elif modality_choice == 'CT':
                        # 5 cerchi
                        area_circle = 0.05 * slice_data.get('roi_area', np.pi * radius**2)
                        circle_r = int(np.sqrt(area_circle / np.pi))
                        
                        positions = [
                            (cx, cy),
                            (cx, cy - radius // 2),
                            (cx + radius // 2, cy),
                            (cx, cy + radius // 2),
                            (cx - radius // 2, cy)
                        ]
                        
                        for pos in positions:
                            cv2.circle(img_overlay, pos, circle_r, (0, 0, 255), 2)
            
            # Applica zoom
            if zoom_factor != 1.0:
                h, w = img_overlay.shape[:2]
                new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
                img_overlay = cv2.resize(img_overlay, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                
                if zoom_factor > 1.0:
                    start_y = (new_h - h) // 2
                    start_x = (new_w - w) // 2
                    img_overlay = img_overlay[start_y:start_y+h, start_x:start_x+w]
            
            # Info text
            instance = slice_data.get('instance_number', slice_idx)
            
            info = f"""
### {modality_choice} - Slice {instance}

**Parametri Visualizzazione:**
- Window Center: {window_center}
- Window Width: {window_width}
- Zoom: {zoom_factor:.1f}x

"""
            
            if modality_choice == 'PET':
                info += f"""**Statistiche SUV:**
- Mean: {slice_data.get('suv_mean', 0):.3f}
- Std: {slice_data.get('suv_std', 0):.3f}
- Min: {slice_data.get('suv_min', 0):.3f}
- Max: {slice_data.get('suv_max', 0):.3f}

**ROI:**
- Centro: {center if 'center' in locals() else 'N/A'}
- Raggio: {radius if 'radius' in locals() else 'N/A'} px
- Area: {slice_data.get('roi_area', 0):.0f} px²

🎯 **Griglia NEMA 15×15 centrata** (rosso)
"""
            
            elif modality_choice == 'CT':
                info += f"""**Statistiche HU:**
- Mean: {slice_data.get('hu_mean', 0):.1f}
- Std: {slice_data.get('hu_std', 0):.1f}
- Min: {slice_data.get('hu_min', 0):.1f}
- Max: {slice_data.get('hu_max', 0):.1f}

**ROI:**
- Centro: {center if 'center' in locals() else 'N/A'}
- Raggio: {radius if 'radius' in locals() else 'N/A'} px
- Area: {slice_data.get('roi_area', 0):.0f} px²

🎯 **5 Cerchi NEMA (5% area)** (rosso)
- Centro, 12h, 3h, 6h, 9h
"""
            
            elif modality_choice == 'Secondary Capture':
                info += f"""**Dimensioni:** {img.shape}
**Tipo:** Secondary Capture (visualizzazione)
"""
            
            # Converti RGB
            img_rgb = cv2.cvtColor(img_overlay, cv2.COLOR_BGR2RGB)
            
            logger.info(f"ROI view: {modality_choice} slice {slice_idx}, W/L: {window_center}/{window_width}, Zoom: {zoom_factor}x")
            
            return img_rgb, info
            
        except Exception as e:
            logger.error(f"Errore visualizzazione ROI: {e}")
            import traceback
            traceback.print_exc()
            return None, f"❌ Errore: {e}"
    
    def create_interface(self):
        """Crea interfaccia Gradio"""
        
        with gr.Blocks(title="SUV Analyzer") as app:
            
            # Header
            gr.HTML("""
            <div class="header">
                <h1>🔬 SUV Analyzer Pro</h1>
                <p style="font-size: 1.2em; margin: 0;">
                    Analisi Quantitativa PET/CT con NEMA NU 2-2012
                </p>
                <p style="margin-top: 10px; opacity: 0.9;">
                    S.C. Interaziendale di Fisica Sanitaria - A.O. Mauriziano / ASL TO3
                </p>
            </div>
            """)
          
       
            mode_selector = gr.Radio(
                choices=["Slice", "W/L", "Zoom"],
                value="Slice",
                label="Modalità Mouse"
            )
          
            mouse_event = gr.Number(visible=False, elem_id="mouse_event")
            
            series_dropdown = gr.Dropdown(
                label="Serie DICOM",
                choices=[],
                value=None
            ) 
            
            with gr.Tabs():             
                # Tab 1: File Selection
                with gr.Tab("📁 Selezione File"):
                    gr.Markdown("### 🔍 Scansione Cartella DICOM")
                    
                    with gr.Row():
                        folder_input = gr.Textbox(
                            label="Cartella DICOM",
                            placeholder="/path/to/dicom/folder",
                            value=r"D:\AOM.SUV\SUV_DICOM"
                        )
                        scan_btn = gr.Button("🔍 Scansiona", variant="primary")
                    
                    scan_output = gr.Markdown()
                    
                    gr.Markdown("### ☑️ Selezione File")
                    file_checkboxes = gr.CheckboxGroup(
                        label="File DICOM trovati",
                        choices=[],
                        value=[]
                    )
                    
                    scan_btn.click(
                        fn=self.scan_dicom_folder,
                        inputs=[folder_input],
                        outputs=[scan_output, file_checkboxes, series_dropdown]
                    )
 
                # Tab 2: Preview
                with gr.Tab("👁️ Preview DICOM"):
 
                    gr.Markdown("### 🖼️ Visualizzazione Immagini")
                    series_dropdown
                    # --- CONTROLLI VISUALIZZAZIONE ---
                    with gr.Row():
                        window_center = gr.Number(value=40, label="Window Center")
                        window_width = gr.Number(value=400, label="Window Width")
                        zoom = gr.Slider(0.5, 3.0, value=1.0, step=0.1, label="Zoom")

                    # --- VISUALIZZAZIONE ---
                    with gr.Row():
                        with gr.Column(scale=3):
                            preview_image = gr.Image(
                                label="DICOM Preview",
                                show_label=False,
                                container=True
                            )
                        with gr.Column(scale=1):
                            preview_info = gr.Markdown("Seleziona una serie")

                    # --- SLIDER SLICE ---
                    preview_slider = gr.Slider(
                        minimum=0,
                        maximum=100,
                        step=1,
                        value=0,
                        label="Slice Navigator"
                    )

                    # --- STATE (per salvare W/L senza mostrarli) ---
                    wc_state = gr.State()
                    ww_state = gr.State()

                    # --- EVENTO ---
                    preview_slider.change(
                        fn=self.preview_dicom,
                        inputs=[
                            file_checkboxes,     # selected_series
                            series_dropdown,     # series_dropdown
                            preview_slider,      # slice_index
                            window_center,
                            window_width,
                            zoom
                        ],
                        outputs=[
                            preview_image,
                            preview_info,
                            wc_state,   # Window Center salvato
                            ww_state    # Window Width salvato
                        ]
                    )
                    for comp in [window_center, window_width, zoom, series_dropdown]:
                        comp.change(
                            fn=self.preview_dicom,
                            inputs=[
                                file_checkboxes,
                                series_dropdown,
                                preview_slider,
                                window_center,
                                window_width,
                                zoom
                            ],
                            outputs=[preview_image, preview_info, wc_state, ww_state]
                        )
                    
                    
                    
                    
                    
                    mouse_event.change(
                        fn=self.handle_mouse,
                        inputs=[
                            mouse_event,
                            mode_selector,
                            preview_slider,
                            window_center,
                            window_width,
                            zoom
                        ],
                        outputs=[
                            preview_slider,
                            window_center,
                            window_width,
                            zoom
                        ]
                    )
                    
                    
                    mouse_event.change(
                        fn=self.preview_dicom,
                        inputs=[
                            file_checkboxes,
                            series_dropdown,
                            preview_slider,
                            window_center,
                            window_width,
                            zoom
                        ],
                        outputs=[
                            preview_image,
                            preview_info,
                            wc_state,
                            ww_state
                        ]
                    )                    
                                    # Tab 3: Analysis
                with gr.Tab("🚀 Analisi SUV"):
                    gr.Markdown("### ⚙️ Configurazione")
                    
                    config_input = gr.Textbox(
                        label="Parametri Analisi",
                        value="""Frazione area ROI: 0.80
Limite superiore tolleranza SUV: 1.10
Limite inferiore tolleranza SUV: 0.90
Limite superiore NU PET: 15.0
Limite inferiore NU PET: -15.0
Limite superiore NU CT: 15.0
Limite inferiore NU CT: -15.0
Limite superiore CV CT: 15.0
Slice esempio PET: 15
Slice esempio CT: 15""",
                        lines=10
                    )
                    
                    analyze_btn = gr.Button("🚀 Avvia Analisi", variant="primary", size="lg")
                    
                    gr.Markdown("### 📊 Risultati")
                    
                    analysis_summary = gr.Markdown()
                    
                    with gr.Row():
                        plot_pet = gr.Plot(label="Grafici PET")
                        plot_ct = gr.Plot(label="Grafici CT")
                    
                    analysis_status = gr.Textbox(label="Status", interactive=False)
                    output_folder = gr.Textbox(value=".", visible=False)
                    analyze_btn.click(
                        fn=self.run_analysis,
                        inputs=[file_checkboxes, config_input, output_folder],
                        outputs=[analysis_summary, plot_pet, plot_ct, gr.State(), analysis_status]
                                        )
                
                # Tab 4: ROI Visualization
                # Tab ROI rimosso - non funzionante
                
                # Tab 5: Report Generation
                with gr.Tab("💾 Report HTML"):
                    gr.Markdown("### 📄 Generazione Report")
                    
                    report_name_input = gr.Textbox(
                        label="Nome File Report",
                        value="suv_report.html"
                    )
                    
                    generate_btn = gr.Button("💾 Genera Report HTML", variant="primary", size="lg")
                    
                    report_output = gr.Markdown()
                    report_file = gr.File(label="Download Report")
                    
                    generate_btn.click(
                        fn=self.generate_html_report,
                        inputs=[report_name_input],
                        outputs=[report_output, report_file]
                    )
            
            # Footer
            gr.HTML("""
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <p style="margin: 0; color: #6c757d;">
                    <strong>SUV Analyzer v1.0</strong> | 
                    Dr. Christian Bracco | 
                    S.C. Interaziendale di Fisica Sanitaria
                </p>
            </div>
            """)
        
        return app


def main():
    """Main entry point"""
    
    print("\n" + "="*60)
    print("✅ Server avviato!")
    print("📱 Apri nel browser: http://localhost:7860")
    print("🌐 Oppure: http://127.0.0.1:7860")
    print("="*60)

    # Crea app
    app_instance = SUVAnalyzerApp()
    app = app_instance.create_interface()
    
    # Lancia server (bloccante)
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        quiet=False,
        theme=gr.themes.Soft(),
        css=CUSTOM_CSS
    )


if __name__ == '__main__':
    main()
