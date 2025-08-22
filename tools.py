# Essai: Tool classes: chaque fonction convertie en classe
import os
import inspect
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
from abc import abstractmethod
from typing import Any, Dict, Optional
import psutil
import platform
import socket
import telnetlib

class BaseTool(BaseModel):
    """Base class for all tools"""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=False
    )

    @abstractmethod
    def execute(self) -> Any:
        """Execute the tool"""
        pass
    
    def _wait_for_web_response(self, question: str) -> str:
        """Attendre une réponse de l'utilisateur via l'interface web"""
        import time
        
        # Écrire la question dans un fichier temporaire
        response_file = "web_chat_response.txt"
        question_file = "web_chat_question.txt"
        
        # Écrire la question
        with open(question_file, "w", encoding="utf-8") as f:
            f.write(question)
        
        # Supprimer le fichier de réponse s'il existe
        if os.path.exists(response_file):
            os.remove(response_file)
        
        print(f"ATTENTE REPONSE WEB: En attente de la réponse utilisateur...", flush=True)
        
        # Attendre que le fichier de réponse soit créé
        max_wait = 300  # 5 minutes max
        wait_time = 0
        
        while wait_time < max_wait:
            if os.path.exists(response_file):
                with open(response_file, "r", encoding="utf-8") as f:
                    response = f.read().strip()
                
                # Nettoyer les fichiers temporaires
                try:
                    os.remove(response_file)
                    os.remove(question_file)
                except:
                    pass
                
                print(f"REPONSE RECUE: {response}", flush=True)
                return response
            
            time.sleep(1)
            wait_time += 1
        
        # Timeout - réponse par défaut
        print("TIMEOUT: Aucune réponse reçue, utilisation de la réponse par défaut", flush=True)
        return "Continuer sans clarification supplémentaire"

class ReadFile(BaseTool):
    """Read a file"""
    path: str = Field(...,description="The path to the file to read")

    def execute(self, path: str) -> str:
        try:
            # Si c'est un chemin relatif, le résoudre depuis l'app cible
            target_app_path = os.getenv('TARGET_APP_PATH', os.getcwd())
            
            if not os.path.isabs(path):
                # Chemin relatif : le résoudre depuis l'app cible
                full_path = os.path.join(target_app_path, path)
            else:
                # Chemin absolu : l'utiliser tel quel
                full_path = path
                
            with open(full_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Fichier non trouvé: {full_path}"
        except Exception as e:
            return f"Erreur lors de la lecture du fichier: {e}"

class AskForClarification(BaseTool):
    """Ask for clarification"""
    message: str = Field(...,description="The message to ask for clarification")

    def execute(self, message: str) -> str:
        # Mode web : attendre une réponse via le chat
        if os.getenv('WEB_MODE', 'false').lower() == 'true':
            print(f"\n{'*' * 20}")
            print("DEMANDE DE CLARIFICATION")
            print(f"CHAT_QUESTION: {message}")
            print(f"{'*' * 20}")
            
            # Attendre la réponse via un fichier temporaire ou polling
            return self._wait_for_web_response(message)
        
        
        # Mode console classique
        print(f"\n{'*' * 20}")
        print("ASKING FOR CLARIFICATION")
        response: str = input(f"\n{message}\nResponse: ")
        return response

class ProvideFurtherAssistance(BaseTool):
    """Provide further assistance"""
    message: str = Field(...,description="The message to show to the user to provide further assistance")

    def execute(self, message: str) -> str:
        # Mode web : attendre une réponse via le chat
        if os.getenv('WEB_MODE', 'false').lower() == 'true':
            print(f"\n{'*' * 20}")
            print("ASSISTANCE SUPPLEMENTAIRE")
            print(f"CHAT_QUESTION: {message}")
            print(f"{'*' * 20}")
            
            # Attendre la réponse via un fichier temporaire ou polling
            return self._wait_for_web_response(message)
        
        
        # Mode console classique
        print(f"\n{'*' * 20}")
        print("NEED MORE ASSISTANCE ?")
        response: str = input(f"\n{message}\nResponse: ")
        return response

class ListDirectory(BaseTool):
    """List files and directories in a given path"""
    path: str = Field(..., description="The directory path to list")
    
    def execute(self, path: str) -> str:
        try:
            # Si c'est un chemin relatif, le résoudre depuis l'app cible
            target_app_path = os.getenv('TARGET_APP_PATH', os.getcwd())
            
            if not os.path.isabs(path):
                full_path = os.path.join(target_app_path, path)
            else:
                full_path = path
                
            if not os.path.exists(full_path):
                return f"Répertoire non trouvé: {full_path}"
            
            if not os.path.isdir(full_path):
                return f"Erreur: '{full_path}' n'est pas un répertoire"
            
            # this was initially for debugging purposes, but imma keep it for now
            items = []
            for item in sorted(os.listdir(full_path)):
                item_path = os.path.join(full_path, item)
                if os.path.isdir(item_path):
                    items.append(f"[DIR] {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"[FILE] {item} ({size} bytes)")
            
            if not items:
                return f"Répertoire vide: {full_path}"
            
            return f"Contenu de '{full_path}':\n" + "\n".join(items)
        except PermissionError:
            return f"Erreur de permissions: impossible de lire le répertoire {full_path}"
        except Exception as e:
            return f"Erreur lors de la lecture du répertoire: {e}"

class DoneForNow(BaseTool):
    """Indicate that the conversation is over"""
    message: str = Field(...,description="The message to show to the user to indicate that the conversation is over")
    
    def execute(self, message: str) -> str:
        return f"{message}"

# System Tools
# model
class SystemInfo(BaseModel):
    """Model for system information"""
    os: str
    os_version: str
    cpu_count: int
    memory: Dict[str, float]
    disk: Dict[str, float]
# tool
class SystemCheck(BaseTool):
    """Tool for performing system checks"""
    
    def execute(self) -> SystemInfo:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_count = psutil.cpu_count(logical=True)
        
        return SystemInfo(
            os=platform.system(),
            os_version=platform.version(),
            cpu_count=cpu_count,
            memory={
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round((memory.total - memory.available) / (1024**3), 2),
                "usage_percent": round(memory.percent, 2),
                "available_percent": round((memory.available / memory.total) * 100, 2)
            },
            disk={
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_gb": round((disk.total - disk.free) / (1024**3), 2),
                "usage_percent": round(((disk.total - disk.free) / disk.total) * 100, 2),
                "free_percent": round((disk.free / disk.total) * 100, 2)
            }
        )

# Network Tools
# model
class ConnectivityResult(BaseModel):
    """Model for connectivity check results"""
    status: str
    message: str
    telnet_error: Optional[str] = None
    socket_error: Optional[str] = None

# tool
class ConnectivityCheck(BaseTool):
    """Tool for checking network connectivity"""
    
    def execute(self) -> ConnectivityResult:
        host = os.getenv("HOST")
        port = os.getenv("PORT")

        if not host or not port:
            return ConnectivityResult(
                status="error", 
                message="Missing HOST or PORT environment variables"
            )

        try:
            port_int = int(port)
        except ValueError:
            return ConnectivityResult(
                status="error", 
                message="PORT must be a number"
            )

        try:
            # try telnet connection (if it fails, try socket connection)
            tn = telnetlib.Telnet(host, port_int, timeout=5)
            tn.close()
            return ConnectivityResult(
                status="success", 
                message=f"Telnet connection to {host}:{port} succeeded"
            )
        except Exception as telnet_error:
            # Fallback: essayer socket connection
            try:
                with socket.create_connection((host, port_int), timeout=5):
                    return ConnectivityResult(
                        status="success", 
                        message=f"Socket connection to {host}:{port} succeeded (Telnet failed)"
                    )
            except Exception as socket_error:
                return ConnectivityResult(
                    status="error",
                    message=f"Connection to {host}:{port} failed",
                    telnet_error=str(telnet_error),
                    socket_error=str(socket_error)
                )

#adapte notre nouveau mode operatoire au main.py
class ToolFactory:
    """Factory class for creating tool instances"""
    # mapper les noms->classes d'outils
    _tools = {
        "read_file": ReadFile,
        "system_check": SystemCheck,
        "ask_for_clarification": AskForClarification,
        "provide_further_assistance": ProvideFurtherAssistance,
        "list_directory": ListDirectory,
        "done_for_now": DoneForNow,
        "connectivity_check": ConnectivityCheck,
    }
#  convertit les classes d'outils en fonctions appelable dans notre main.py
    @classmethod
    def create_function_mappings(cls):
        """Create function mappings for all tools"""
        def create_wrapper(tool_class):
            def wrapper(**kwargs):
                tool = tool_class(**kwargs)
                # Get the execute method signature
                execute_method = tool.execute
                sig = inspect.signature(execute_method)
                
                # If execute method takes parameters, pass them
                if len(sig.parameters) > 0:
                    if tool_class == ReadFile:
                        return execute_method(kwargs.get('path'))
                    elif tool_class == SystemCheck or tool_class == ConnectivityCheck:
                        return execute_method()
                    elif tool_class == ListDirectory:
                        return execute_method(kwargs.get('path'))
                    elif tool_class in (AskForClarification, ProvideFurtherAssistance, DoneForNow):
                        return execute_method(kwargs.get('message'))
                    else:
                        return execute_method()
                else:
                    return execute_method()
            return wrapper
    
        return {name: create_wrapper(tool_class) for name, tool_class in cls._tools.items()}