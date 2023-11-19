import json
from typing import Dict, Callable, Any, Tuple, List
from .function import create_definition, FunctionDefinition

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionMessage,
    completion_create_params,
)

TransitionFunction = Callable[[...], Tuple[str, str]]
FUNCTION_NAME = "ActionSelector"
MODEL = "gpt-4" # "gpt-4-1106-preview"


class WorkflowAgent:
    def __init__(self, transitions: Dict[str, Dict[str, TransitionFunction]]):
        if "INIT" not in transitions:
            raise Exception("Must define INIT state")
        self._transitions: Dict[str, Dict[str, TransitionFunction]] = transitions
        self._current_state = "INIT"
        self._messages: List[ChatCompletionMessageParam] = []
        self._client = OpenAI()
        self._func_defs: Dict[TransitionFunction, FunctionDefinition] = dict()
        for name_dict in self._transitions.values():
            for func in name_dict.values():
                if func not in self._func_defs:
                    print(repr(func))
                    self._func_defs[func] = create_definition(func)

    def trigger(self, function_call: str, args: List[Any]) -> str:
        transition_func = self._transitions[self._current_state].get(function_call)
        if transition_func:
            try:
                result, next_state = transition_func(*args)
            except Exception as e:
                # Function raised an exception.
                # No state update and returning exception.
                return str(e)
            self._current_state = next_state
            return result
        # Model trying to call something that is not allowed
        # State stays the same and let's just report back illegal move.
        return (
            f"Illegal function call '{function_call}' in current state."
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
            definition = self._func_defs[func]
            actions.append(definition["function_name"])
            action_descriptions.append(definition["function_name"] + ": " + definition["function_description"])
            argument_descriptions.append(
                f"For {definition['function_name']} argument: {definition['argument_description']}"
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
