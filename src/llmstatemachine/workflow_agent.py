import inspect
import json
import re
from typing import Dict, Callable, Any, Tuple, List

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionMessage,
    completion_create_params,
)

TransitionFunction = Callable[[...], Tuple[str, str]]
FUNCTION_NAME = "ActionSelector"
MODEL = "gpt-4" # "gpt-4-1106-preview"


def parse_function_docstring(func: Callable):
    """
    Parses the docstring of a given function to extract the action description and parameter descriptions
    following the NumPy docstring convention.

    Parameters
    ----------
    func : function
        The function whose docstring is to be parsed.

    Returns
    -------
    action_name : str
        The name of the action (function).
    action_description : str
        The general description of the action (function).
    parameters : dict
        A dictionary where keys are parameter names and values are their descriptions.
    """
    # Get the docstring of the function
    docstring = inspect.getdoc(func)
    if not docstring:
        return func.__name__, "No docstring provided", {}

    # Split the docstring into lines
    lines = docstring.strip().split("\n")

    # Initialize variables
    action_description = ""
    parameters = {}
    param_mode = False
    current_param = ""

    # Iterate through lines to parse the docstring
    for line in lines:
        # Check for the start of the 'Parameters' section
        if line.strip().lower() == "parameters":
            param_mode = True
            continue

        if param_mode:
            # Detect parameter line (usually starts with parameter name)
            param_match = re.match(r"^(\w+)\s*:", line)
            if param_match:
                current_param = param_match.group(1)
                parameters[current_param] = ""
            elif current_param:
                # Append description to the current parameter
                parameters[current_param] += line.strip() + " "
        else:
            # Before 'Parameters' section, it's part of the action description
            action_description += line.strip() + " "

    # Clean up the final descriptions
    action_description = action_description.strip()
    for param in parameters:
        parameters[param] = parameters[param].strip()

    return func.__name__, action_description, parameters


class WorkflowAgent:
    def __init__(self, transitions: Dict[str, Dict[str, TransitionFunction]]):
        if "INIT" not in transitions:
            raise Exception("Must define INIT state")
        self._transitions = transitions
        self._current_state = "INIT"
        self._messages: List[ChatCompletionMessageParam] = []
        self._client = OpenAI()

    def trigger(self, function_call: str, args: List[Any]) -> str:
        transition_func = self._transitions[self._current_state].get(function_call)
        if transition_func:
            result, next_state = transition_func(*args)
            self._current_state = next_state
            return result
        raise ValueError(
            f"No valid transition for event '{function_call}' in state '{self._current_state}'"
        )

    def add_message(self, message: ChatCompletionMessageParam | ChatCompletionMessage):
        self._messages.append(message)

    def add_system_message(self, content: str):
        self.add_message({
            "role": "system",
            "content": content
        })

    @property
    def current_state(self):
        return self._current_state

    @property
    def messages(self) -> List[ChatCompletionMessageParam]:
        return self._messages

    @property
    def last_message(self) -> ChatCompletionMessageParam | None:
        if len(self._messages) < 1:
            return None
        return self._messages[-1]

    def function_def_action_selector(self) -> completion_create_params.Function:
        actions = []
        action_descriptions = []
        argument_descriptions = []
        for func in self._transitions[self._current_state].values():
            func_name, action_description, parameters = parse_function_docstring(func)
            actions.append(func_name)
            action_descriptions.append(func_name + ": " + action_description)
            argument_descriptions.append(
                f"For {func_name} argument: {parameters['argument']}"
            )
        return {
            "description": "ActionSelector is a tool that selects next action",
            "name": "ActionSelector",
            "parameters": {
                "type": "object",
                "properties": {
                    "thinking": {
                        "type": "string",
                        "description": (
                            "Reflection about latest learnings."
                            "Assume last function result content will be purged to save space."
                            "Logical thinking about the problem leading to taking this action."
                        ),
                    },
                    "action": {
                        "type": "string",
                        "enum": actions,
                        "description": "\n".join(action_descriptions),
                    },
                    "argument": {
                        "type": "string",
                        "description": "\n".join(argument_descriptions),
                    },
                },
                "required": ["thinking", "action", "argument"],
            },
        }

    def step(self):
        response = self._client.chat.completions.create(
            model=MODEL,
            messages=self._messages,
            functions=[self.function_def_action_selector()],
            function_call={"name": "ActionSelector"},
        )
        print("=" * 80)
        print(
            f"tokens: {response.usage.total_tokens} total; {response.usage.completion_tokens} completion; {response.usage.prompt_tokens} prompt"
        )
        print("=" * 80)
        msg = response.choices[0].message
        assert msg.function_call
        res = execute_function_call(msg.function_call, self)
        print(res[:120] + ("..." if len(res) > 120 else ""))
        self.add_message(msg)
        self.add_message(
            {"role": "function", "name": msg.function_call.name, "content": res}
        )
        return res


def execute_function_call(function_call, workflow_agent: WorkflowAgent) -> str:
    if function_call.name != FUNCTION_NAME:
        return f"Error: function {function_call.name} does not exist"
    args = json.loads(function_call.arguments)
    print(f'AI: {args["thinking"]}')
    action = args["action"]
    argument = args["argument"]
    print(f"""{action} '{argument}'""")
    return workflow_agent.trigger(action.lower(), [argument])


class WorkflowAgentBuilder:
    def __init__(self):
        self._transitions: Dict[str, Dict[str, TransitionFunction]] = dict()

    def add_state_and_transitions(
        self, state_name: str, transition_functions: set[TransitionFunction]
    ):
        if state_name in self._transitions:
            raise Exception(f"State {state_name} transition already defined")
        self._transitions[state_name] = {
            func.__name__: func for func in transition_functions
        }
        return self

    def add_end_state(self, state_name: str):
        if state_name in self._transitions:
            raise Exception(f"State {state_name} already defined")
        self._transitions[state_name] = {}
        return self

    def build(self) -> WorkflowAgent:
        if "INIT" not in self._transitions:
            raise Exception("Must define INIT state")
        return WorkflowAgent(self._transitions)
