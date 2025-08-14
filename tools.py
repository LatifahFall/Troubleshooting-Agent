# Essai: Tool classes: chaque fonction convertie en classe
import os
import inspect
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field
from abc import abstractmethod
from typing import Any

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

class ReadFile(BaseTool):
    """Read a file"""
    path: str = Field(...,description="The path to the file to read")

    def execute(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Fichier non trouvé: {path}"
        except Exception as e:
            return f"Erreur lors de la lecture du fichier: {e}"

class AskForClarification(BaseTool):
    """Ask for clarification"""
    message: str = Field(...,description="The message to ask for clarification")

    def execute(self, message: str) -> str:
        print(f"\n{'*' * 20}")
        print("ASKING FOR CLARIFICATION")
        response: str = input(f"\n{message}\nResponse: ")
        return response

class ProvideFurtherAssistance(BaseTool):
    """Provide further assistance"""
    message: str = Field(...,description="The message to show to the user to provide further assistance")

    def execute(self, message: str) -> str:
        print(f"\n{'*' * 20}")
        print("NEED MORE ASSISTANCE ?")
        response: str = input(f"\n{message}\nResponse: ")
        return response

class ListDirectory(BaseTool):
    """List files and directories in a given path"""
    path: str = Field(..., description="The directory path to list")
    
    def execute(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Répertoire non trouvé: {path}"
            
            if not os.path.isdir(path):
                return f"Erreur: '{path}' n'est pas un répertoire"
            
            items = []
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    size = os.path.getsize(item_path)
                    items.append(f"📄 {item} ({size} bytes)")
            
            if not items:
                return f"Répertoire vide: {path}"
            
            return f"Contenu de '{path}':\n" + "\n".join(items)
        except PermissionError:
            return f"Erreur de permissions: impossible de lire le répertoire {path}"
        except Exception as e:
            return f"Erreur lors de la lecture du répertoire: {e}"

class DoneForNow(BaseTool):
    """Indicate that the conversation is over"""
    message: str = Field(...,description="The message to show to the user to indicate that the conversation is over")
    
    def execute(self, message: str) -> None:
        print(f"\n{'*' * 20}")
        print(f"\n{message}")
        print(f"\n{'*' * 20}")

##adapte notre nouveau mode operatoire au main.py
class ToolFactory:
    """Factory class for creating tool instances"""
    _tools = {
        "read_file": ReadFile,
        "ask_for_clarification": AskForClarification,
        "provide_further_assistance": ProvideFurtherAssistance,
        "list_directory": ListDirectory,
        "done_for_now": DoneForNow,
    }

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
                    elif tool_class == ListDirectory:
                        return execute_method(kwargs.get('path'))
                    elif tool_class == AskForClarification:
                        return execute_method(kwargs.get('message'))
                    elif tool_class == ProvideFurtherAssistance:
                        return execute_method(kwargs.get('message'))
                    elif tool_class == DoneForNow:
                        return execute_method(kwargs.get('message'))
                    else:
                        return execute_method()
                else:
                    return execute_method()
            return wrapper
    
        return {name: create_wrapper(tool_class) for name, tool_class in cls._tools.items()}