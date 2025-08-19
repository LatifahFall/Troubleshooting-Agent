from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template
from typing import Any, Callable, Union
from pydantic import BaseModel, ValidationError, ConfigDict
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, \
    ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam
import json
from tools import ToolFactory, ReadFile, AskForClarification, ProvideFurtherAssistance, ListDirectory, DoneForNow, SystemCheck, ConnectivityCheck
from inspect import signature
import requests
import json
import os
from report_manager import ReportManager
# ================================
from database import DatabaseManager
import uuid
# ================================
load_dotenv()

def send_teams_message(message: str):
    webhook = "https://prod-186.westeurope.logic.azure.com:443/workflows/c5a65c6b8fb14fa28375af6b7e54da0f/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=hqxw7xLDPh0cVA0YjRJw8WBHe8WdUsFrlwJdBMMomYQ"
    
    payload = {
        "text": message
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(webhook, data=json.dumps(payload), headers=headers)

    if response.status_code == 200:
        print("✅ Alert sent to Microsoft Teams successfully!")

tool_factory = ToolFactory()
tool_mappings = tool_factory.create_function_mappings()

function_mappings: dict[str, Callable[..., Any]] = {
    **tool_mappings
}

def load_dynamic_prompt(template_path: str, capabilities: dict[str, Callable[..., Any]]) -> str:
    # load the template from the file
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    # create a context for the template
    capabilities_context = {
        name: {
            "signature": str(signature(func)),
            "returns": "string" if name in ["read_file", "ask_for_clarification", "provide_further_assistance", "list_directory", "done_for_now"] else "list of strings"
                    #    "list of strings" if name in ["find_app_log_files", "read_log_files"] else
                    #    "list of dicts" if name in ["get_app_logs", "get_nginx_logs"] else
                    #    "string"
        }
        for name, func in capabilities.items()
    }
    return template.render(capabilities=capabilities_context)

SYSTEM_PROMPT = load_dynamic_prompt("system_prompt_short.j2", function_mappings)

# print(SYSTEM_PROMPT)

client = OpenAI()

class Action(BaseModel):
    type: str
    parameters:Union[ReadFile, AskForClarification, ProvideFurtherAssistance, ListDirectory, DoneForNow, SystemCheck, ConnectivityCheck]
 
    model_config = ConfigDict(extra="forbid")

class Interpretation(BaseModel):
    log_type: str
    thoughts: str
    action: Action

    model_config = ConfigDict(extra="forbid")

class Response(BaseModel):
    interpretations: list[Interpretation]

messages: list[ChatCompletionMessageParam] = list([
    ChatCompletionSystemMessageParam(content=SYSTEM_PROMPT, role="system"),
])

# Initialize report manager
report_manager = ReportManager()

# ================================
# Initialize database
try:
    db_manager = DatabaseManager()
    session_id = str(uuid.uuid4())
    print(f"--- Database connected - Session: {session_id[:8]}")
except Exception as e:
    print(f"⚠️ Database connection failed: {e}")
    db_manager = None
# ================================

# Generate app ID based on the application directory
app_id = os.path.basename(os.getcwd())  # current directory name as app ID
# DEBUG: print the app ID pour voir si c'est bon
print(f"--- Application ID: {app_id}")

# Initialize a response object to collect all interpretations
final_response = Response(interpretations=[])

# Variable to store le message de diagnostic specifique
diagnostic_message = None

iteration: int = 0
max_iterations = 35
max_messages = 30  # Keeping only last 20 messages to prevent memory issues

while True and iteration < max_iterations:
    iteration += 1
    print(f"\n--- Iteration {iteration} ---")
    print(f"Current message count: {len(messages)}")

    try:
        completion = client.chat.completions.parse(
            model="gpt-4.1",
            messages=messages,
            temperature=0.7,
            response_format=Interpretation
        )
        # Debug: print raw OpenAI response only when i need
        # print(json.dumps(completion.choices[0].message.to_dict(), ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"Erreur lors de l'appel à OpenAI: {e}")
        break

    # print(completion.choices[0].message.observation)

    interpretation = completion.choices[0].message.parsed

    if interpretation is None:
        raise ValueError("Received empty response from OpenAI")
    
    try: 
        
        # Adding this interpretation to the final response
        final_response.interpretations.append(interpretation)
        
        log_type: str = interpretation.log_type
        thoughts: str = interpretation.thoughts
        action_type: str = interpretation.action.type
        action_params: dict[str, Any] = interpretation.action.parameters.model_dump()

        messages.append(
            ChatCompletionAssistantMessageParam(
                role="assistant",
                content=interpretation.model_dump_json()
            )
        )

        # Clean up messages to prevent memory issues
        if len(messages) > max_messages:
            # Keep system message and last max_messages-1 messages
            messages = [messages[0]] + messages[-(max_messages-1):]

        # DEBUGGING: printing individual interpretations
        print(json.dumps(interpretation.model_dump(), ensure_ascii=False, indent=2))
        print("-" * 25)

        if action_type in function_mappings:
            function = function_mappings[action_type]
            result = function(**action_params)
            # print(f"Function result: {result}")
            # print(f"Action: {action_type}")

            # For user input functions, add the user's response as a user message
            if action_type in ["ask_for_clarification", "provide_further_assistance"]:
                print(f"{result}")
                
                # Manière de reconnaitre un msg de diagnostic
                # Capture diagnostic message if it contains diagnosis details + is longer than 500 characters
                if action_type == "provide_further_assistance":
                    message = action_params.get('message', '')
                    if "Diagnosis" in message and len(message) > 250:
                        diagnostic_message = message
                        print(f"--- Diagnostic captured ({len(message)} characters)")
                    #TODO: j'aime pas cette logique, c'est pas sûr, il faudrait que le diagnostic soit un peu plus explicite, trouver mieux

                messages.append(ChatCompletionUserMessageParam(
                    role="user",
                    content=result
                ))
            # dont wanna print the result of the read_file function
            if action_type == "read_file":
                print(f"FILE READ SUCCESSFULLY")
                messages.append(ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=str({
                        "action": f"{action_type}_result",
                        "observation": result,
                    })
                ))
            else:
                # For other functions, add the result as an assistant message
                print(f"{result}")
                messages.append(ChatCompletionAssistantMessageParam(
                    role="assistant",
                    content=str({
                        "action": f"{action_type}_result",
                        "observation": result,
                    })
                ))
            
            # Clean up messages after function result too
            if len(messages) > max_messages:
                messages = [messages[0]] + messages[-(max_messages-1):]

            if action_type == "done_for_now":
                # Print the complete final response with all interpretations FIRST
                print("\n" + "="*50)
                print("COMPLETE ANALYSIS LOG:")
                print("="*50)
                print(json.dumps(final_response.model_dump(), ensure_ascii=False, indent=2))
                
                # THEN show the completion message from the function result
                print(f"\n{'*' * 20}")
                print("ANALYSIS COMPLETE")
                print(f"\n{result}")
                print(f"\n{'*' * 20}")
                
                # Save troubleshooting report
                try:
                    print(f"\n--- Saving troubleshooting report...")
                    #si pas de diagnostic message, on utilise le dernier message
                    if diagnostic_message:
                        report_content = diagnostic_message
                    else:
                        report_content = result
                    report_path = report_manager.save_report(app_id, report_content)
                    print(f"--- Report saved: {report_path}")
                    
                    # Send diagnosis to Teams
                    try:
                        print(f"\n--- Sending diagnosis to Microsoft Teams...")
                        send_teams_message(report_content)
                    except Exception as teams_error:
                        print(f"\n⚠️ Failed to send Teams notification: {teams_error}")
                    
                    # ================================
                    # Save to database
                    if db_manager:
                        try:
                            db_manager.save_session(
                                session_id=session_id,
                                app_name=app_id,
                                diagnostic_message=diagnostic_message or result,
                                final_response=final_response.model_dump()
                            )
                            print(f"--- Session saved to database")
                        except Exception as e:
                            print(f"⚠️ Database save failed: {e}")
                        
                except Exception as e:
                    print(f"\n⚠️ Failed to save report: {e}")
                    import traceback
                    traceback.print_exc()
                break
        else:
            raise ValueError("Invalid action type")

    # ================================
    except ValidationError as e:
        print(f"Erreur de validation du modèle Response: {e}")

    except Exception as e:
        print(f"Erreur de décodage JSON: {e}")