# from memory_manager import MemoryManager
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template
from typing import Any, Callable, Union
from pydantic import BaseModel, ValidationError, ConfigDict
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, \
    ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam
import json
from tools import ToolFactory, ReadFile, AskForClarification, ProvideFurtherAssistance, ListDirectory, DoneForNow, SystemCheck, ConnectivityCheck

load_dotenv()

tool_factory = ToolFactory()
tool_mappings = tool_factory.create_function_mappings()

function_mappings: dict[str, Callable[..., Any]] = {
    **tool_mappings
}

def load_dynamic_prompt(template_path: str, capabilities: dict[str, Callable[..., Any]]) -> str:
    from inspect import signature

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    capabilities_context = {
        name: {
            "signature": str(signature(func)),
            "returns": "string" if name in ["read_file", "ask_for_clarification", "provide_further_assistance", "list_directory", "done_for_now"] else
                       "list of strings" if name in ["find_app_log_files", "read_log_files"] else
                       "list of dicts" if name in ["get_app_logs", "get_nginx_logs"] else
                       "string"
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

# Initialize memory manager
# memory_manager = MemoryManager()

# Initialize a response object to collect all interpretations
final_response = Response(interpretations=[])

iteration: int = 0
max_iterations = 25
max_messages = 20  # Keeping only last 20 messages to prevent memory issues

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
                
                # Save conversation to memory
                # try:
                #     print(f"\n💾 Saving conversation to memory...")
                #     memory_file = memory_manager.save_conversation(".", final_response.model_dump())
                #     print(f"✅ Conversation saved to memory: {memory_file}")
                # except Exception as e:
                #     print(f"\n⚠️ Failed to save memory: {e}")
                #     import traceback
                #     traceback.print_exc()
                
                break
        else:
            raise ValueError("Invalid action type")


    except ValidationError as e:
        print(f"Erreur de validation du modèle Response: {e}")

    except Exception as e:
        print(f"Erreur de décodage JSON: {e}")