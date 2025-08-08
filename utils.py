import os
import re

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

def done_for_now(message: str) -> None:
    print(f"\n{'*' * 20}")
    print(f"\n{message}")
    print(f"\n{'*' * 20}")

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
    log_extensions = ['.log']
    nginx_keywords = ['nginx', 'access', 'error', 'ssl', 'combined']
    nginx_dirs = ['/var/log/nginx', '/usr/local/nginx/logs']
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}')

    for dirpath, _, filenames in os.walk(root_path):
        dir_lower = dirpath.lower()

        # Skip non-nginx directories unless file matches keywords
        if not any(nginx_dir in dir_lower for nginx_dir in nginx_dirs):
            # This allows catching nginx logs even outside the default folder
            pass

        for filename in filenames:
            filename_lower = filename.lower()
            file_path = os.path.join(dirpath, filename)

            # Match nginx logs either by directory or filename keywords
            if (any(ext for ext in log_extensions if filename_lower.endswith(ext)) and
                (any(keyword in filename_lower for keyword in nginx_keywords) or
                 any(nginx_dir in dir_lower for nginx_dir in nginx_dirs))):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        first_line = f.readline()
                        if timestamp_pattern.search(first_line):
                            log_files.append(file_path)
                except Exception:
                    continue
    return log_files

# def get_app_logs(root_path: str) -> list[str]:
#     """Find and read all application log files from the given directory."""
#     log_files = find_app_log_files(root_path)
#     return read_log_files(log_files)

#Meilleur d'indiquer dans quel fichier on a trouvé chqaue
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
