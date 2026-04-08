/**
 * SUV Analyzer - Bun Server
 * Backend server per interfaccia web HTML/JS
 */

import { serve } from "bun";
import { readdir, stat, mkdir, writeFile } from "fs/promises";
import { join, extname } from "path";
import { spawn } from "child_process";
import { tmpdir } from "os";

const PORT = 7860;
const UPLOAD_DIR = join(tmpdir(), 'suv-analyzer-uploads');

// MIME types
const MIME_TYPES: Record<string, string> = {
  '.html': 'text/html',
  '.js': 'application/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon'
};

// Helper: esegui script Python
async function runPython(script: string, args: string[] = []): Promise<any> {
  return new Promise((resolve, reject) => {
    const pythonProcess = spawn('python3', [script, ...args]);
    
    let stdout = '';
    let stderr = '';
    
    pythonProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    pythonProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    pythonProcess.on('close', (code) => {
      if (code === 0) {
        try {
          // Prova parsing diretto
          resolve(JSON.parse(stdout));
        } catch {
          // Se fallisce, cerca l'ultima riga che sembra JSON
          const lines = stdout.trim().split('\n');
          for (let i = lines.length - 1; i >= 0; i--) {
            const line = lines[i].trim();
            if (line.startsWith('{') || line.startsWith('[')) {
              try {
                resolve(JSON.parse(line));
                return;
              } catch {
                // Non è JSON valido, continua
              }
            }
          }
          // Nessun JSON trovato, ritorna output grezzo
          resolve({ output: stdout });
        }
      } else {
        reject(new Error(stderr || 'Python script failed'));
      }
    });
    
    pythonProcess.on('error', (err) => {
      reject(err);
    });
  });
}

// Server Bun
serve({
  port: PORT,
  
  async fetch(req) {
    const url = new URL(req.url);
    const path = url.pathname;
    
    console.log(`${req.method} ${path}`);
    
    // ============================================================
    // API ENDPOINTS
    // ============================================================
    
    // POST /api/upload-dicom
    if (path === '/api/upload-dicom' && req.method === 'POST') {
      try {
        const formData = await req.formData();
        const files = formData.getAll('files') as File[];
        
        if (files.length === 0) {
          return new Response(JSON.stringify({ error: 'No files uploaded' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' }
          });
        }
        
        // Create upload directory with timestamp
        const timestamp = Date.now();
        const uploadPath = join(UPLOAD_DIR, `upload_${timestamp}`);
        await mkdir(uploadPath, { recursive: true });
        
        // Save all files
        for (const file of files) {
          const buffer = await file.arrayBuffer();
          const filePath = join(uploadPath, file.name);
          await writeFile(filePath, Buffer.from(buffer));
        }
        
        // Scan uploaded folder
        const result = await runPython('api_scan_folder.py', [uploadPath]);
        result.uploadPath = uploadPath;
        
        return new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json' }
        });
        
      } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    
    // GET /api/scan-folder?path=...
    if (path === '/api/scan-folder' && req.method === 'GET') {
      try {
        const folderPath = url.searchParams.get('path');
        
        if (!folderPath) {
          return new Response(JSON.stringify({ error: 'Missing path parameter' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' }
          });
        }
        
        // Chiama Python script per scan
        const result = await runPython('api_scan_folder.py', [folderPath]);
        
        return new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json' }
        });
        
      } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    
    // POST /api/load-series
    if (path === '/api/load-series' && req.method === 'POST') {
      try {
        const body = await req.json();
        const { seriesUid, folderPath } = body;
        
        // Chiama Python per caricare serie
        const result = await runPython('api_load_series.py', [
          folderPath,
          seriesUid
        ]);
        
        return new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json' }
        });
        
      } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    
    // POST /api/analyze
    if (path === '/api/analyze' && req.method === 'POST') {
      try {
        const body = await req.json();
        let { folderPath, folderPaths } = body;
        
        // Supporta sia folderPath singolo che folderPaths array
        if (folderPath && !folderPaths) {
          folderPaths = [folderPath];
        }
        
        if (!folderPaths || folderPaths.length === 0) {
          return new Response(JSON.stringify({ error: 'Missing folderPath or folderPaths' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json' }
          });
        }
        
        // Analizza ogni cartella e unisci i risultati
        // Per ora passiamo solo la prima (backward compatibility)
        // TODO: modificare api_analyze.py per gestire array
        const result = await runPython('api_analyze.py', folderPaths);
        
        return new Response(JSON.stringify(result), {
          headers: { 'Content-Type': 'application/json' }
        });
        
      } catch (error: any) {
        return new Response(JSON.stringify({ error: error.message }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' }
        });
      }
    }
    
    // ============================================================
    // STATIC FILES
    // ============================================================
    
    // Root → index.html
    if (path === '/' || path === '/index.html') {
      const file = Bun.file('public/index.html');
      if (await file.exists()) {
        return new Response(file, {
          headers: { 'Content-Type': 'text/html' }
        });
      }
    }
    
    // Serve static files from public/
    try {
      // Remove leading slash
      const cleanPath = path.startsWith('/') ? path.slice(1) : path;
      const filePath = join('public', cleanPath);
      const file = Bun.file(filePath);
      
      console.log(`  Looking for: ${filePath}`);
      
      if (await file.exists()) {
        const ext = extname(filePath);
        const contentType = MIME_TYPES[ext] || 'application/octet-stream';
        
        console.log(`  ✓ Found: ${filePath} (${contentType})`);
        
        return new Response(file, {
          headers: { 'Content-Type': contentType }
        });
      } else {
        console.log(`  ✗ Not found: ${filePath}`);
      }
    } catch (error) {
      console.error(`  Error: ${error}`);
    }
    
    // 404
    return new Response('Not Found', { status: 404 });
  }
});

console.log('');
console.log('═══════════════════════════════════════════════');
console.log('  SUV Analyzer - Bun Server');
console.log('═══════════════════════════════════════════════');
console.log('');
console.log(`  🚀 Server running on http://localhost:${PORT}`);
console.log(`  📁 Static files: ./public/`);
console.log(`  🐍 Python backend: ./api_*.py`);
console.log('');
console.log('  Press Ctrl+C to stop');
console.log('');
