from utils import get_app_logs, get_nginx_logs, read_file, ask_for_clarification, done_for_now, provide_further_assistance
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template
from typing import Any, Callable
from pydantic import BaseModel, ValidationError
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, \
    ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam
import json

load_dotenv()

function_mappings: dict[str, Callable[..., Any]] = {
    "read_file": read_file,
    "ask_for_clarification": ask_for_clarification,
    "provide_further_assistance": provide_further_assistance,
    "done_for_now": done_for_now,
    # "find_app_log_files": find_app_log_files,
    # "read_log_files": read_log_files,
    "get_app_logs": get_app_logs,
    "get_nginx_logs": get_nginx_logs
}

def load_dynamic_prompt(template_path: str, capabilities: dict[str, Callable[..., Any]]) -> str:
    from inspect import signature

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    capabilities_context = {
        name: {
            "signature": str(signature(func)),
            "returns": "string" if name in ["read_file", "ask_for_clarification", "provide_further_assistance"] else
                       "list of strings" if name in ["find_app_log_files", "read_log_files"] else
                       "list of dicts" if name in ["get_app_logs", "get_nginx_logs"] else
                       "None" if name in ["done_for_now"] else
                       "string"
        }
        for name, func in capabilities.items()
    }

    return template.render(capabilities=capabilities_context)

SYSTEM_PROMPT = load_dynamic_prompt("system_prompt.j2", function_mappings)

client = OpenAI()

class Interpretation(BaseModel):
    log_type: str
    thoughts: str
    intent: str
    args: dict[str, Any]
    
    class Config:
        extra = "forbid"  # This prevents additional properties

class Response(BaseModel):
    interpretations: list[Interpretation]

messages: list[ChatCompletionMessageParam] = list([
    ChatCompletionSystemMessageParam(content=SYSTEM_PROMPT, role="system"),
])

# Initialize a response object to collect all interpretations
final_response = Response(interpretations=[])

iteration: int = 0
max_iterations = 10
max_messages = 20  # Keep only last 20 messages to prevent memory issues

while True and iteration < max_iterations:
    iteration += 1

    try:
        completion = client.chat.completions.create(
            model="gpt-4.1",
            messages=messages,
            response_format={"type": "json_object"}
        )
    except Exception as e:
        print(f"Erreur lors de l'appel à OpenAI: {e}")
        break

    # print(completion.choices[0].message.observation)

    observation = completion.choices[0].message.content
    if observation is None:
        raise ValueError("Received empty response from OpenAI")
    
    try: 
        response_dict = json.loads(observation)
        # Parse the interpretation from the response
        interpretation = Interpretation(**response_dict)
        
        # Add this interpretation to the final response
        final_response.interpretations.append(interpretation)
        
        log_type: str = interpretation.log_type
        thoughts: str = interpretation.thoughts
        intent: str = interpretation.intent
        args: dict[str, Any] = interpretation.args

        messages.append(
            ChatCompletionAssistantMessageParam(
                role="assistant",
                content=observation
            )
        )

        # Clean up messages to prevent memory issues
        if len(messages) > max_messages:
            # Keep system message and last max_messages-1 messages
            messages = [messages[0]] + messages[-(max_messages-1):]

        print(json.dumps(interpretation.model_dump(), ensure_ascii=False, indent=2))
        print("-" * 25)

        if intent in function_mappings:
            function = function_mappings[intent]
            result = function(**args)
            print(f"Function result: {result}")

            # Pushing the function call result to the messages array
            messages.append(ChatCompletionAssistantMessageParam(
                role="assistant",
                content=str({
                    "intent": f"{intent}_result",
                    "observation": result,
                })
            ))
            
            # Clean up messages after function result too
            if len(messages) > max_messages:
                messages = [messages[0]] + messages[-(max_messages-1):]

            if intent == "done_for_now":
                # Extract and display the diagnosis message prominently
                diagnosis_message = args.get("message", "No diagnosis message found")
                print("\n" + "="*80)
                print("FINAL DIAGNOSIS AND TROUBLESHOOTING STEPS:")
                print("="*80)
                print(diagnosis_message)
                print("="*80)
                
                # Print the complete final response with all interpretations
                print("\n" + "="*50)
                print("COMPLETE ANALYSIS LOG:")
                print("="*50)
                print(json.dumps(final_response.model_dump(), ensure_ascii=False, indent=2))
                break
        else:
            raise ValueError("Invalid intent")


    except ValidationError as e:
        print(f"Erreur de validation du modèle Response: {e}")

    except Exception as e:
        print(f"Erreur de décodage JSON: {e}")