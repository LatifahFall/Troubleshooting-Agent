import os
import re
import platform
import psutil
from dotenv import load_dotenv
import socket
import telnetlib

load_dotenv()

def read_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"Fichier non trouvé: {path}"
    except Exception as e:
        return f"Erreur lors de la lecture du fichier: {e}"

def ask_for_clarification(message: str) -> str:
    print(f"\n{'*' * 20}")
    print("ASKING FOR CLARIFICATION")
    response: str = input(f"\n{message}\nResponse: ")
    return response

def provide_further_assistance(message: str) -> str:
    print(f"\n{'*' * 20}")
    print("NEED MORE ASSISTANCE ?")
    response: str = input(f"\n{message}\nResponse: ")
    return response

def provide_diagnosis(message: str) -> str:
    print(f"\n{'*' * 20}")
    print("DIAGNOSIS PROVIDED")
    print(f"\n{message}")
    print(f"\n{'*' * 20}")
    return "Diagnosis provided successfully"

def done_for_now(message: str) -> None:
    print(f"\n{'*' * 20}")
    print(f"\n{message}")
    print(f"\n{'*' * 20}")
    
# Configuration for log directories
APP_LOG_DIRS = [
    './storage/logs',        # Laravel logs
    './logs',               # Custom app logs
    './chemin'              # current sample directory
]

NGINX_LOG_DIRS = [
    '/var/log/nginx',       # Standard nginx location
    '/var/log'              # System logs (includes nginx)
]

#cette fonction est utilisée pour trouver le répertoire de travail
#pour l'analyse des logs applicatifs
def get_app_log_directory() -> str:
    """
    Get the directory to search for application logs.
    Priority: ENV variable > common app dirs > current dir
    """
    # 1. Environment variable (highest priority)
    env_log_dir = os.getenv('APP_LOG_DIR')
    if env_log_dir and os.path.exists(env_log_dir):
        return env_log_dir
    
    # 2. Check common app log directories
    for log_dir in APP_LOG_DIRS:
        if os.path.exists(log_dir):
            return log_dir
    
    # 3. Fallback to current directory
    return "."

#cette fonction est utilisée pour trouver le répertoire de travail
#pour l'analyse des logs nginx
def get_nginx_log_directory() -> str:
    """
    Get the directory to search for nginx logs.
    Priority: ENV variable > common nginx dirs > current dir
    """
    # 1. Environment variable (highest priority)
    env_log_dir = os.getenv('NGINX_LOG_DIR')
    if env_log_dir and os.path.exists(env_log_dir):
        return env_log_dir
    
    # 2. Check common nginx log directories
    for log_dir in NGINX_LOG_DIRS:
        if os.path.exists(log_dir):
            return log_dir
    
    # 3. Fallback to current directory
    return "."

#fonction que j'utiliserai à la fois pour les logs applicatifs et ceux du serveur web
#pour lire et stocker dans une variable le contenu des fichiers trouvés
def read_log_files(log_files: list[str]) -> list[str]:
    log_contents = []
    for log_file in log_files:
        content = read_file(log_file)
        log_contents.append(content)
    return log_contents

#cette fonction trouve les logs applicatifs dans un répertoire
def find_app_log_files(root_path: str) -> list[str]:
    log_files = []
    log_extensions = {'.log', '.txt', '.out', '.err'}

    # Application-specific hints
    app_keywords = {'app', 'application', 'exception', 'debug', 'trace', 'laravel'}
    app_dirs = {'/logs', '/storage/logs', '/var/log/myapp', '/var/log/app'}

    # Web server hints à exclure
    web_server_keywords = {'nginx', 'apache', 'httpd', 'access', 'combined', 'ssl'}
    web_dirs = {'/var/log/nginx', '/var/log/apache2', '/var/log/httpd'}

    # Patterns to detect log-like content
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}')
    log_level_pattern = re.compile(r'\b(INFO|ERROR|WARN|DEBUG|TRACE|CRITICAL)\b')

    for dirpath, _, filenames in os.walk(root_path):
        dir_lower = dirpath.lower()

        # Skip obvious web server directories
        if any(wd in dir_lower for wd in web_dirs):
            continue

        for filename in filenames:
            filename_lower = filename.lower()
            file_path = os.path.join(dirpath, filename)

            # Skip files that look like web server logs
            if any(web_kw in filename_lower for web_kw in web_server_keywords):
                continue

            # Check extension or app keyword
            if not (filename_lower.endswith(tuple(log_extensions)) or
                    any(kw in filename_lower for kw in app_keywords) or
                    any(ad in dir_lower for ad in app_dirs)):
                continue

            # Skip huge files (for safety)
            try:
                if os.path.getsize(file_path) > 500_000_000:  # 500MB
                    continue
            except OSError:
                continue

            # Read some lines to check if it looks like a log
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [next(f, '') for _ in range(10)]
                    content = ' '.join(lines)
                    if timestamp_pattern.search(content) or log_level_pattern.search(content):
                        log_files.append(file_path)
            except (OSError, StopIteration):
                continue

    return log_files

# This function finds Nginx log files in a directory
def find_nginx_log_files(root_path: str) -> list[str]:
    log_files = []
    log_extensions = {'.log'}

    # Mots-clés et dossiers typiques pour nginx
    nginx_keywords = {'nginx', 'access', 'error', 'ssl', 'combined'}
    nginx_dirs = {'/var/log/nginx', '/usr/local/nginx/logs'}

    # Patterns pour détecter un log nginx
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}')
    nginx_access_pattern = re.compile(r'^\d{1,3}(?:\.\d{1,3}){3} - - \[.*\]')

    for dirpath, _, filenames in os.walk(root_path):
        dir_lower = dirpath.lower()

        for filename in filenames:
            filename_lower = filename.lower()
            file_path = os.path.join(dirpath, filename)

            # Filtrer sur extension et dossier ou mots-clés dans le nom de fichier
            if not filename_lower.endswith(tuple(log_extensions)):
                continue

            in_nginx_dir = any(ng_dir in dir_lower for ng_dir in nginx_dirs)
            has_nginx_keyword = any(kw in filename_lower for kw in nginx_keywords)

            if not (in_nginx_dir or has_nginx_keyword):
                continue

            # Ignorer les fichiers très gros (> 500MB)
            try:
                if os.path.getsize(file_path) > 500_000_000:
                    continue
            except OSError:
                continue

            # Lire les 10 premières lignes pour mieux détecter les logs nginx
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [next(f, '') for _ in range(10)]
            except (OSError, StopIteration):
                continue

            content_sample = ' '.join(lines)

            # Valider si c’est un log nginx via pattern d’accès ou timestamp
            if any(nginx_access_pattern.match(line) for line in lines) or timestamp_pattern.search(content_sample):
                log_files.append(file_path)

    return log_files

#Meilleur d'indiquer dans quel fichier on a trouvé chqaue log
def get_app_logs(root_path: str) -> list[dict]:
    """Find and read all application log files from the given directory."""
    log_files = find_app_log_files(root_path)
    log_data = []
    for log_file in log_files:
        content = read_file(log_file)
        log_data.append({
            'file_path': log_file,
            'content': content,
            'file_size': os.path.getsize(log_file) if os.path.exists(log_file) else 0
        })
    return log_data

def get_nginx_logs(root_path: str) -> list[dict]:
    """Find and read all nginx log files from the given directory"""
    log_files = find_nginx_log_files(root_path)
    log_data = []
    for log_file in log_files:
        content = read_file(log_file)
        log_data.append({
            'file_path' : log_file,
            'content' : content,
            'file_size' : os.path.getsize(log_file)
        if os.path.exists(log_file) else 0
        })
    return log_data

class SystemStatus:
    def __init__(self):
        self.memory = psutil.virtual_memory()
        self.disk = psutil.disk_usage('/')
        self.cpu_count = psutil.cpu_count(logical=True)
        
    def get_memory_usage_percent(self):
        return round(self.memory.percent, 2)
    
    def get_disk_usage_percent(self):
        return round(((self.disk.total - self.disk.free) / self.disk.total) * 100, 2)
    
    def get_memory_available_percent(self):
        return round((self.memory.available / self.memory.total) * 100, 2)
    
    def get_disk_free_percent(self):
        return round((self.disk.free / self.disk.total) * 100, 2)
    
    def to_dict(self):
        return {
            "os": platform.system(),
            "os_version": platform.version(),
            "cpu_count": self.cpu_count,
            "memory": {
                "total_gb": round(self.memory.total / (1024**3), 2),
                "available_gb": round(self.memory.available / (1024**3), 2),
                "used_gb": round((self.memory.total - self.memory.available) / (1024**3), 2),
                "usage_percent": self.get_memory_usage_percent(),
                "available_percent": self.get_memory_available_percent()
            },
            "disk": {
                "total_gb": round(self.disk.total / (1024**3), 2),
                "free_gb": round(self.disk.free / (1024**3), 2),
                "used_gb": round((self.disk.total - self.disk.free) / (1024**3), 2),
                "usage_percent": self.get_disk_usage_percent(),
                "free_percent": self.get_disk_free_percent()
            }
        }

def system_check():
    status = SystemStatus()
    return status.to_dict()

def get_app_history(app_path: str = ".") -> dict:
    """Get historical data about this application for context"""
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from memory_manager import MemoryManager
        memory_manager = MemoryManager()
        history = memory_manager.get_relevant_history(app_path)
        return history
    except Exception as e:
        return {"error": f"Failed to load history: {e}"}

def connectivity_check():
    host = os.getenv("HOST")
    port = os.getenv("PORT")

    if not host or not port:
        return {"status": "error", "message": "Missing HOST or PORT environment variables"}

    try:
        port = int(port)
    except ValueError:
        return {"status": "error", "message": "PORT must be a number"}

    try:
        tn = telnetlib.Telnet(host, port, timeout=5)
        tn.close()
        return {"status": "success", "message": f"Telnet connection to {host}:{port} succeeded"}
    except Exception as telnet_error:
        # Fallback: essayer socket connection
        try:
            with socket.create_connection((host, port), timeout=5):
                return {"status": "success", "message": f"Socket connection to {host}:{port} succeeded (Telnet failed)"}
        except Exception as socket_error:
            return {
                "status": "error",
                "message": f"Connection to {host}:{port} failed",
                "telnet_error": str(telnet_error),
                "socket_error": str(socket_error)
            }