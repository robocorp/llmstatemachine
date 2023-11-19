import inspect
import json
from typing import Callable, TypedDict

from openai import OpenAI


class FunctionDefinition(TypedDict):
    function_name: str
    function_description: str
    argument_description: str


def create_definition(func: Callable) -> FunctionDefinition:
    source = inspect.getsource(func)
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"""Extract function metadata from the following function definition:
```
{source}
```             
"""
            }
        ],
        functions=[{
            "description": "FunctionDefinition is a tool for metadata extraction",
            "name": "FunctionDefinition",
            "parameters": {
                "type": "object",
                "properties": {
                    "thinking": {
                        "type": "string",
                        "description": (
                            "Logical thinking about function metadata extraction and draft of the answer."
                        ),
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Name of the function."
                    },
                    "function_description": {
                        "type": "string",
                        "description": "Short well thought description of what the function is used for."
                    },
                    "argument_description": {
                        "type": "string",
                        "description": "Short well thought description of what the function argument is used for."
                    }
                },
                "required": ["thinking", "function_name", "function_description", "argument_description"],
            },
        }],
        function_call={"name": "FunctionDefinition"},
    )
    msg = response.choices[0].message
    assert msg.function_call
    print(msg.function_call)
    print(msg.tool_calls)
    args: FunctionDefinition = json.loads(msg.function_call.arguments)
    return args

