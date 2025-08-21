from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import time
from datetime import datetime
import subprocess
import sys
import threading

app = FastAPI(title="Troubleshooting Agent")

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory="static"), name="static")

# Variables globales pour les logs
diagnostic_logs = []
diagnostic_running = False

class DiagnosticRequest(BaseModel):
    app_path: str

@app.get("/")
async def home():
    return FileResponse("static/index.html")

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
                continue
        
        return {
            "current_path": path,
            "directories": directories,
            "files": files[:10]  # Limiter à 10 fichiers pour l'affichage
        }
    except PermissionError:
        return JSONResponse({"error": "Permissions insuffisantes"}, status_code=403)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/start-diagnostic")
async def start_diagnostic(request: DiagnosticRequest, background_tasks: BackgroundTasks):
    """Demarrer un diagnostic"""
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
        timestamp = datetime.now().strftime('%H:%M:%S')
        diagnostic_logs.append(f"[{timestamp}] Demarrage du diagnostic pour: {app_path}")
        
        # Preparer l'environnement avec le chemin cible
        env = os.environ.copy()
        env['TARGET_APP_PATH'] = app_path
        env['WEB_MODE'] = 'true'  # Activer le mode web pour éviter les input() pour le moment
        env['PYTHONUNBUFFERED'] = '1'  # Forcer l'affichage en temps réel
        
        diagnostic_logs.append(f"[{timestamp}] Lancement de main.py...")
        diagnostic_logs.append(f"[{timestamp}] Repertoire de travail: {os.getcwd()}")
        diagnostic_logs.append(f"[{timestamp}] Chemin Python: {sys.executable}")
        
        # Executer main.py avec capture des sorties
        process = subprocess.Popen(
            [sys.executable, "-u", "main.py"],  # -u pour unbuffered
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.getcwd(),  # S'assurer qu'on est dans le bon répertoire
            bufsize=1,  # Line buffered pour avoir les lignes immédiatement
            universal_newlines=True
        )
        
        # Fonction pour lire stdout en temps reel
        def read_stdout():
            for line in iter(process.stdout.readline, ''):
                # if line.strup():
                line = line.rstrip('\n\r')  # Enlever les retours à la ligne
                if line:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    diagnostic_logs.append(f"[{timestamp}] {line}")
        
        # Fonction pour lire stderr en temps reel
        def read_stderr():
            for line in iter(process.stderr.readline, ''):
                line = line.rstrip('\n\r')
                if line:
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    diagnostic_logs.append(f"[{timestamp}] STDERR: {line}")
        
        # Verifier si le processus a demarré
        time.sleep(0.5)  # Attendre un peu
        if process.poll() is not None:
            # Le processus s'est termine immediatement
            stdout, stderr = process.communicate()
            timestamp = datetime.now().strftime('%H:%M:%S')
            diagnostic_logs.append(f"[{timestamp}] ERREUR: Le processus s'est termine immediatement")
            if stdout:
                diagnostic_logs.append(f"[{timestamp}] STDOUT: {stdout}")
            if stderr:
                diagnostic_logs.append(f"[{timestamp}] STDERR: {stderr}")
            return
        
        diagnostic_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] Processus demarré avec succes, lecture des sorties...")
        
        # Démarrer les threads de lecture
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
            diagnostic_logs.append(f"[{timestamp}] Diagnostic terminé avec succes!")
        else:
            diagnostic_logs.append(f"[{timestamp}] Diagnostic terminé avec code d'erreur: {return_code}")
        
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
    return {
        "logs": diagnostic_logs,
        "running": diagnostic_running
    }

if __name__ == "__main__":
    import uvicorn
    print("Démarrage interface web avec fichiers séparés...")
    print("http://localhost:8000")
    uvicorn.run("web_app:app", host="0.0.0.0", port=8000, reload=True)