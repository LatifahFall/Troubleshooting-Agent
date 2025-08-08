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
    log_extensions = ['.log', '.txt', '.out', '.err']
    
    # Application-specific keywords (excluding web server logs)
    app_keywords = ['app', 'application', 'exception', 'debug', 'trace', 'laravel']
    
    # Web server keywords to exclude
    web_server_keywords = ['nginx', 'apache', 'httpd', 'access', 'combined', 'ssl', 'error']
    
    timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2}|\d{2}:\d{2}:\d{2}')  # Simple pattern date/time

    # Boucle sur les dossiers/fichiers
    for dirpath, _, filenames in os.walk(root_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            filename_lower = filename.lower()
            
            # Skip web server logs
            if any(web_keyword in filename_lower for web_keyword in web_server_keywords):
                continue
                
            # vérifie extension or application keyword in filename
            if any(filename_lower.endswith(ext) for ext in log_extensions) or \
               any(keyword in filename_lower for keyword in app_keywords):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        first_line = f.readline()
                        # Check if first line has a timestamp pattern
                        if timestamp_pattern.search(first_line):
                            log_files.append(file_path)
                except Exception:
                    # File non lisible ou autre, on ignore
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