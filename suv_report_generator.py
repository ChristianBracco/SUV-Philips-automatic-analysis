"""
SUV HTML Report Generator
Genera report HTML professionali con grafici interattivi e analisi statistiche
"""

import json
from datetime import datetime
import base64
import numpy as np


class HTMLReportGenerator:
    """Generatore report HTML per analisi SUV"""
    
    def __init__(self, analyzer, nema_results=None):
        self.analyzer = analyzer
        self.pt_data = analyzer.pt_data
        self.ct_data = analyzer.ct_data
        self.secondary_captures = analyzer.secondary_captures
        self.config = analyzer.config
        self.nema_results = nema_results or {}
    
    def generate(self):
        """Genera report HTML completo"""
        html = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SUV Quality Control Report</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
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
            margin: 15mm;
        }
        
        @media print {
            @page {
                size: A4 portrait;
                margin: 12mm 10mm;
            }
            
            * {
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
            }
            
            body {
                background: white !important;
                padding: 0 !important;
                margin: 0 !important;
                font-size: 9pt !important;
                line-height: 1.3 !important;
            }
            
            .toolbar {
                display: none !important;
            }
            
            .container {
                box-shadow: none !important;
                max-width: 100% !important;
                margin: 0 !important;
                padding: 0 !important;
                background: white !important;
                border-radius: 0 !important;
            }
            
            /* HEADER COMPATTO */
            .header {
                page-break-after: avoid;
                page-break-inside: avoid;
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%) !important;
                padding: 10mm 6mm !important;
                margin-bottom: 4mm !important;
            }
            
            .header h1 {
                font-size: 16pt !important;
                margin: 0 0 3mm 0 !important;
            }
            
            .header .subtitle {
                font-size: 10pt !important;
                margin: 0 !important;
            }
            
            .header .institution {
                margin-top: 4mm !important;
                padding: 4mm !important;
                font-size: 9pt !important;
            }
            
            .header::before {
                display: none !important;
            }
            
            /* SUMMARY CARDS 3 COLONNE */
            .summary {
                page-break-inside: avoid;
                grid-template-columns: repeat(3, 1fr) !important;
                padding: 4mm !important;
                gap: 3mm !important;
                margin-bottom: 4mm !important;
            }
            
            .summary-card {
                padding: 3mm !important;
                margin: 0 !important;
            }
            
            .summary-card .label {
                font-size: 8pt !important;
                margin-bottom: 2mm !important;
            }
            
            .summary-card .value {
                font-size: 14pt !important;
            }
            
            .summary-card .unit {
                font-size: 10pt !important;
            }
            
            /* SEZIONI */
            .section {
                page-break-before: auto;
                page-break-inside: avoid;
                margin-bottom: 5mm !important;
                padding: 0 4mm !important;
            }
            
            .section-title {
                page-break-after: avoid;
                font-size: 11pt !important;
                padding: 3mm !important;
                margin-bottom: 3mm !important;
            }
            
            .section-title .icon {
                width: 24px !important;
                height: 24px !important;
                font-size: 11pt !important;
            }
            
            /* GRAFICI - RIDUCI SOLO ALTEZZA MASSIMA */
            .chart-container {
                page-break-inside: avoid;
                margin-bottom: 4mm !important;
                padding: 3mm !important;
            }
            
            .chart-title {
                font-size: 10pt !important;
                margin-bottom: 3mm !important;
            }
            
            .chart-container img {
                max-width: 100% !important;
                height: auto !important;
                max-height: 80mm !important;
            }
            
            /* TABELLE */
            .data-table {
                page-break-inside: auto;
                font-size: 7pt !important;
                margin-bottom: 4mm !important;
            }
            
            .data-table th {
                padding: 2mm 3mm !important;
                font-size: 7pt !important;
            }
            
            .data-table td {
                padding: 1mm 3mm !important;
                font-size: 7pt !important;
                line-height: 1.2 !important;
            }
            
            .data-table thead {
                background: linear-gradient(135deg, #2c3e50, #3498db) !important;
            }
            
            /* CARD */
            .card {
                padding: 4mm !important;
                margin-bottom: 4mm !important;
            }
            
            /* FOOTER */
            .footer {
                page-break-before: auto;
                margin-top: 5mm !important;
                padding: 3mm 4mm !important;
                font-size: 7pt !important;
                border-top: 1px solid #ccc !important;
            }
            
            /* EVITA BREAK IMMAGINI */
            img {
                page-break-inside: avoid;
                page-break-after: avoid;
            }
            
            /* CONCLUSIONI */
            h2 {
                font-size: 12pt !important;
                margin: 3mm 0 !important;
            }
            
            h3 {
                font-size: 10pt !important;
                margin: 2mm 0 !important;
            }
            
            p, li {
                font-size: 8pt !important;
                line-height: 1.3 !important;
                margin: 1mm 0 !important;
            }
            
            ul {
                margin: 2mm 0 !important;
                padding-left: 5mm !important;
            }
            
            input[type="text"],
            input[type="date"],
            input[type="checkbox"] {
                border: 1px solid #999 !important;
                padding: 1mm !important;
                font-size: 8pt !important;
            }
            
            label {
                font-size: 8pt !important;
            }
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
        """Genera toolbar con pulsanti Print e PDF"""
        return """
    <div class="toolbar">
        <div class="toolbar-title">📊 SUV QC Report</div>
        <div class="toolbar-buttons">
            <button class="btn btn-print" onclick="window.print()">
                🖨️ Stampa
            </button>
            <button class="btn btn-pdf" onclick="savePDF()">
                📄 Salva PDF
            </button>
        </div>
    </div>
        """
    
    def _generate_header(self):
        """Genera header del report"""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # Estrai metadata acquisizione
        metadata = self.analyzer.acquisition_metadata
        institution = metadata.get('institution', 'Unknown') if metadata else 'Unknown'
        study_date_raw = metadata.get('study_date', '') if metadata else ''
        study_time_raw = metadata.get('study_time', '') if metadata else ''
        activity_mbq = metadata.get('injected_activity_mbq', None) if metadata else None
        
        # Formatta data DICOM (YYYYMMDD -> DD/MM/YYYY)
        if study_date_raw and len(study_date_raw) == 8:
            study_date = f"{study_date_raw[6:8]}/{study_date_raw[4:6]}/{study_date_raw[0:4]}"
        else:
            study_date = study_date_raw or 'N/A'
        
        # Formatta ora DICOM (HHMMSS.ffffff -> HH:MM:SS)
        if study_time_raw and len(study_time_raw) >= 6:
            study_time = f"{study_time_raw[0:2]}:{study_time_raw[2:4]}:{study_time_raw[4:6]}"
        else:
            study_time = study_time_raw[:8] if study_time_raw else 'N/A'
        
        # Formatta attività
        if activity_mbq is not None:
            activity_str = f"{activity_mbq:.1f} MBq"
        else:
            activity_str = 'N/A'
        
        return f"""
    <div class="container">
        <div class="header">
            <h1>📊 SUV Quality Control Report</h1>
            <div class="subtitle">Analisi Quantitativa PET/CT - Controllo di Qualità</div>
            <div class="institution">
                <div><strong>{self.config['department']}</strong></div>
                <div>{self.config['institution']}</div>
                <div>Responsabile: {self.config['specialist']}</div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 0.9em;">
                        <div><strong>Ospedale:</strong> {institution}</div>
                        <div><strong>Data acquisizione:</strong> {study_date}</div>
                        <div><strong>Ora scansione:</strong> {study_time}</div>
                        <div><strong>Attività:</strong> {activity_str}</div>
                    </div>
                </div>
                <div style="margin-top: 10px; opacity: 0.8; font-size: 0.85em;">Report generato: {now}</div>
            </div>
        </div>
        """
    
    def _generate_summary(self):
        """Genera sezione riassuntiva"""
        # Calcola statistiche
        num_pt = len(self.pt_data)
        num_ct = len(self.ct_data)
        num_sc = len(self.secondary_captures)
        
        avg_suv = np.mean([d['suv_mean'] for d in self.pt_data]) if self.pt_data else 0
        avg_hu = np.mean([d['hu_mean'] for d in self.ct_data]) if self.ct_data else 0
        
        # Verifica QC
        suv_in_tolerance = 0
        if self.pt_data:
            for data in self.pt_data:
                if (self.config['suv_tolerance_lower'] <= data['suv_mean'] / avg_suv <= 
                    self.config['suv_tolerance_upper']):
                    suv_in_tolerance += 1
        
        qc_percentage = (suv_in_tolerance / num_pt * 100) if num_pt > 0 else 0
        
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
                <div class="value">{avg_suv:.2f}<span class="unit"></span></div>
            </div>
            
            <div class="summary-card">
                <div class="label">HU Medio</div>
                <div class="value">{avg_hu:.1f}<span class="unit">HU</span></div>
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
        
        # Prepara dati per grafico
        instance_numbers = [d['instance_number'] for d in self.pt_data]
        suv_means = [d['suv_mean'] for d in self.pt_data]
        suv_stds = [d['suv_std'] for d in self.pt_data]
        suv_maxs = [d['suv_max'] for d in self.pt_data]
        suv_mins = [d['suv_min'] for d in self.pt_data]
        
        # Calcola statistiche
        avg_suv = np.mean(suv_means)
        std_suv = np.std(suv_means)
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
            
            <div class="chart-container">
                <div class="chart-title">📈 Andamento SUV Mean per Slice</div>
                <canvas id="chartSUVMean"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📊 Distribuzione SUV</div>
                <canvas id="chartSUVDistribution"></canvas>
            </div>
            
            <div class="chart-container">
                <div class="chart-title">📊 Range SUV (Min/Max) per Slice</div>
                <canvas id="chartSUVRange"></canvas>
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
        
        <script>
            const ptData = {{
                instances: {json.dumps(instance_numbers)},
                suvMeans: {json.dumps(suv_means)},
                suvStds: {json.dumps(suv_stds)},
                suvMins: {json.dumps(suv_mins)},
                suvMaxs: {json.dumps(suv_maxs)}
            }};
        </script>
        """
    
    def _generate_ct_section(self):
        """Genera sezione analisi CT"""
        if not self.ct_data:
            return ""
        
        # Prepara dati
        instance_numbers = [d['instance_number'] for d in self.ct_data]
        hu_means = [d['hu_mean'] for d in self.ct_data]
        hu_stds = [d['hu_std'] for d in self.ct_data]
        
        # Statistiche
        avg_hu = np.mean(hu_means)
        std_hu = np.std(hu_means)
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
                <canvas id="chartHUMean"></canvas>
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
        
        <script>
            const ctData = {{
                instances: {json.dumps(instance_numbers)},
                huMeans: {json.dumps(hu_means)},
                huStds: {json.dumps(hu_stds)}
            }};
        </script>
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
            
            <div class="chart-container">
                <div class="chart-title">🎯 Esempio Griglia 25×25 ROI</div>
                <img src="data:image/png;base64,{nema_pet.get('plot_example', '')}" 
                     style="width: 100%; max-width: 800px; height: auto; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" 
                     alt="Esempio griglia PET">
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
            
            <div class="chart-container">
                <div class="chart-title">🎯 Esempio 5 Cerchi Concentrici ROI</div>
                <img src="data:image/png;base64,{nema_ct.get('plot_example', '')}" 
                     style="width: 100%; max-width: 800px; height: auto; image-rendering: -webkit-optimize-contrast; image-rendering: crisp-edges;" 
                     alt="Esempio cerchi CT">
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
        """Genera JavaScript per grafici interattivi"""
        return """
    <script>
        // Configurazione Chart.js
        Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
        Chart.defaults.color = '#2c3e50';
        
        // Grafico SUV Mean
        if (typeof ptData !== 'undefined') {
            const ctxSUVMean = document.getElementById('chartSUVMean').getContext('2d');
            new Chart(ctxSUVMean, {
                type: 'line',
                data: {
                    labels: ptData.instances,
                    datasets: [{
                        label: 'SUV Mean',
                        data: ptData.suvMeans,
                        borderColor: '#3498db',
                        backgroundColor: 'rgba(52, 152, 219, 0.1)',
                        borderWidth: 3,
                        pointRadius: 5,
                        pointBackgroundColor: '#3498db',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.0,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        title: {
                            display: false
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12,
                            titleFont: {
                                size: 14
                            },
                            bodyFont: {
                                size: 13
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grace: '10%',
                            title: {
                                display: true,
                                text: 'SUV ()',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                padding: 8
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Instance Number',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        }
                    }
                }
            });
            
            // Grafico Distribuzione SUV (Istogramma)
            const ctxSUVDist = document.getElementById('chartSUVDistribution').getContext('2d');
            // Crea istogramma da tutti i valori SUV mean
            const allSUVs = ptData.suvMeans;
            const minSUV = Math.min(...allSUVs);
            const maxSUV = Math.max(...allSUVs);
            const numBins = 20;
            const binWidth = (maxSUV - minSUV) / numBins;
            
            // Calcola bins
            const bins = new Array(numBins).fill(0);
            const binLabels = [];
            for (let i = 0; i < numBins; i++) {
                const binStart = minSUV + i * binWidth;
                const binEnd = binStart + binWidth;
                binLabels.push(binStart.toFixed(2));
                
                // Conta valori in questo bin
                allSUVs.forEach(suv => {
                    if (suv >= binStart && suv < binEnd) {
                        bins[i]++;
                    }
                });
            }
            
            new Chart(ctxSUVDist, {
                type: 'bar',
                data: {
                    labels: binLabels,
                    datasets: [{
                        label: 'Frequenza',
                        data: bins,
                        backgroundColor: 'rgba(231, 76, 60, 0.7)',
                        borderColor: '#e74c3c',
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.0,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        tooltip: {
                            backgroundColor: 'rgba(0, 0, 0, 0.8)',
                            padding: 12
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grace: '5%',
                            title: {
                                display: true,
                                text: 'Frequenza',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                padding: 8
                            },
                            grid: {
                                color: 'rgba(0, 0, 0, 0.05)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'SUV',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            grid: {
                                display: false
                            }
                        }
                    }
                }
            });
            
            // Grafico SUV Range
            const ctxSUVRange = document.getElementById('chartSUVRange').getContext('2d');
            new Chart(ctxSUVRange, {
                type: 'line',
                data: {
                    labels: ptData.instances,
                    datasets: [
                        {
                            label: 'SUV Max',
                            data: ptData.suvMaxs,
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)',
                            borderWidth: 2,
                            pointRadius: 4,
                            tension: 0.4
                        },
                        {
                            label: 'SUV Mean',
                            data: ptData.suvMeans,
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            borderWidth: 3,
                            pointRadius: 5,
                            tension: 0.4
                        },
                        {
                            label: 'SUV Min',
                            data: ptData.suvMins,
                            borderColor: '#27ae60',
                            backgroundColor: 'rgba(39, 174, 96, 0.1)',
                            borderWidth: 2,
                            pointRadius: 4,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.0,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: false,
                            grace: '10%',
                            title: {
                                display: true,
                                text: 'SUV ()',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                padding: 8
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Instance Number',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Grafico HU Mean
        if (typeof ctData !== 'undefined') {
            const ctxHUMean = document.getElementById('chartHUMean').getContext('2d');
            new Chart(ctxHUMean, {
                type: 'line',
                data: {
                    labels: ctData.instances,
                    datasets: [{
                        label: 'HU Mean',
                        data: ctData.huMeans,
                        borderColor: '#9b59b6',
                        backgroundColor: 'rgba(155, 89, 182, 0.1)',
                        borderWidth: 3,
                        pointRadius: 5,
                        pointBackgroundColor: '#9b59b6',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    aspectRatio: 2.0,
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        y: {
                            grace: '10%',
                            title: {
                                display: true,
                                text: 'Hounsfield Units (HU)',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            },
                            ticks: {
                                padding: 8
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Instance Number',
                                font: {
                                    size: 14,
                                    weight: 'bold'
                                }
                            }
                        }
                    }
                }
            });
        }
        
        // Save PDF function
        function savePDF() {
            const element = document.querySelector('.container');
            const opt = {
                margin: 10,
                filename: 'SUV_QC_Report_' + new Date().toISOString().split('T')[0] + '.pdf',
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };
            html2pdf().set(opt).from(element).save();
        }
    </script>
        """


from io import BytesIO
