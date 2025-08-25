from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from database import DatabaseManager
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

# Variables globales pour le chat
current_chat_question = None
chat_response_received = None

class DiagnosticRequest(BaseModel):
    app_path: str

class ChatResponseRequest(BaseModel):
    message: str

@app.get("/")
async def home():
    return FileResponse("static/index.html")

@app.get("/browse")
async def browse_directory(path: str = "."):
    """API pour naviguer dans les dossiers"""
    try:
        # conv chemin relatif en chemin absolu
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
    
    # Réinitialiser l'état si nécessaire
    if diagnostic_running:
        diagnostic_logs.append(f"[{datetime.now().strftime('%H:%M:%S')}] ATTENTION: Forçage du redémarrage (diagnostic précédent terminé)")
        diagnostic_running = False
    
    diagnostic_running = True
    diagnostic_logs = [f"[{datetime.now().strftime('%H:%M:%S')}] Diagnostic demarre pour: {request.app_path}"]
    
    # Lancer le vrai diagnostic en arriere-plan
    background_tasks.add_task(run_real_diagnostic, request.app_path)
    
    return {"status": "started", "message": "Diagnostic demarre"}

@app.get("/logs")
async def get_logs():
    """Récupérer les logs du diagnostic"""
    return {"logs": diagnostic_logs, "running": diagnostic_running}

@app.post("/chat-response")
async def receive_chat_response(request: ChatResponseRequest):
    """Recevoir une réponse de l'utilisateur"""
    global chat_response_received
    chat_response_received = request.message
    timestamp = datetime.now().strftime('%H:%M:%S')
    diagnostic_logs.append(f"[{timestamp}] CHAT: Réponse utilisateur reçue: {request.message}")
    
    # Écrire la réponse dans le fichier temporaire pour l'agent
    try:
        with open("web_chat_response.txt", "w", encoding="utf-8") as f:
            f.write(request.message)
        diagnostic_logs.append(f"[{timestamp}] CHAT: Réponse transmise à l'agent")
    except Exception as e:
        diagnostic_logs.append(f"[{timestamp}] CHAT: Erreur transmission: {e}")
    
    return {"status": "ok", "message": "Réponse reçue"}

@app.post("/stop-diagnostic")
async def stop_diagnostic():
    """Arrêter le diagnostic en cours"""
    global diagnostic_running, diagnostic_logs
    diagnostic_running = False
    timestamp = datetime.now().strftime('%H:%M:%S')
    diagnostic_logs.append(f"[{timestamp}] Diagnostic arrêté manuellement")
    return {"status": "stopped", "message": "Diagnostic arrêté"}

@app.get("/history")
async def get_history(app_name: str = None):
    """Récupérer l'historique des diagnostics"""
    try:
        db_manager = DatabaseManager()
        
        if app_name:
            # Filtrer par nom d'application
            sessions = db_manager.get_sessions_by_app(app_name)
        else:
            # Récupérer tout l'historique
            sessions = db_manager.get_all_sessions()
        
        # Formater les données pour l'affichage
        history_data = []
        for session in sessions:
            history_data.append({
                "id": session.id,
                "app_name": session.app_name,
                "started_at": session.started_at.strftime("%Y-%m-%d %H:%M:%S") if session.started_at else "",
                "diagnostic_message": session.diagnostic_message[:200] + "..." if session.diagnostic_message and len(session.diagnostic_message) > 200 else session.diagnostic_message,
                "has_final_response": bool(session.final_response)
            })
        
        return {"history": history_data}
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/apps")
async def get_apps():
    """Récupérer la liste des applications diagnostiquées"""
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        apps = db_manager.get_unique_app_names()
        
        return {"apps": apps}
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/history/{session_id}")
async def get_diagnostic_details(session_id: str):
    """Récupérer les détails complets d'un diagnostic spécifique"""
    try:
        from database import DatabaseManager
        
        db_manager = DatabaseManager()
        session = db_manager.get_session_by_id(session_id)
        
        if not session:
            return JSONResponse({"error": "Diagnostic non trouvé"}, status_code=404)
        
        # Formater les données complètes
        details = {
            "id": session.id,
            "app_name": session.app_name,
            "started_at": session.started_at.strftime("%Y-%m-%d %H:%M:%S") if session.started_at else "",
            "diagnostic_message": session.diagnostic_message,
            "final_response": session.final_response,
            "has_final_response": bool(session.final_response)
        }
        
        return {"details": details}
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

def run_real_diagnostic(app_path: str):
    """Executer le vrai agent de troubleshooting"""
    global diagnostic_running, diagnostic_logs
    
    try:    
        timestamp = datetime.now().strftime('%H:%M:%S')
        diagnostic_logs.append(f"[{timestamp}] Demarrage du diagnostic pour: {app_path}")
        
        # Preparer l'environnement avec le chemin cible
        env = os.environ.copy()
        env['TARGET_APP_PATH'] = app_path
        # env['WEB_MODE'] = 'true'  # Activer le mode web pour éviter les input() pour le moment
        env['PYTHONUNBUFFERED'] = '1'  # Forcer l'affichage en temps réel
        
        diagnostic_logs.append(f"[{timestamp}] Lancement de main.py...")
        # diagnostic_logs.append(f"[{timestamp}] Repertoire de travail: {os.getcwd()}")
        # diagnostic_logs.append(f"[{timestamp}] Chemin Python: {sys.executable}")
        
        # Executer main.py avec capture des sorties
        process = subprocess.Popen(
            [sys.executable, "-u", "main.py"],  # -u pour unbuffered
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=os.getcwd(),  # S'assurer qu'on est dans le bon répertoire (courant)
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

if __name__ == "__main__":
    import uvicorn
    print("Démarrage interface web avec fichiers séparés...")
    print("http://localhost:8001")
    uvicorn.run("web_app:app", host="0.0.0.0", port=8001, reload=True)