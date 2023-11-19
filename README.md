# Large Language Model State Machine (llmstatemachine)

[![Version](https://img.shields.io/pypi/v/llmstatemachine.svg)](https://pypi.python.org/pypi/llmstatemachine)
[![Downloads](http://pepy.tech/badge/llmstatemachine)](http://pepy.tech/project/llmstatemachine)

## Introduction

The llmstatemachine library merges a state machine approach with advanced language 
models like GPT, enhancing their decision-making capabilities. This library is designed to 
steer agents, built using these models, on a defined path. It achieves this by using the 
agent's chat history and custom tools you create using regular Python functions.

This setup means the agent remembers past interactions with the tools (chat history) and uses this 
memory, along with the tools you define, to make informed decisions. 
The prototype runs on the OpenAI chat model and enforces the execution of 
these Python function-based tools.

The core focus of this project is to develop and explore workflows for an agent 
using a state machine structure, where the agent's conversational abilities and
memory (chat history) are central.

Function description JSONs are automatically generated with LLM from the function source.

## Installation
```bash
pip install llmsstatemachine
```

## Usage
To use the Large Language Model State Machine, follow these steps:

1. Have OPENAI_API_KEY exported in your environment.
2. Initialize a WorkflowAgentBuilder.
3. Define states and their respective transitions.
4. Build the workflow agent and add a system message to it.
5. Run model step by step until DONE.

## Example: Memory Game Agent

Consider a memory game, where you need to remember and match hidden pairs -
you don't see everything at once. Our library makes a language model based 
agent play such games. Memory is the chat history.
This showcases how our library can be applied to scenarios 
where you need to make decisions with limited information.
Also note that the game mechanisms are not forced, agent might do illegal moves. 

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


def display_board(argument: str) -> Tuple[str, str]:
    board_state = " ".join(f'{i}:{deck[i] if board[i] else "X"}' for i in range(len(deck)))
    return f"display_board: (position:value or X if hidden) {board_state}", "INIT"


def flip_card(argument: str) -> Tuple[str, str]:
    position = int(argument)
    if board[position]:
        board[position] = False
        print(f"< debug not shown to agent {display_board('')[0]} >")
        return f"flip_card: Hide card at position {position}.", "INIT"
    board[position] = True
    print(f"< debug not shown to agent {display_board('')[0]} >")
    next_state = "COMPLETE" if all(board) else "INIT"
    return f"flip_card: Showing card at position {position}. Value is {deck[position]}.", next_state


def game_done(argument: str) -> Tuple[str, str]:
    """Call this to end the game"""
    return argument, "DONE"


builder = WorkflowAgentBuilder()
builder.add_state_and_transitions("INIT", {flip_card, display_board})
builder.add_state_and_transitions("COMPLETE", {game_done})
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
    memory_game_agent.step()
print("-= OK =-")

```
Example output from game play
```shell
...
================================================================================
tokens: 3642 total; 62 completion; 3580 prompt
================================================================================
AI: The card on position 18 shows a 7. I remember seeing a 7 long ago, it was at
 position 2. So I will flip the card at position 2 to check if it matches.
flip_card '2'
< debug not shown to agent display_board: 9 5 7 9 8 8 1 5 6 4 2 4 6 X 10 2 10 1 7 X >
flip_card: Showing card at position 2. Value is 7.
================================================================================
tokens: 3757 total; 86 completion; 3671 prompt
================================================================================
AI: We found another matching pair! The cards at positions 2 and 18 both have the
 value 7. At this point, we have only two unknown cards remaining. Since all other
  pairs have been found, these last two cards must form a pair as well. Let's flip
   the card at position 19 to see its value.
flip_card '19'
< debug not shown to agent display_board: 9 5 7 9 8 8 1 5 6 4 2 4 6 X 10 2 10 1 7 3 >
flip_card: Showing card at position 19. Value is 3.
================================================================================
tokens: 3837 total; 51 completion; 3786 prompt
================================================================================
AI: As I thought, the last card is a 3, which matches with the card at position 13
 we discovered earlier. Let's flip it to confirm.
flip_card '13'
< debug not shown to agent display_board: 9 5 7 9 8 8 1 5 6 4 2 4 6 3 10 2 10 1 7 3 >
flip_card: Showing card at position 13. Value is 3.
================================================================================
tokens: 3872 total; 52 completion; 3820 prompt
================================================================================
AI: The last pair matched as expected. I have now found all the pairs in the game.
 The game has been solved.
game_done 'Found all pairs. The game has been solved successfully.'
Found all pairs. The game has been solved successfully.
-= OK =-
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
