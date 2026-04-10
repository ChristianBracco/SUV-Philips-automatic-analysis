"""
SUV HTML Report Generator
Genera report HTML professionali con grafici interattivi e analisi statistiche
"""

import json
from datetime import datetime
import base64
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Backend non-GUI per server
import matplotlib.pyplot as plt
from io import BytesIO


class HTMLReportGenerator:
    """Generatore report HTML per analisi SUV"""
    
    def __init__(self, analyzer, nema_results=None):
        self.analyzer = analyzer
        self.pt_data = analyzer.pt_data
        self.ct_data = analyzer.ct_data
        self.secondary_captures = analyzer.secondary_captures
        self.config = analyzer.config
        self.nema_results = nema_results
        # Configurazione matplotlib per SVG
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def _create_svg_plot(self, x_data, y_data, xlabel, ylabel, title, color='#3b82f6', show_grid=True, y_range=None):
        """Crea grafico SVG lineare responsive che fitta perfettamente"""
        fig, ax = plt.subplots(figsize=(12, 4), dpi=100)
        
        # Imposta sfondo bianco esplicito
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        ax.plot(x_data, y_data, color=color, linewidth=2.5, marker='o', markersize=5)
        ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        
        # Griglia sempre visibile
        ax.grid(True, alpha=0.4, linewidth=0.8, linestyle='--', color='#cccccc')
        
        # Imposta range Y se specificato
        if y_range:
            ax.set_ylim(y_range)
        
        ax.tick_params(labelsize=10)
        
        # Tight layout per eliminare spazi bianchi
        plt.tight_layout(pad=0.1)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='svg', bbox_inches='tight', transparent=False, pad_inches=0.05, facecolor='white')
        plt.close(fig)
        buffer.seek(0)
        svg_string = buffer.getvalue().decode('utf-8')
        
        return svg_string
    
    def _create_svg_scatter_range(self, x_data, y_min, y_max, y_mean, xlabel, ylabel, title, y_range=None):
        """Crea grafico SVG con range (min/max) e media che fitta perfettamente"""
        fig, ax = plt.subplots(figsize=(12, 4), dpi=100)
        
        # Imposta sfondo bianco esplicito
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        ax.fill_between(x_data, y_min, y_max, alpha=0.25, color='#3b82f6', label='Range Min-Max')
        ax.plot(x_data, y_mean, color='#ef4444', linewidth=2.5, marker='o', markersize=5, label='Mean')
        
        ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        ax.legend(loc='best', fontsize=10)
        
        # Griglia sempre visibile
        ax.grid(True, alpha=0.4, linewidth=0.8, linestyle='--', color='#cccccc')
        
        # Imposta range Y se specificato
        if y_range:
            ax.set_ylim(y_range)
        
        ax.tick_params(labelsize=10)
        
        plt.tight_layout(pad=0.1)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='svg', bbox_inches='tight', transparent=False, pad_inches=0.05, facecolor='white')
        plt.close(fig)
        buffer.seek(0)
        svg_string = buffer.getvalue().decode('utf-8')
        
        return svg_string
    
    def _create_svg_histogram(self, data, xlabel, ylabel, title, bins=30, color='#3b82f6'):
        """Crea istogramma SVG che fitta perfettamente"""
        fig, ax = plt.subplots(figsize=(12, 4), dpi=100)
        
        # Imposta sfondo bianco esplicito
        fig.patch.set_facecolor('white')
        ax.set_facecolor('white')
        
        ax.hist(data, bins=bins, color=color, alpha=0.75, edgecolor='black', linewidth=0.8)
        ax.set_xlabel(xlabel, fontsize=11, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=11, fontweight='bold')
        ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
        
        # Griglia sempre visibile
        ax.grid(True, alpha=0.4, axis='y', linewidth=0.8, linestyle='--', color='#cccccc')
        
        ax.tick_params(labelsize=10)
        
        plt.tight_layout(pad=0.1)
        
        buffer = BytesIO()
        plt.savefig(buffer, format='svg', bbox_inches='tight', transparent=False, pad_inches=0.05, facecolor='white')
        plt.close(fig)
        buffer.seek(0)
        svg_string = buffer.getvalue().decode('utf-8')
        
        return svg_string
        
    def _generate_dicom_section(self):
        """Genera sezione con immagini DICOM rappresentative (CT e PET) con ROI"""
        if not self.nema_results:
            return ""

        gallery_html = ""
        
        # Immagine PET con ROI (se disponibile)
        if 'pet' in self.nema_results and self.nema_results['pet'].get('plot_example'):
            pet_img_b64 = self.nema_results['pet']['plot_example']
            gallery_html += f"""
                <div class="dicom-roi-container">
                    <div class="dicom-roi-header">
                        <div class="modality-badge pet-badge">PET</div>
                        <h3>Immagine PET con ROI NEMA</h3>
                    </div>
                    <img src="data:image/png;base64,{pet_img_b64}" class="dicom-roi-image">
                    <div class="dicom-roi-caption">
                        Griglia NEMA {self.config.get('grid_size', 4)}×{self.config.get('grid_size', 4)} 
                        per analisi omogeneità SUV
                    </div>
                </div>
            """
        
        # Immagine CT con ROI (se disponibile)
        if 'ct' in self.nema_results and self.nema_results['ct'].get('plot_example'):
            ct_img_b64 = self.nema_results['ct']['plot_example']
            gallery_html += f"""
                <div class="dicom-roi-container">
                    <div class="dicom-roi-header">
                        <div class="modality-badge ct-badge">CT</div>
                        <h3>Immagine CT con ROI NEMA</h3>
                    </div>
                    <img src="data:image/png;base64,{ct_img_b64}" class="dicom-roi-image">
                    <div class="dicom-roi-caption">
                        5 cerchi concentrici per analisi omogeneità HU
                    </div>
                </div>
            """

        if not gallery_html:
            return ""

        return f"""
        <div class="section dicom-section">
            <div class="section-title">
                <div class="icon">🧠</div>
                <div>Immagini DICOM con ROI</div>
            </div>

            <div class="dicom-roi-gallery">
                {gallery_html}
            </div>
        </div>
        """
            
        
    
    def generate(self):
        """Genera report HTML completo"""
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SUV Quality Control Report</title>
    <style>
        {self._generate_css()}
    </style>
</head>
<body>
    {self._generate_toolbar()}
    {self._generate_header()}
    {self._generate_summary()}
    {self._generate_pet_section()}
    {self._generate_nema_pet_section()}
    {self._generate_ct_section()}
    {self._generate_nema_ct_section()}
    {self._generate_dicom_section()}
    {self._generate_conclusions_section()}
    {self._generate_footer()}
    {self._generate_javascript()}
</body>
</html>"""
        return html
    
    def _generate_css(self):
        """CSS styling professionale medico"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary: #2c3e50;
            --secondary: #3498db;
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --bg-light: #ecf0f1;
            --text: #2c3e50;
            --border: #bdc3c7;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: var(--text);
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
            color: white;
            padding: 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 3s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            position: relative;
            z-index: 1;
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }
        
        .header .institution {
            margin-top: 20px;
            padding: 15px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            backdrop-filter: blur(10px);
            position: relative;
            z-index: 1;
        }
        
        .metadata-separator {
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255,255,255,0.3);
        }
        
        .metadata-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9em;
        }
        
        .metadata-grid div {
            color: white;
        }
        
        .metadata-grid strong {
            color: #fff;
        }
        
        .report-timestamp {
            margin-top: 10px;
            opacity: 0.8;
            font-size: 0.85em;
        }
        
        /* Summary Cards */
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            padding: 40px;
            background: var(--bg-light);
        }
        
        .summary-card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
            border-left: 5px solid var(--secondary);
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .summary-card .label {
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 2em;
            font-weight: bold;
            color: var(--primary);
        }
        
        .summary-card .unit {
            font-size: 0.8em;
            color: #95a5a6;
            margin-left: 5px;
        }
        
        /* Section */
        .section {
            padding: 40px;
            border-bottom: 2px solid var(--bg-light);
        }
        
        .section-title {
            font-size: 2em;
            color: var(--primary);
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--secondary);
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .section-title .icon {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, var(--secondary), var(--primary));
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.5em;
        }
        
        /* Charts */
        .chart-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .chart-title {
            font-size: 1.3em;
            color: var(--primary);
            margin-bottom: 20px;
            font-weight: 600;
        }
        
        /* SVG responsive - fitta perfettamente il container */
        .chart-container svg {
            width: 100%;
            height: auto;
            max-width: 100%;
            display: block;
        }
        
        /* Griglia per i 3 grafici - layout verticale, 1 colonna */
        .charts-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .charts-grid .chart-container {
            margin-bottom: 0;
        }
        
        /* Table */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .data-table thead {
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
        }
        
        .data-table th {
            padding: 8px 10px;
            text-align: left;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75em;
            letter-spacing: 0.5px;
        }
        
        .data-table td {
            padding: 6px 10px;
            border-bottom: 1px solid var(--bg-light);
            font-size: 0.85em;
        }
        
        .data-table tbody tr:hover {
            background: #f8f9fa;
        }
        
        .data-table tbody tr:last-child td {
            border-bottom: none;
        }
        
        /* Status badges */
        .badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .badge-success {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-warning {
            background: #fff3cd;
            color: #856404;
        }
        
        .badge-danger {
            background: #f8d7da;
            color: #721c24;
        }
        
        /* Images */
        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .image-item {
            background: white;
            padding: 15px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .image-item img {
            width: 100%;
            height: auto;
            border-radius: 10px;
            margin-bottom: 10px;
        }
        
        .image-caption {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.9em;
        }
        
        /* DICOM ROI Images */
        .dicom-roi-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-top: 20px;
        }
        
        .dicom-roi-container {
            background: white;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 6px 20px rgba(0,0,0,0.12);
            border: 2px solid var(--bg-light);
            page-break-inside: avoid;
        }
        
        .dicom-roi-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .dicom-roi-header h3 {
            margin: 0;
            color: var(--primary);
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .modality-badge {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .pet-badge {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .ct-badge {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            color: white;
        }
        
        .dicom-roi-image {
            width: 100%;
            height: auto;
            border-radius: 10px;
            margin-bottom: 12px;
            border: 1px solid var(--border);
        }
        
        .dicom-roi-caption {
            text-align: center;
            color: #7f8c8d;
            font-size: 0.95em;
            font-style: italic;
            padding: 10px;
            background: var(--bg-light);
            border-radius: 8px;
        }
        
        /* Footer */
        .footer {
            background: var(--primary);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .footer .timestamp {
            opacity: 0.8;
            font-size: 0.9em;
        }
        
        /* Toolbar Print/PDF */
        .toolbar {
            position: sticky;
            top: 0;
            z-index: 1000;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 15px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        
        .toolbar-title {
            color: white;
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .toolbar-buttons {
            display: flex;
            gap: 15px;
        }
        
        .btn {
            padding: 10px 25px;
            border: none;
            border-radius: 25px;
            font-size: 0.95em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .btn-print {
            background: white;
            color: #667eea;
        }
        
        .btn-print:hover {
            background: #f0f0f0;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        .btn-pdf {
            background: #e74c3c;
            color: white;
        }
        
        .btn-pdf:hover {
            background: #c0392b;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        
        /* Print styles */
        @page {
            size: A4 portrait;
            margin: 10mm 8mm;
        }
        
        @media print {

            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }

            body {
                background: white !important;
                margin: 0 !important;
                padding: 0 !important;
                font-size: 8pt !important;
                line-height: 1.2 !important;
                color: #000 !important;
            }

            .toolbar {
                display: none !important;
            }

            .container {
                max-width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                background: white !important;
                box-shadow: none !important;
                border-radius: 0 !important;
            }

            /* HEADER - compatto */
            .header {
                page-break-inside: avoid;
                background: #2c3e50 !important;
                color: white !important;
                padding: 4mm 6mm !important;
                margin-bottom: 2mm !important;
            }
            .header h1 {
                font-size: 13pt !important;
                margin-bottom: 1mm !important;
            }
            .header .subtitle {
                font-size: 9pt !important;
                margin-bottom: 2mm !important;
            }
            .header .institution {
                font-size: 8pt !important;
                padding: 2mm !important;
            }
            .metadata-separator {
                margin-top: 2mm !important;
                padding-top: 2mm !important;
            }
            .metadata-grid {
                grid-template-columns: 1fr 1fr !important;
                gap: 1mm !important;
                font-size: 8pt !important;
                line-height: 1.4 !important;
            }
            .report-timestamp {
                margin-top: 2mm !important;
                font-size: 7pt !important;
            }

            /* SUMMARY - 5 cards in riga unica */
            .summary {
                page-break-inside: avoid;
                display: grid !important;
                grid-template-columns: repeat(5, 1fr) !important;
                gap: 2mm !important;
                padding: 2mm !important;
                margin-bottom: 2mm !important;
                background: #f8f9fa !important;
            }
            .summary-card {
                padding: 2mm !important;
                border: 0.5pt solid #ccc !important;
                background: white !important;
                box-shadow: none !important;
                border-left-width: 3px !important;
            }
            .summary-card .label {
                font-size: 6pt !important;
                margin-bottom: 1mm !important;
            }
            .summary-card .value {
                font-size: 11pt !important;
            }

            /* SEZIONI */
            .section {
                padding: 3mm 4mm !important;
                margin-bottom: 2mm !important;
                border-bottom: 1pt solid #e0e0e0 !important;
                page-break-inside: avoid;
            }
            .section-title {
                font-size: 10pt !important;
                margin-bottom: 2mm !important;
                padding-bottom: 1.5mm !important;
            }
            .section-title .icon {
                width: 22px !important;
                height: 22px !important;
                font-size: 0.9em !important;
            }

            /* SUB-SUMMARY dentro sezioni (3 cards) */
            .section .summary {
                grid-template-columns: repeat(3, 1fr) !important;
                margin-bottom: 2mm !important;
                padding: 0 !important;
            }

            /* GRAFICI */
            .chart-container {
                page-break-inside: avoid;
                margin-bottom: 2mm !important;
                padding: 2mm !important;
                border: 0.5pt solid #e0e0e0 !important;
                box-shadow: none !important;
                border-radius: 4px !important;
            }
            .chart-title {
                font-size: 8pt !important;
                margin-bottom: 1mm !important;
                font-weight: bold !important;
            }
            .chart-container svg,
            .chart-container img {
                max-width: 100% !important;
                max-height: 55mm !important;
                height: auto !important;
                width: 100% !important;
            }
            .chart-container div[style*="font-size: 0.85em"] {
                font-size: 6.5pt !important;
                margin-top: 0.5mm !important;
            }

            /* GRIGLIA grafici - verticale anche in stampa */
            .charts-grid {
                grid-template-columns: 1fr !important;
                gap: 2mm !important;
                margin-bottom: 2mm !important;
            }
            .charts-grid .chart-container {
                margin-bottom: 0 !important;
            }
            .charts-grid .chart-container svg,
            .charts-grid .chart-container img {
                max-height: 45mm !important;
            }

            /* TABELLE - niente page-break automatici, compatte */
            .data-table {
                font-size: 6pt !important;
                width: 100% !important;
                border-collapse: collapse !important;
                margin-bottom: 2mm !important;
            }
            .data-table th {
                padding: 1mm 1.5mm !important;
                font-size: 6pt !important;
            }
            .data-table td {
                padding: 0.8mm 1.5mm !important;
            }
            h3[style*="color: var(--primary)"] {
                font-size: 8pt !important;
                margin: 2mm 0 1mm 0 !important;
            }

            /* CRITERI NEMA box */
            div[style*="background: #f8f9fa"][style*="border-left"] {
                padding: 2mm !important;
                margin-top: 2mm !important;
                font-size: 7pt !important;
            }
            div[style*="background: #f8f9fa"] h4 {
                font-size: 7.5pt !important;
                margin-bottom: 1mm !important;
            }

            /* SEZIONE DICOM ROI - compatta, 2 immagini affiancate */
            .dicom-section {
                page-break-before: avoid !important;
            }
            .dicom-roi-gallery {
                display: grid !important;
                grid-template-columns: repeat(2, 1fr) !important;
                gap: 3mm !important;
                margin-top: 2mm !important;
            }
            .dicom-roi-container {
                page-break-inside: avoid;
                padding: 2mm !important;
                border: 0.5pt solid #ccc !important;
                box-shadow: none !important;
            }
            .dicom-roi-header {
                margin-bottom: 1.5mm !important;
            }
            .dicom-roi-header h3 {
                font-size: 9pt !important;
                margin: 0 !important;
            }
            .modality-badge {
                font-size: 6.5pt !important;
                padding: 0.5mm 2mm !important;
            }
            .dicom-roi-image {
                max-width: 100% !important;
                max-height: 70mm !important;
                height: auto !important;
                width: 100% !important;
                object-fit: contain !important;
                margin: 0 auto !important;
                display: block !important;
            }
            .dicom-roi-caption {
                font-size: 7pt !important;
                margin-top: 1mm !important;
                padding: 1mm !important;
            }

            /* CONCLUSIONI */
            .section div[style*="page-break-inside:avoid"] {
                padding: 2mm !important;
            }

            /* FOOTER */
            .footer {
                margin-top: 3mm !important;
                padding: 3mm !important;
                font-size: 7pt !important;
            }
            .footer .timestamp {
                margin-top: 1mm !important;
            }

            p, li { font-size: 7.5pt !important; }
            h2 { font-size: 11pt !important; margin: 2mm 0 !important; }
            h3 { font-size: 9pt !important; }
            img { page-break-inside: avoid; }
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .summary {
                grid-template-columns: 1fr;
            }
            
            .section {
                padding: 20px;
            }
        }
        """
    
    def _generate_toolbar(self):
        """Genera toolbar con pulsante Stampa"""
        return """
    <div class="toolbar">
        <div class="toolbar-title">📊 SUV QC Report</div>
        <div class="toolbar-buttons">
            <button class="btn btn-print" onclick="window.print()">
                🖨️ Stampa Report (Ctrl+P)
            </button>
        </div>
    </div>
        """
    def _generate_header(self):
        """Genera header del report"""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        metadata = self.analyzer.acquisition_metadata or {}

        scanner_model = metadata.get('scanner_model') or 'N/A'
        study_date_raw = metadata.get('study_date') or ''
        study_time_raw = metadata.get('study_time') or ''
        activity_mbq = metadata.get('injected_activity_mbq')
        patient_weight = metadata.get('patient_weight')
        recon_diameter = metadata.get('reconstruction_diameter')
        procedure_desc = metadata.get('procedure_description') or 'N/A'
        total_dose_bq = metadata.get('total_dose_bq')

        if len(study_date_raw) == 8:
            study_date = f"{study_date_raw[6:8]}/{study_date_raw[4:6]}/{study_date_raw[0:4]}"
        else:
            study_date = study_date_raw or 'N/A'

        if len(study_time_raw) >= 6:
            study_time = f"{study_time_raw[0:2]}:{study_time_raw[2:4]}:{study_time_raw[4:6]}"
        else:
            study_time = study_time_raw[:8] if study_time_raw else 'N/A'

        activity_str = f"{activity_mbq:.1f} MBq" if activity_mbq else 'N/A'
        weight_str = f"{patient_weight:.2f} kg" if patient_weight else 'N/A'
        recon_str = f"{recon_diameter:.0f} mm" if recon_diameter else 'N/A'
        dose_str = f"{total_dose_bq / 1e6:.1f} MBq" if total_dose_bq else 'N/A'

        return f"""
        <div class="container">
            <div class="header">
                <h1>📊 SUV Quality Control Report</h1>
                <div class="subtitle">Analisi Quantitativa PET/CT</div>

                <div class="institution">
                    <div><strong>{self.config.get('department', '')}</strong></div>
                    <div>{self.config.get('institution', '')}</div>
                </div>

                <div class="metadata-separator"></div>

                <div class="metadata-grid">
                    <div><strong>Scanner:</strong> {scanner_model}</div>
                    <div><strong>Procedura:</strong> {procedure_desc}</div>

                    <div><strong>Data:</strong> {study_date}</div>
                    <div><strong>Ora:</strong> {study_time}</div>

                    <div><strong>Peso:</strong> {weight_str}</div>
                    <div><strong>Attività:</strong> {activity_str}</div>

                    <div><strong>Ricostruzione:</strong> {recon_str}</div>
                    <div><strong>Dose totale:</strong> {dose_str}</div>
                </div>

                <div class="report-timestamp">
                    Report generato: {now}
                </div>
            </div>
        """




    def _generate_summary(self):
        """Genera sezione riassuntiva"""
        # Calcola statistiche
        num_pt = len(self.pt_data)
        num_ct = len(self.ct_data)
        num_sc = len(self.secondary_captures)
        
        # Escludi prime 5 e ultime 5 fette per calcoli statistici
        pt_valid = self.pt_data[5:-5] if len(self.pt_data) > 10 else self.pt_data
        ct_valid = self.ct_data[5:-5] if len(self.ct_data) > 10 else self.ct_data
        
        avg_suv = np.mean([d['suv_mean'] for d in pt_valid]) if pt_valid else 0
        std_suv = np.std([d['suv_mean'] for d in pt_valid]) if pt_valid else 0
        
        avg_hu = np.mean([d['hu_mean'] for d in ct_valid]) if ct_valid else 0
        std_hu = np.std([d['hu_mean'] for d in ct_valid]) if ct_valid else 0
        
        # Verifica QC (usa slice valide)
        suv_in_tolerance = 0
        if pt_valid:
            for data in pt_valid:
                if (self.config['suv_tolerance_lower'] <= data['suv_mean'] / avg_suv <= 
                    self.config['suv_tolerance_upper']):
                    suv_in_tolerance += 1
        
        qc_percentage = (suv_in_tolerance / len(pt_valid) * 100) if pt_valid else 0
        
        return f"""
        <div class="summary">
            <div class="summary-card">
                <div class="label">Immagini PET</div>
                <div class="value">{num_pt}</div>
            </div>
            
            <div class="summary-card">
                <div class="label">Immagini CT</div>
                <div class="value">{num_ct}</div>
            </div>
            
            <div class="summary-card">
                <div class="label">SUV Medio</div>
                <div class="value">{avg_suv:.2f} <span style="font-size: 0.7em; opacity: 0.8;">± {std_suv:.2f}</span></div>
            </div>
            
            <div class="summary-card">
                <div class="label">HU Medio</div>
                <div class="value">{avg_hu:.1f} <span style="font-size: 0.7em; opacity: 0.8;">± {std_hu:.1f} HU</span></div>
            </div>
            
            <div class="summary-card">
                <div class="label">QC Superato</div>
                <div class="value">{qc_percentage:.1f}<span class="unit">%</span></div>
            </div>
        </div>
        """
    
    def _generate_pet_section(self):
        """Genera sezione analisi PET"""
        if not self.pt_data:
            return ""
        
        # Prepara dati per grafico - usa slice_positions se disponibili
        slice_positions = [d.get('slice_position', d['instance_number']) for d in self.pt_data]
        instance_numbers = [d['instance_number'] for d in self.pt_data]
        suv_means = [d['suv_mean'] for d in self.pt_data]
        suv_stds = [d['suv_std'] for d in self.pt_data]
        suv_maxs = [d['suv_max'] for d in self.pt_data]
        suv_mins = [d['suv_min'] for d in self.pt_data]
        
        # Calcola statistiche escludendo prime 5 e ultime 5 fette
        pt_valid = self.pt_data[5:-5] if len(self.pt_data) > 10 else self.pt_data
        suv_means_valid = [d['suv_mean'] for d in pt_valid]
        
        avg_suv = np.mean(suv_means_valid) if suv_means_valid else 0
        std_suv = np.std(suv_means_valid) if suv_means_valid else 0
        cv_suv = (std_suv / avg_suv * 100) if avg_suv > 0 else 0
        
        # Tabella dati
        table_rows = ""
        for data in self.pt_data:
            # Determina status
            ratio = data['suv_mean'] / avg_suv if avg_suv > 0 else 1
            if self.config['suv_tolerance_lower'] <= ratio <= self.config['suv_tolerance_upper']:
                status = '<span class="badge badge-success">OK</span>'
            else:
                status = '<span class="badge badge-warning">Attenzione</span>'
            
            table_rows += f"""
                <tr>
                    <td>{data['instance_number']}</td>
                    <td>{data['suv_mean']:.2f}</td>
                    <td>{data['suv_std']:.2f}</td>
                    <td>{data['suv_min']:.2f}</td>
                    <td>{data['suv_max']:.2f}</td>
                    <td>{data['suv_scale_factor']:.4f}</td>
                    <td>{status}</td>
                </tr>
            """
        
        return f"""
        <div class="section">
            <div class="section-title">
                <div class="icon">🔬</div>
                <div>Analisi PET - Standardized Uptake Values</div>
            </div>
            
            <div class="summary" style="padding: 0; margin-bottom: 30px;">
                <div class="summary-card">
                    <div class="label">SUV Medio</div>
                    <div class="value">{avg_suv:.3f}</div>
                    <div class="unit" style="font-size: 0.75em; color: #7f8c8d; margin-top: 5px;">
                        (escluse prime/ultime 5 slice)
                    </div>
                </div>
                <div class="summary-card">
                    <div class="label">Deviazione Standard</div>
                    <div class="value">{std_suv:.3f}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Coefficiente di Variazione</div>
                    <div class="value">{cv_suv:.2f}<span class="unit">%</span></div>
                </div>
            </div>
            
            <div class="charts-grid">
                <div class="chart-container">
                    <div class="chart-title">📈 Andamento SUV Mean per Slice</div>
                    {self._create_svg_plot(
                        slice_positions, suv_means,
                        'Slice Position (mm)', 'SUV Mean',
                        'SUV Mean vs Slice Position',
                        color='#3b82f6'
                    )}
                    <div style="font-size: 0.85em; color: #7f8c8d; margin-top: 8px; text-align: center;">
                        ℹ️ Statistiche calcolate escludendo le prime 5 e le ultime 5 slice
                    </div>
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">📊 Distribuzione SUV</div>
                    {self._create_svg_histogram(
                        suv_means, 'SUV Mean', 'Frequenza',
                        'Distribuzione SUV Mean',
                        bins=25, color='#10b981'
                    )}
                </div>
                
                <div class="chart-container">
                    <div class="chart-title">📊 Range SUV (Min/Max) per Slice</div>
                    {self._create_svg_scatter_range(
                        slice_positions, suv_mins, suv_maxs, suv_means,
                        'Slice Position (mm)', 'SUV',
                        'SUV Range (Min/Max/Mean)'
                    )}
                </div>
            </div>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Slice</th>
                        <th>SUV Mean</th>
                        <th>SUV Std</th>
                        <th>SUV Min</th>
                        <th>SUV Max</th>
                        <th>Scale Factor</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_ct_section(self):
        """Genera sezione analisi CT"""
        if not self.ct_data:
            return ""
        
        # Prepara dati - usa slice_positions se disponibili
        slice_positions = [d.get('slice_position', d['instance_number']) for d in self.ct_data]
        instance_numbers = [d['instance_number'] for d in self.ct_data]
        hu_means = [d['hu_mean'] for d in self.ct_data]
        hu_stds = [d['hu_std'] for d in self.ct_data]
        
        # Statistiche escludendo prime 5 e ultime 5 fette
        ct_valid = self.ct_data[5:-5] if len(self.ct_data) > 10 else self.ct_data
        hu_means_valid = [d['hu_mean'] for d in ct_valid]
        
        avg_hu = np.mean(hu_means_valid) if hu_means_valid else 0
        std_hu = np.std(hu_means_valid) if hu_means_valid else 0
        cv_hu = (std_hu / avg_hu * 100) if avg_hu > 0 else 0
        
        # Tabella
        table_rows = ""
        for data in self.ct_data:
            table_rows += f"""
                <tr>
                    <td>{data['instance_number']}</td>
                    <td>{data['hu_mean']:.1f}</td>
                    <td>{data['hu_std']:.1f}</td>
                    <td>{data['hu_min']:.1f}</td>
                    <td>{data['hu_max']:.1f}</td>
                </tr>
            """
        
        return f"""
        <div class="section">
            <div class="section-title">
                <div class="icon">🏥</div>
                <div>Analisi CT - Hounsfield Units</div>
            </div>
            
            <div class="summary" style="padding: 0; margin-bottom: 30px;">
                <div class="summary-card">
                    <div class="label">HU Medio</div>
                    <div class="value">{avg_hu:.1f}</div>
                    <div class="unit" style="font-size: 0.75em; color: #7f8c8d; margin-top: 5px;">
                        (escluse prime/ultime 5 slice)
                    </div>
                </div>
                <div class="summary-card">
                    <div class="label">Deviazione Standard</div>
                    <div class="value">{std_hu:.1f}</div>
                </div>
                <div class="summary-card">
                    <div class="label">Coefficiente di Variazione</div>
                    <div class="value">{cv_hu:.2f}<span class="unit">%</span></div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📈 Andamento HU Mean per Slice</div>
                {self._create_svg_plot(
                    slice_positions, hu_means,
                    'Slice Position (mm)', 'HU Mean',
                    'HU Mean vs Slice Position',
                    color='#ef4444',
                    y_range=(avg_hu - 100, avg_hu + 100)
                )}
                <div style="font-size: 0.85em; color: #7f8c8d; margin-top: 8px; text-align: center;">
                    ℹ️ Statistiche calcolate escludendo le prime 5 e le ultime 5 slice
                </div>
            </div>
            
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Slice</th>
                        <th>HU Mean</th>
                        <th>HU Std</th>
                        <th>HU Min</th>
                        <th>HU Max</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """
    
    def _generate_nema_pet_section(self):
        """Genera sezione analisi NEMA PET (griglia 25x25)"""
        if 'pet' not in self.nema_results:
            return ""
        
        nema_pet = self.nema_results['pet']
        slice_data = nema_pet['slice_data']
        stats = nema_pet.get('statistics', {})
        
        # Tabella dati NEMA
        table_rows = ""
        for data in slice_data:
            # Status basato su limiti
            cv_ok = data['CV'] < self.config.get('cv_ct_upper', 15.0)
            nu_ok = (self.config.get('nu_pet_lower', -15.0) < data['NUmin'] and 
                    data['NUmax'] < self.config.get('nu_pet_upper', 15.0))
            
            if cv_ok and nu_ok:
                status = '<span class="badge badge-success">OK</span>'
            elif cv_ok or nu_ok:
                status = '<span class="badge badge-warning">Parziale</span>'
            else:
                status = '<span class="badge badge-danger">Fuori Limiti</span>'
            
            table_rows += f"""
                <tr>
                    <td>{data['instance_number']}</td>
                    <td>{data['VMPmean']:.3f}</td>
                    <td>{data['SD']:.3f}</td>
                    <td>{data['CV']:.2f}</td>
                    <td>{data['NUmax']:.2f}</td>
                    <td>{data['NUmin']:.2f}</td>
                    <td>{status}</td>
                </tr>
            """
        
        # QC Summary
        qc_status = "✅ PASS" if stats.get('overall_pass', False) else "❌ FAIL"
        qc_class = "badge-success" if stats.get('overall_pass', False) else "badge-danger"
        
        return f"""
        <div class="section">
            <div class="section-title">
                <div class="icon">🔬</div>
                <div>Analisi NEMA PET - Uniformità Quantitativa (Griglia 25×25)</div>
            </div>
            
            <div class="summary" style="padding: 0; margin-bottom: 30px;">
                <div class="summary-card">
                    <div class="label">CV Medio</div>
                    <div class="value">{stats.get('cv_mean', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">CV Massimo</div>
                    <div class="value">{stats.get('cv_max', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">NU Max Medio</div>
                    <div class="value">{stats.get('nu_max_mean', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">NU Min Medio</div>
                    <div class="value">{stats.get('nu_min_mean', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">Esito QC</div>
                    <div class="value"><span class="badge {qc_class}">{qc_status}</span></div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📊 Coefficiente di Variazione e Non-Uniformità (PET)</div>
                <img src="data:image/png;base64,{nema_pet['plot_combined']}" 
                     style="width: 100%; max-width: 1200px; height: auto; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" 
                     alt="Grafici CV e NU PET">
            </div>
                       
            <div style="margin-top: 30px;">
                <h3 style="color: var(--primary); margin-bottom: 15px;">📋 Dati Dettagliati per Slice</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Slice</th>
                            <th>VMP Mean</th>
                            <th>SD</th>
                            <th>CV (%)</th>
                            <th>NU Max (%)</th>
                            <th>NU Min (%)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 5px solid var(--secondary);">
                <h4 style="margin-bottom: 10px;">ℹ️ Criteri di Accettabilità NEMA</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Coefficiente di Variazione (CV) &lt; {self.config.get('cv_ct_upper', 15.0)}%</li>
                    <li>Non-Uniformità (NU): {self.config.get('nu_pet_lower', -15.0)}% &lt; NU &lt; {self.config.get('nu_pet_upper', 15.0)}%</li>
                    <li>Valutazione esclude prime 5 e ultime 5 slices</li>
                    <li>Griglia 25×25 con celle variabili (NEMA NU 2-2012)</li>
                </ul>
            </div>
        </div>
        """
    
    def _generate_nema_ct_section(self):
        """Genera sezione analisi NEMA CT (5 cerchi)"""
        if 'ct' not in self.nema_results:
            return ""
        
        nema_ct = self.nema_results['ct']
        slice_data = nema_ct['slice_data']
        stats = nema_ct.get('statistics', {})
        
        # Tabella dati NEMA
        table_rows = ""
        for data in slice_data:
            # Status
            cv_ok = data['CV'] < self.config.get('cv_ct_upper', 15.0)
            nu_ok = (self.config.get('nu_ct_lower', -15.0) < data['NUmin'] and 
                    data['NUmax'] < self.config.get('nu_ct_upper', 15.0))
            
            if cv_ok and nu_ok:
                status = '<span class="badge badge-success">OK</span>'
            elif cv_ok or nu_ok:
                status = '<span class="badge badge-warning">Parziale</span>'
            else:
                status = '<span class="badge badge-danger">Fuori Limiti</span>'
            
            # Cerchi info
            circles = data.get('circle_means', {})
            circle_str = f"C:{circles.get('center', 0):.1f} T:{circles.get('top', 0):.1f} R:{circles.get('right', 0):.1f} B:{circles.get('bottom', 0):.1f} L:{circles.get('left', 0):.1f}"
            
            table_rows += f"""
                <tr>
                    <td>{data['instance_number']}</td>
                    <td>{data['VMPmean']:.1f}</td>
                    <td>{data['SD']:.1f}</td>
                    <td>{data['CV']:.2f}</td>
                    <td>{data['NUmax']:.2f}</td>
                    <td>{data['NUmin']:.2f}</td>
                    <td style="font-size: 0.85em;">{circle_str}</td>
                    <td>{status}</td>
                </tr>
            """
        
        # QC Summary
        qc_status = "✅ PASS" if stats.get('overall_pass', False) else "❌ FAIL"
        qc_class = "badge-success" if stats.get('overall_pass', False) else "badge-danger"
        
        return f"""
        <div class="section">
            <div class="section-title">
                <div class="icon">🏥</div>
                <div>Analisi NEMA CT - Uniformità Quantitativa (5 Cerchi Concentrici)</div>
            </div>
            
            <div class="summary" style="padding: 0; margin-bottom: 30px;">
                <div class="summary-card">
                    <div class="label">CV Medio</div>
                    <div class="value">{stats.get('cv_mean', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">CV Massimo</div>
                    <div class="value">{stats.get('cv_max', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">NU Max Medio</div>
                    <div class="value">{stats.get('nu_max_mean', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">NU Min Medio</div>
                    <div class="value">{stats.get('nu_min_mean', 0):.2f}<span class="unit">%</span></div>
                </div>
                <div class="summary-card">
                    <div class="label">Esito QC</div>
                    <div class="value"><span class="badge {qc_class}">{qc_status}</span></div>
                </div>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📊 Coefficiente di Variazione e Non-Uniformità (CT)</div>
                <img src="data:image/png;base64,{nema_ct['plot_combined']}" 
                     style="width: 100%; max-width: 1200px; height: auto; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" 
                     alt="Grafici CV e NU CT">
            </div>
            
            
            <div style="margin-top: 30px;">
                <h3 style="color: var(--primary); margin-bottom: 15px;">📋 Dati Dettagliati per Slice</h3>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Slice</th>
                            <th>VMP Mean</th>
                            <th>SD</th>
                            <th>CV (%)</th>
                            <th>NU Max (%)</th>
                            <th>NU Min (%)</th>
                            <th>Cerchi (C/T/R/B/L)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 10px; border-left: 5px solid var(--secondary);">
                <h4 style="margin-bottom: 10px;">ℹ️ Criteri di Accettabilità NEMA</h4>
                <ul style="margin: 0; padding-left: 20px;">
                    <li>Coefficiente di Variazione (CV) &lt; {self.config.get('cv_ct_upper', 15.0)}%</li>
                    <li>Non-Uniformità (NU): {self.config.get('nu_ct_lower', -15.0)}% &lt; NU &lt; {self.config.get('nu_ct_upper', 15.0)}%</li>
                    <li>Valutazione esclude prime 5 e ultime 5 slices</li>
                    <li>5 cerchi concentrici al 5% dell'area ROI (Centro, 12h, 3h, 6h, 9h)</li>
                </ul>
            </div>
        </div>
        """
    
    def _generate_secondary_captures_section(self):
        """Genera sezione secondary captures"""
        if not self.secondary_captures:
            return ""
        
        gallery_html = ""
        # Mostra solo la PRIMA secondary capture con TUTTI i frames (mosaico completo)
        if self.secondary_captures:
            sc = self.secondary_captures[0]  # Solo la prima
            for frame in sc['frames']:  # TUTTI i frame (mosaico completo)
                gallery_html += f"""
                    <div class="image-item">
                        <img src="data:image/png;base64,{frame['image_b64']}" 
                             alt="Frame {frame['frame_number']}">
                        <div class="image-caption">
                            Frame {frame['frame_number']} - {sc['study_date']}
                        </div>
                    </div>
                """
        
        return f"""
        <div class="section">
            <div class="section-title">
                <div class="icon">📸</div>
                <div>Secondary Captures - Mosaico Scanner</div>
            </div>
            
            <div class="image-gallery">
                {gallery_html}
            </div>
        </div>
        """
    
    
    def _generate_conclusions_section(self):
        """Genera sezione conclusioni normative D.Lgs 101/2020"""
        return f"""
        <!-- Conclusioni Normative -->
        <div class="section">
            <h2>📋 Conclusioni</h2>
            <div class="card card-break" style="page-break-inside:avoid">
                <p style="font-size:13px;color:#475569;margin-bottom:4px">Note:</p>
                <div contenteditable="true" style="border:1px solid #e2e8f0;border-radius:4px;
                     min-height:48px;padding:8px;font-size:13px;color:#1e293b;margin-bottom:18px"
                     data-placeholder="(inserire note)"></div>
                
                <h3 style="margin-top:24px;margin-bottom:12px">Giudizi Normativi</h3>
                
                <p style="margin-bottom:10px;font-size:13px;color:#475569">
                    Giudizio sulla qualità tecnica delle attrezzature medico-radiologiche ai sensi dell'art.163 comma 5 del D.Lgs 31.07.2020 n.101:
                </p>
                <div style="display:flex;gap:32px;margin-bottom:14px;font-size:13px">
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> adeguato
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> non adeguato
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> adeguato con limitazioni
                    </label>
                </div>
                
                <div style="display:flex;justify-content:flex-end;margin-bottom:24px">
                    <div style="text-align:center">
                        <div style="font-size:12px;color:#64748b;margin-bottom:4px">Lo Specialista in fisica medica</div>
                        <div contenteditable="true" style="border-bottom:1px solid #94a3b8;
                             min-width:220px;padding:4px 8px;font-size:13px;text-align:center;color:#1e293b"
                             data-placeholder="Nome e firma">Dr. Christian Bracco</div>
                    </div>
                </div>
                
                <p style="margin-bottom:10px;font-size:13px;color:#475569">
                    Giudizio di idoneità sull'uso clinico delle attrezzature medico-radiologiche ai sensi dell'art.163 comma 6 del D.Lgs 31.07.2020 n.101:
                </p>
                <div style="display:flex;gap:32px;margin-bottom:14px;font-size:13px">
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> idoneo
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> non idoneo
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> idoneo con limitazioni
                    </label>
                </div>
                
                <p style="margin-bottom:10px;font-size:13px;color:#475569">
                    Verifica del mantenimento dei criteri specifici di accettabilità dell'attrezzatura ai sensi dell'art.163 comma 10 del D.Lgs 31.07.2020 n.101:
                </p>
                <div style="display:flex;gap:32px;margin-bottom:18px;font-size:13px">
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> sì
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer">
                        <input type="checkbox" style="width:14px;height:14px"> no
                    </label>
                </div>
                
                <p style="font-size:13px;color:#475569;margin-bottom:4px">
                    Opportuni interventi correttivi ai sensi dell'art.163 comma 12 del D.Lgs 31.07.2020 n.101:
                </p>
                <div contenteditable="true" style="border:1px solid #e2e8f0;border-radius:4px;
                     min-height:48px;padding:8px;font-size:13px;color:#1e293b;margin-bottom:18px"
                     data-placeholder="(inserire interventi correttivi se necessari)"></div>
                
                <div style="display:flex;justify-content:space-between;align-items:flex-end;margin-top:16px">
                    <div>
                        <span style="font-size:13px;color:#475569">Data: </span>
                        <span contenteditable="true" style="border-bottom:1px solid #94a3b8;
                              min-width:120px;display:inline-block;padding:2px 8px;
                              font-size:13px;color:#1e293b">{datetime.now().strftime("%d/%m/%Y")}</span>
                    </div>
                    <div style="text-align:center">
                        <div style="font-size:12px;color:#64748b;margin-bottom:4px">Il Responsabile dell'impianto radiologico</div>
                        <div contenteditable="true" style="border-bottom:1px solid #94a3b8;
                             min-width:220px;padding:4px 8px;font-size:13px;text-align:center;color:#1e293b"
                             data-placeholder="Nome e firma"></div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    def _generate_footer(self):
        """Genera footer informativo"""
        now = datetime.now().strftime("%d/%m/%Y alle %H:%M:%S")
        
        return f"""
        <!-- Footer Informativo -->
        <div class="footer">
            <div>
                <strong>SUV Analyzer v3.3</strong> - Sistema di Analisi Quantitativa PET/CT<br>
                {self.config['department']}<br>
                {self.config['institution']}
            </div>
            <div class="timestamp" style="margin-top: 15px;">
                Report generato il {now}
            </div>
            <div style="margin-top: 15px; font-size: 0.85em; color: #7f8c8d;">
                Conforme a D.Lgs. 101/2020 | NEMA NU 2-2012 | IAEA QA Standards
            </div>
        </div>
    </div>
        """
    
    def _generate_javascript(self):
        """Genera JavaScript per PDF (i grafici sono già SVG)"""
        return """
    <script>
        // Save PDF function - Molto semplificato con grafici SVG
        async function savePDF() {
            const SERVER_URL = 'http://localhost:7860';
            
            try {
                console.log('Preparazione PDF...');
                const html = document.documentElement.outerHTML;
                console.log(`✓ HTML pronto (${(html.length / 1024).toFixed(1)} KB)`);
                
                const response = await fetch(`${SERVER_URL}/api/generate-pdf`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ html })
                });
                
                if (!response.ok) throw new Error('Errore generazione PDF');
                
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'SUV_QC_Report_' + new Date().toISOString().split('T')[0] + '.pdf';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);
                
                console.log('✓ PDF scaricato');
                
            } catch (error) {
                console.error('Errore PDF:', error);
                alert('Errore generazione PDF: ' + error.message + '\n\nVerifica che il server sia avviato (bun run server.ts)');
            }
        }
    </script>
        """




from io import BytesIO
