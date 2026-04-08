#!/usr/bin/env python3
"""
QC Database Module
Gestione database SQLite per storico Quality Control PET/CT
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
import os


class QCDatabase:
    """Database per storico QC"""
    
    def __init__(self, db_path='qc_history.db'):
        """Inizializza database"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Crea tabelle se non esistono"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabella QC sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qc_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                scanner_name TEXT,
                scanner_model TEXT,
                operator TEXT,
                pt_slices INTEGER,
                ct_slices INTEGER,
                report_html_path TEXT,
                report_json_path TEXT,
                report_pdf_path TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabella metriche PET
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qc_metrics_pt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                cv_mean REAL,
                cv_std REAL,
                cv_max REAL,
                cv_min REAL,
                nu_max_mean REAL,
                nu_min_mean REAL,
                nu_max_max REAL,
                nu_min_min REAL,
                cv_pass BOOLEAN,
                nu_pass BOOLEAN,
                overall_pass BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES qc_sessions(id)
            )
        ''')
        
        # Tabella metriche CT
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qc_metrics_ct (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                cv_mean REAL,
                cv_std REAL,
                cv_max REAL,
                cv_min REAL,
                nu_max_mean REAL,
                nu_min_mean REAL,
                nu_max_max REAL,
                nu_min_min REAL,
                cv_pass BOOLEAN,
                nu_pass BOOLEAN,
                overall_pass BOOLEAN,
                FOREIGN KEY (session_id) REFERENCES qc_sessions(id)
            )
        ''')
        
        # Tabella configurazione
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS qc_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                config_json TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES qc_sessions(id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database inizializzato: {self.db_path}")
    
    def save_qc_session(self, json_data, html_path, json_path, pdf_path=None, notes=None):
        """
        Salva sessione QC nel database
        
        Args:
            json_data: dict con risultati QC
            html_path: path al report HTML
            json_path: path al report JSON
            pdf_path: path al report PDF (opzionale)
            notes: note aggiuntive (opzionale)
            
        Returns:
            session_id: ID della sessione creata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estrai metadata
        metadata = json_data.get('metadata', {})
        acquisition = json_data.get('acquisition', {})
        data_counts = json_data.get('data_counts', {})
        nema_results = json_data.get('nema_results', {})
        config = json_data.get('configuration', {})
        
        # Inserisci sessione
        cursor.execute('''
            INSERT INTO qc_sessions (
                timestamp, scanner_name, scanner_model, operator,
                pt_slices, ct_slices,
                report_html_path, report_json_path, report_pdf_path, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata.get('timestamp', datetime.now().isoformat()),
            acquisition.get('scanner_name', 'Unknown'),
            acquisition.get('scanner_model', 'Unknown'),
            metadata.get('specialist', config.get('specialist', 'Unknown')),
            data_counts.get('pt_slices', 0),
            data_counts.get('ct_slices', 0),
            html_path,
            json_path,
            pdf_path,
            notes
        ))
        
        session_id = cursor.lastrowid
        
        # Salva metriche PET
        pt_metrics = nema_results.get('pt', {}).get('statistics', {})
        if pt_metrics:
            cursor.execute('''
                INSERT INTO qc_metrics_pt (
                    session_id, cv_mean, cv_std, cv_max, cv_min,
                    nu_max_mean, nu_min_mean, nu_max_max, nu_min_min,
                    cv_pass, nu_pass, overall_pass
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                pt_metrics.get('cv_mean', 0),
                pt_metrics.get('cv_std', 0),
                pt_metrics.get('cv_max', 0),
                pt_metrics.get('cv_min', 0),
                pt_metrics.get('nu_max_mean', 0),
                pt_metrics.get('nu_min_mean', 0),
                pt_metrics.get('nu_max_max', 0),
                pt_metrics.get('nu_min_min', 0),
                pt_metrics.get('cv_pass', False),
                pt_metrics.get('nu_pass', False),
                pt_metrics.get('overall_pass', False)
            ))
        
        # Salva metriche CT
        ct_metrics = nema_results.get('ct', {}).get('statistics', {})
        if ct_metrics:
            cursor.execute('''
                INSERT INTO qc_metrics_ct (
                    session_id, cv_mean, cv_std, cv_max, cv_min,
                    nu_max_mean, nu_min_mean, nu_max_max, nu_min_min,
                    cv_pass, nu_pass, overall_pass
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                ct_metrics.get('cv_mean', 0),
                ct_metrics.get('cv_std', 0),
                ct_metrics.get('cv_max', 0),
                ct_metrics.get('cv_min', 0),
                ct_metrics.get('nu_max_mean', 0),
                ct_metrics.get('nu_min_mean', 0),
                ct_metrics.get('nu_max_max', 0),
                ct_metrics.get('nu_min_min', 0),
                ct_metrics.get('cv_pass', False),
                ct_metrics.get('nu_pass', False),
                ct_metrics.get('overall_pass', False)
            ))
        
        # Salva configurazione
        cursor.execute('''
            INSERT INTO qc_config (session_id, config_json)
            VALUES (?, ?)
        ''', (session_id, json.dumps(config)))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Sessione QC salvata nel database: ID {session_id}")
        return session_id
    
    def get_all_sessions(self, limit=100):
        """Recupera tutte le sessioni QC"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM qc_sessions
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        sessions = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return sessions
    
    def get_session_details(self, session_id):
        """Recupera dettagli sessione con metriche"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Session info
        cursor.execute('SELECT * FROM qc_sessions WHERE id = ?', (session_id,))
        session = dict(cursor.fetchone())
        
        # PT metrics
        cursor.execute('SELECT * FROM qc_metrics_pt WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        session['pt_metrics'] = dict(row) if row else None
        
        # CT metrics
        cursor.execute('SELECT * FROM qc_metrics_ct WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        session['ct_metrics'] = dict(row) if row else None
        
        # Config
        cursor.execute('SELECT config_json FROM qc_config WHERE session_id = ?', (session_id,))
        row = cursor.fetchone()
        session['config'] = json.loads(row['config_json']) if row else None
        
        conn.close()
        
        return session
    
    def get_trend_data(self, metric='cv_mean', modality='pt', limit=50):
        """
        Recupera dati trend per grafici
        
        Args:
            metric: metrica da tracciare (cv_mean, nu_max_mean, etc)
            modality: 'pt' o 'ct'
            limit: numero sessioni
            
        Returns:
            list di (timestamp, value)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        table = f'qc_metrics_{modality}'
        
        cursor.execute(f'''
            SELECT s.timestamp, m.{metric}
            FROM qc_sessions s
            JOIN {table} m ON s.id = m.session_id
            ORDER BY s.timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        data = [(row['timestamp'], row[metric]) for row in cursor.fetchall()]
        conn.close()
        
        # Inverti ordine per grafico cronologico
        return list(reversed(data))
    
    def export_to_json(self, output_path='qc_history_export.json'):
        """Esporta tutto il database in JSON"""
        sessions = self.get_all_sessions(limit=9999)
        
        # Aggiungi dettagli per ogni sessione
        for session in sessions:
            session_id = session['id']
            details = self.get_session_details(session_id)
            session.update(details)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Database esportato in: {output_path}")
        return output_path


# ============================================================================
# CLI per gestione database
# ============================================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestione Database QC')
    parser.add_argument('action', choices=['init', 'list', 'export', 'trends'],
                       help='Azione da eseguire')
    parser.add_argument('--db', default='qc_history.db',
                       help='Path database SQLite')
    parser.add_argument('--limit', type=int, default=50,
                       help='Limite risultati')
    parser.add_argument('--metric', default='cv_mean',
                       help='Metrica per trends')
    parser.add_argument('--modality', choices=['pt', 'ct'], default='pt',
                       help='Modalità per trends')
    
    args = parser.parse_args()
    
    db = QCDatabase(args.db)
    
    if args.action == 'init':
        print("✅ Database inizializzato")
    
    elif args.action == 'list':
        sessions = db.get_all_sessions(limit=args.limit)
        print(f"\n📋 Ultime {len(sessions)} sessioni QC:\n")
        for s in sessions:
            status = "✅ PASS" if s.get('overall_pass') else "❌ FAIL"
            print(f"  [{s['id']}] {s['timestamp'][:16]} - {s['scanner_name']} - {status}")
    
    elif args.action == 'export':
        output = f"qc_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        db.export_to_json(output)
    
    elif args.action == 'trends':
        trend_data = db.get_trend_data(
            metric=args.metric,
            modality=args.modality,
            limit=args.limit
        )
        print(f"\n📈 Trend {args.metric} ({args.modality.upper()}):\n")
        for timestamp, value in trend_data:
            print(f"  {timestamp[:16]}: {value:.2f}")
