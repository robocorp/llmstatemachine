# Large Language Model State Machine

# WIP

NOTE! This project is at this point a draft and a technical concept exploring state machine use for driving LLM Agents to success.
 
## Introduction
The Large Language Model State Machine is a sophisticated framework for building state-driven workflow agents using large language models, like GPT-4. It's designed to streamline the process of handling complex workflows and decision-making processes in automated systems.

## Installation
```bash
# Clone the repository
git clone https://github.com/robocorp/llm_state_machine

# Install dependencies (if any)
pip install [dependencies]
```

## Usage
To use the Large Language Model State Machine, follow these steps:

1. Initialize a WorkflowAgentBuilder.
2. Define states and their respective transitions.
3. Build the workflow agent and add messages to it.
4. Run model step by step until DONE.

## Example

```python

def focus(argument: str):
    """when searching for texts in the html,

    Parameters
    ----------
    argument : str
        The focused text to find from html.
    """
    output = html_explorer(html_content, focus_text=argument, max_total_length=3000)
    return f"""focus "{argument}":\n```\n{output}\n```""", "INIT"

...

builder = WorkflowAgentBuilder()
builder.add_state_and_transitions("INIT", {focus, select})
builder.add_state_and_transitions("SELECTED_NON_EMPTY", {focus, select, validate})
builder.add_state_and_transitions("VALIDATED", {focus, select, validate, result})
builder.add_end_state("DONE")
workflow_agent = builder.build()
workflow_agent.add_message(
    {
        "role": "system",
        "content": "You are a helpful HTML css selector finding assistant.",
    }
)
workflow_agent.add_message(
    {
        "role": "user",
        "content": (
            "Assignment: Create CSS Selectors Based on Text Content\n"
            "Your task is to develop CSS selectors that can target HTML elements containing specific text contents. "
            "You are provided with a list of example texts. Use these examples to create selectors that can identify "
            "elements containing these texts in a given HTML structure.\n\n"
            "Instructions:\n"
            f"- Use the provided list of examples: {examples_str}.\n"
            "Your goal is to create selectors that are both precise and efficient, tailored to the specific"
            " content and structure of the HTML elements."
        ),
    }
)
for message in workflow_agent.messages:
    print(str(message)[:160])
print(">" * 80)
res = "NO RESULT"
while workflow_agent.current_state != "DONE":
    res = workflow_agent.step()
print(res)
```

## API Reference

### WorkflowAgentBuilder

- `add_state_and_transitions(state_name, transition_functions): Define a state and its transitions.`
- `add_end_state(state_name): Define an end state for the workflow.`
- `build(): Builds and returns a WorkflowAgent.`

### WorkflowAgent

- `trigger(function_call, args): Triggers a transition in the workflow.`
- `add_message(message): Adds a message to the workflow.`
- `step(): Executes a step in the workflow.`

## License
Apache 2.0
