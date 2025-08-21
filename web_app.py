from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import os
import time
from datetime import datetime

app = FastAPI(title="Troubleshooting Agent")

# Variables globales pour les logs
diagnostic_logs = []
diagnostic_running = False

class DiagnosticRequest(BaseModel):
    app_path: str

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Troubleshooting Agent</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 1000px; 
                margin: 20px auto; 
                padding: 20px; 
            }
            .container {
                display: grid;
                grid-template-columns: 350px 1fr;
                gap: 20px;
            }
            .sidebar {
                border-right: 1px solid #ccc;
                padding-right: 20px;
            }
            .main-content {
                text-align: center;
            }
            button { 
                background-color: #007bff; 
                color: white; 
                border: none; 
                padding: 10px 15px; 
                margin: 5px;
                border-radius: 5px; 
                cursor: pointer; 
                font-size: 14px;
                width: 100%;
            }
            button:hover { background-color: #0056b3; }
            button.secondary { background-color: #6c757d; }
            button.secondary:hover { background-color: #545b62; }
            
            .current-path {
                background-color: #e9ecef;
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                font-family: monospace;
                font-size: 12px;
                word-break: break-all;
            }
            
            .file-browser {
                background-color: #f8f9fa;
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
                height: 400px;
                overflow-y: auto;
            }
            
            .dir-item, .file-item {
                padding: 8px;
                margin: 2px 0;
                cursor: pointer;
                border-radius: 3px;
                border: 1px solid transparent;
            }
            .dir-item:hover, .file-item:hover {
                background-color: #e9ecef;
            }
            .dir-item {
                font-weight: bold;
                color: #007bff;
            }
            .selected {
                background-color: #007bff;
                color: white;
            }
            
            .result {
                margin: 20px 0;
                padding: 15px;
                background-color: #f8f9fa;
                border-radius: 5px;
                text-align: left;
            }
        </style>
    </head>
    <body>
        <h1>Troubleshooting Agent - Version 2</h1>
        
        <div class="container">
            <!-- Sidebar avec explorateur -->
            <div class="sidebar">
                <h3>Explorateur de fichiers</h3>
                
                <div class="current-path" id="currentPath">
                    Chargement...
                </div>
                
                <button onclick="goUp()" class="secondary">Dossier parent</button>
                <button onclick="refreshBrowser()" class="secondary">Actualiser</button>
                
                <div class="file-browser" id="fileBrowser">
                    Chargement des dossiers...
                </div>
                
                <h3>Actions</h3>
                <button onclick="selectCurrentFolder()">Selectionner ce dossier</button>
                <button onclick="startDiagnostic()" id="startBtn">Lancer le diagnostic</button>
                <button onclick="testConnection()">Test de connexion</button>
            </div>
            
            <!-- Zone principale -->
            <div class="main-content">
                <h2>Dossier selectionne</h2>
                <div id="selectedPath" class="current-path">
                    Aucun dossier selectionne
                </div>
                
                <div id="status" class="result" style="display: none;">
                    Statut: Pret
                </div>
                
                <h2>Logs du diagnostic</h2>
                <div id="logs" class="result" style="display: block; height: 300px; overflow-y: auto; font-family: monospace; white-space: pre-wrap;">
                    Aucun diagnostic en cours...
                </div>
            </div>
        </div>

        <script>
            var currentPath = "C:/Users/latif/OneDrive/Desktop";
            var selectedPath = null;
            
            // Charger au demarrage
            window.onload = function() {
                loadDirectory(currentPath);
            };
            
            // Navigation dans les dossiers
            function loadDirectory(path) {
                fetch('/browse?path=' + encodeURIComponent(path))
                    .then(function(response) {
                        return response.json();
                    })
                    .then(function(data) {
                        if (data.error) {
                            alert('Erreur: ' + data.error);
                            return;
                        }
                        
                        currentPath = data.current_path;
                        document.getElementById('currentPath').textContent = currentPath;
                        
                        var browser = document.getElementById('fileBrowser');
                        browser.innerHTML = '';
                        
                        // Ajouter les dossiers
                        for (var i = 0; i < data.directories.length; i++) {
                            var dir = data.directories[i];
                            var item = document.createElement('div');
                            item.className = 'dir-item';
                            item.textContent = '[DIR] ' + dir;
                            item.setAttribute('data-dir', dir);
                            item.onclick = function() {
                                var separator = currentPath.endsWith('/') ? '' : '/';
                                var newPath = currentPath + separator + this.getAttribute('data-dir');
                                loadDirectory(newPath);
                            };
                            browser.appendChild(item);
                        }
                        
                        // Ajouter les fichiers (juste pour affichage)
                        for (var j = 0; j < data.files.length; j++) {
                            var file = data.files[j];
                            var item = document.createElement('div');
                            item.className = 'file-item';
                            item.textContent = '[FILE] ' + file;
                            browser.appendChild(item);
                        }
                        
                        if (data.directories.length === 0 && data.files.length === 0) {
                            browser.innerHTML = '<p style="color: #666;">Dossier vide</p>';
                        }
                    })
                    .catch(function(error) {
                        console.error('Erreur:', error);
                        alert('Erreur de navigation: ' + error.message);
                    });
            }
            
            function goUp() {
                console.log('goUp() clique, currentPath:', currentPath);
                
                // Simple: chercher le dernier separateur
                var lastSlash = Math.max(currentPath.lastIndexOf('/'), currentPath.lastIndexOf('\\\\'));
                
                if (lastSlash > 0) {
                    var parentPath = currentPath.substring(0, lastSlash);
                    console.log('Remontee vers:', parentPath);
                    loadDirectory(parentPath);
                } else {
                    console.log('Deja a la racine');
                    alert('Deja a la racine du systeme');
                }
            }
            
            function refreshBrowser() {
                loadDirectory(currentPath);
            }
            
            function selectCurrentFolder() {
                selectedPath = currentPath;
                document.getElementById('selectedPath').textContent = selectedPath;
                
                // Visual feedback
                document.getElementById('status').style.display = 'block';
                document.getElementById('status').textContent = 'Dossier selectionne: ' + selectedPath;
            }
            
            function startDiagnostic() {
                if (!selectedPath) {
                    alert('Veuillez selectionner un dossier');
                    return;
                }
                
                document.getElementById('startBtn').disabled = true;
                document.getElementById('status').style.display = 'block';
                document.getElementById('status').textContent = 'Diagnostic en cours...';
                document.getElementById('logs').textContent = 'Demarrage du diagnostic...';
                
                // Demarrer l'actualisation des logs
                updateLogs();
                var logsInterval = setInterval(function() {
                    updateLogs();
                }, 2000);
                
                fetch('/start-diagnostic', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({app_path: selectedPath})
                })
                .then(function(response) { return response.json(); })
                .then(function(result) {
                    if (result.error) {
                        throw new Error(result.error);
                    }
                    document.getElementById('status').textContent = 'Diagnostic demarre!';
                })
                .catch(function(error) {
                    document.getElementById('status').textContent = 'Erreur: ' + error.message;
                    document.getElementById('startBtn').disabled = false;
                    clearInterval(logsInterval);
                });
            }
            
            function updateLogs() {
                fetch('/logs')
                    .then(function(response) { return response.json(); })
                    .then(function(data) {
                        if (data.logs && data.logs.length > 0) {
                            document.getElementById('logs').textContent = data.logs.join('\\n');
                            
                            // Scroll automatique vers le bas
                            var logsEl = document.getElementById('logs');
                            logsEl.scrollTop = logsEl.scrollHeight;
                        }
                        
                        // Mettre a jour le statut si le diagnostic est termine
                        if (data.status === 'completed') {
                            document.getElementById('status').textContent = 'Diagnostic termine!';
                            document.getElementById('startBtn').disabled = false;
                        }
                    })
                    .catch(function(error) {
                        console.error('Erreur actualisation logs:', error);
                    });
            }
            
            function testConnection() {
                document.getElementById('status').style.display = 'block';
                document.getElementById('status').textContent = 'Test en cours...';
                
                fetch('/test')
                    .then(function(response) {
                        return response.json();
                    })
                    .then(function(data) {
                        document.getElementById('status').textContent = 
                            'Connexion reussie! Message: ' + data.message +
                            (selectedPath ? ' - Dossier selectionne: ' + selectedPath : '');
                    })
                    .catch(function(error) {
                        document.getElementById('status').textContent = 'Erreur: ' + error.message;
                    });
            }
        </script>
    </body>
    </html>
    """

@app.get("/browse")
async def browse_directory(path: str = "."):
    """API pour naviguer dans les dossiers"""
    try:
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            return JSONResponse({"error": "Chemin inexistant"}, status_code=400)
        
        if not os.path.isdir(path):
            return JSONResponse({"error": "Ce n'est pas un dossier"}, status_code=400)
        
        items = os.listdir(path)
        directories = []
        files = []
        
        for item in sorted(items):
            item_path = os.path.join(path, item)
            try:
                if os.path.isdir(item_path):
                    directories.append(item)
                else:
                    files.append(item)
            except PermissionError:
                # Ignorer les fichiers sans permission
                continue
        
        return {
            "current_path": path,
            "directories": directories,
            "files": files[:10]  # Limiter a 10 fichiers pour pas surcharger
        }
        
    except PermissionError:
        return JSONResponse({"error": "Permissions insuffisantes"}, status_code=403)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/start-diagnostic")
async def start_diagnostic(request: DiagnosticRequest, background_tasks: BackgroundTasks):
    """Demarrer un diagnostic (simulation pour l'etape 3)"""
    global diagnostic_running, diagnostic_logs
    
    if diagnostic_running:
        return JSONResponse({"error": "Un diagnostic est deja en cours"}, status_code=400)
    
    diagnostic_running = True
    diagnostic_logs = [f"[{datetime.now().strftime('%H:%M:%S')}] Diagnostic demarre pour: {request.app_path}"]
    
    # Lancer le vrai diagnostic en arriere-plan
    background_tasks.add_task(run_real_diagnostic, request.app_path)
    
    return {"status": "started", "message": "Diagnostic demarre"}

def run_real_diagnostic(app_path: str):
    """Executer le vrai agent de troubleshooting"""
    global diagnostic_running, diagnostic_logs
    
    try:
        import subprocess
        import sys
        import threading
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        diagnostic_logs.append(f"[{timestamp}] Demarrage du diagnostic pour: {app_path}")
        
        # Preparer l'environnement avec le chemin cible
        env = os.environ.copy()
        env['TARGET_APP_PATH'] = app_path
        
        diagnostic_logs.append(f"[{timestamp}] Lancement de main.py...")
        
        # Executer main.py avec capture des sorties
        process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Fonction pour lire stdout en temps reel
        def read_stdout():
            for line in iter(process.stdout.readline, ''):
                if line.strip():
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    diagnostic_logs.append(f"[{timestamp}] {line.strip()}")
        
        # Fonction pour lire stderr en temps reel
        def read_stderr():
            for line in iter(process.stderr.readline, ''):
                if line.strip():
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    diagnostic_logs.append(f"[{timestamp}] STDERR: {line.strip()}")
        
        # Demarrer les threads de lecture
        stdout_thread = threading.Thread(target=read_stdout)
        stderr_thread = threading.Thread(target=read_stderr)
        
        stdout_thread.start()
        stderr_thread.start()
        
        # Attendre la fin du processus
        return_code = process.wait()
        
        # Attendre que les threads de lecture terminent
        stdout_thread.join()
        stderr_thread.join()
        
        timestamp = datetime.now().strftime('%H:%M:%S')
        if return_code == 0:
            diagnostic_logs.append(f"[{timestamp}] Diagnostic termine avec succes!")
        else:
            diagnostic_logs.append(f"[{timestamp}] Diagnostic termine avec code d'erreur: {return_code}")
        
    except Exception as e:
        timestamp = datetime.now().strftime('%H:%M:%S')
        diagnostic_logs.append(f"[{timestamp}] ERREUR: {str(e)}")
        import traceback
        diagnostic_logs.append(f"[{timestamp}] Details: {traceback.format_exc()}")
    finally:
        diagnostic_running = False

@app.get("/logs")
async def get_logs():
    """Recuperer les logs actuels"""
    global diagnostic_running, diagnostic_logs
    
    status = "running" if diagnostic_running else ("completed" if diagnostic_logs else "ready")
    
    return {
        "logs": diagnostic_logs,
        "status": status,
        "running": diagnostic_running
    }

@app.get("/test")
async def test():
    return {"message": "Interface web operationnelle!", "status": "ok"}

if __name__ == "__main__":
    import uvicorn
    print("Demarrage interface V3 avec logs temps reel...")
    print("http://localhost:8000")
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)