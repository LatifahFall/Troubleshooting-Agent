from utils import get_app_logs, get_nginx_logs, read_file, ask_for_clarification, provide_further_assistance, provide_diagnosis, get_app_log_directory, get_nginx_log_directory, system_check, connectivity_check, get_app_history
from memory_manager import MemoryManager
from dotenv import load_dotenv
from openai import OpenAI
from jinja2 import Template
from typing import Any, Callable, Dict, Optional, Union
from pydantic import BaseModel, ValidationError, ConfigDict
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionSystemMessageParam, \
    ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam
import json
from tools import ToolFactory, ReadFile, AskForClarification, ProvideFurtherAssistance, ListDirectory, DoneForNow

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
            "returns": "string" if name in ["read_file", "ask_for_clarification", "provide_further_assistance"] else
                       "list of strings" if name in ["find_app_log_files", "read_log_files"] else
                       "list of dicts" if name in ["get_app_logs", "get_nginx_logs"] else
                       "None" if name in ["done_for_now"] else
                       "string"
        }
        for name, func in capabilities.items()
    }

    return template.render(capabilities=capabilities_context)

SYSTEM_PROMPT = load_dynamic_prompt("system_prompt_short.j2", function_mappings)

print(SYSTEM_PROMPT)

client = OpenAI()

class Interpretation(BaseModel):
    #log_type: str
    thoughts: str
    intent: str
    # args: Union[ReadFile, AskForClarification, ProvideFurtherAssistance]
    args: Union[ReadFile, AskForClarification, ProvideFurtherAssistance, ListDirectory, DoneForNow]  # Use your tool classes!

    model_config = ConfigDict(extra="forbid")
    
    #class Config:
    #    extra = "forbid"  # This prevents additional properties

class Response(BaseModel):
    interpretations: list[Interpretation]

messages: list[ChatCompletionMessageParam] = list([
    ChatCompletionSystemMessageParam(content=SYSTEM_PROMPT, role="system"),
])

# Initialize memory manager
memory_manager = MemoryManager()

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
            # response_format={"type": "json_object"},
            #put my structured output here
            temperature=0.7,
            response_format=Interpretation
        )

        print(json.dumps(completion.choices[0].message.to_dict(), ensure_ascii=False, indent=2))
        # observation = completion.choices[0].message.parsed

        #print(observation)
        #print(type(observation))

    except Exception as e:
        print(f"Erreur lors de l'appel à OpenAI: {e}")
        break

    # print(completion.choices[0].message.observation)

    interpretation = completion.choices[0].message.parsed

    if interpretation is None:
        raise ValueError("Received empty response from OpenAI")
    
    try: 
        # response_dict = json.loads(observation)
        # Parse the interpretation from the response
        # interpretation = observation
        
        # Add this interpretation to the final response
        final_response.interpretations.append(interpretation)
        
        # log_type: str = interpretation.log_type
        thoughts: str = interpretation.thoughts
        intent: str = interpretation.intent
        args: dict[str, Any] = interpretation.args.model_dump()

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

        print(json.dumps(interpretation.model_dump(), ensure_ascii=False, indent=2))
        print("-" * 25)

        if intent in function_mappings:
            function = function_mappings[intent]
            result = function(**args)
            print(f"Function result: {result}")
            print(f"Intent: {intent}")

            # For user input functions, add the user's response as a user message
            if intent in ["ask_for_clarification", "provide_further_assistance"]:
                print(f"Adding user response to conversation: {result}")
                messages.append(ChatCompletionUserMessageParam(
                    role="user",
                    content=result
                ))
            else:
                # For other functions, add the result as an assistant message
                print(f"Adding function result to conversation: {result}")
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
                # Extract and display the termination message
                termination_message = args.get("message", "No termination message found")
                print("\n" + "="*80)
                print("ANALYSIS COMPLETE")
                print("="*80)
                print(termination_message)
                print("="*80)
                
                # Save conversation to memory
                try:
                    print(f"\n💾 Saving conversation to memory...")
                    memory_file = memory_manager.save_conversation(".", final_response.model_dump())
                    print(f"✅ Conversation saved to memory: {memory_file}")
                except Exception as e:
                    print(f"\n⚠️ Failed to save memory: {e}")
                    import traceback
                    traceback.print_exc()
                
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