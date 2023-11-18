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

Here is a simple memory game playing agent.

```python
import random
from typing import Tuple

from dotenv import load_dotenv

load_dotenv()

from llmstatemachine import WorkflowAgentBuilder


def initialize_game(num_pairs):
    """Create and shuffle the deck, then display it as a hidden board."""
    init_deck = list(range(1, num_pairs + 1)) * 2
    random.shuffle(init_deck)
    return init_deck, [False] * len(init_deck)


deck, board = initialize_game(10)


def flip_card(argument: str) -> Tuple[str, str]:
    """Turn or flip a card at given position.
    Shows the value of that card or hides it.

    Parameters
    ----------
    argument : str
       Position number as text. Positions are from 0 to 9.
    """
    position = int(argument)
    if board[position]:
        board[position] = False
        return f"flip_card: Hide card at position {position}.", "INIT"
    board[position] = True
    return f"flip_card: Showing card at position {position}. Value is {deck[position]}.", "INIT"


def game_done(argument: str) -> Tuple[str, str]:
    """Call this to end the game when it has been solved.

        Parameters
        ----------
        argument : str
          Reasoning about game end.
    """
    return argument, "DONE"


builder = WorkflowAgentBuilder()
builder.add_state_and_transitions("INIT", {flip_card, game_done})
builder.add_end_state("DONE")

memory_game_agent = builder.build()
memory_game_agent.add_system_message("You are a player of memory game. " +
                                     "In this game you have 10 number pairs in 20 cards. " +
                                     "Cards have been shuffled and they are all face down. " +
                                     "You may flip a card to see the value. " +
                                     "According to the rules of the memory game you can check a pair. " +
                                     "If they are not a pair you must flip them back hidden. " +
                                     "Once you have all pairs found and shown the game is done.")

while memory_game_agent.current_state != "DONE":
    result = memory_game_agent.step()
    print(result)
print("-= OK =-")
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
