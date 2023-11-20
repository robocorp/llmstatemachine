# Large Language Model State Machine (llmstatemachine)

[![Version](https://img.shields.io/pypi/v/llmstatemachine.svg)](https://pypi.python.org/pypi/llmstatemachine)
[![Downloads](http://pepy.tech/badge/llmstatemachine)](http://pepy.tech/project/llmstatemachine)

## Introduction

llmstatemachine is a library for creating agents with GPT-based language models and state machine logic.

- **Chat History as Memory**: Leverages large context window models, making chat history the primary source of agent memory.
- **Custom Python Functions with JSON Generation**: Allows the creation of functions for agent actions, with automatic JSON definition generation for both agent and OpenAI API interaction.
- **Controlled Actions**: Ensures agents are restricted to specific, well-defined actions in each state for reliable and predictable behavior.

llmstatemachine is exploring how to make agents that use conversational tools and the conversation history as memory,
utilizing a state machine structure together with Generative AI.

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
you don't see everything at once. This is a partially observable environment. llmstatemachibe enables a language model based 
agent play such games.
This showcases how the library can be applied to scenarios 
where you need to make decisions with limited information.
Also note that the game mechanisms are not forced and agent can do illegal moves. 

```python
import random

from dotenv import load_dotenv

load_dotenv()

from llmstatemachine import WorkflowAgentBuilder, set_next_state


def initialize_game(num_pairs):
    """Create and shuffle the deck, then display it as a hidden board."""
    init_deck = list(range(1, num_pairs + 1)) * 2
    random.shuffle(init_deck)
    return init_deck, [False] * len(init_deck)


deck, board = initialize_game(10)


def display_board(argument: str) -> str:
    board_state = " ".join(
        f'{i}:{deck[i] if board[i] else "X"}' for i in range(len(deck))
    )
    return f"display_board: (position:value or X if hidden) {board_state}"


def flip_card(argument: str) -> str:
    position = int(argument)
    if board[position]:
        board[position] = False
        print(f"< debug not shown to agent {display_board('')} >")
        set_next_state("INIT")
        return f"flip_card: Hide card at position {position}."
    board[position] = True
    print(f"< debug not shown to agent {display_board('')} >")
    if all(board):
        set_next_state("COMPLETE")
    return f"flip_card: Showing card at position {position}. Value is {deck[position]}."


def game_done(argument: str) -> str:
    """Call this to end the game"""
    set_next_state("DONE")
    return argument


memory_game_agent = (
    WorkflowAgentBuilder()
    .add_system_message(
        "You are a player of memory game. "
        + "In this game you have 10 number pairs in 20 cards. "
        + "Cards have been shuffled and they are all face down. "
        + "You may flip a card to see the value. "
        + "According to the rules of the memory game you can check a pair. "
        + "If they are not a pair you must flip them back hidden. "
        + "Once you have all pairs found and shown the game is done."
    )
    .add_state_and_transitions("INIT", {flip_card, display_board})
    .add_state_and_transitions("COMPLETE", {game_done})
    .add_end_state("DONE")
    .build()
)
memory_game_agent.run()
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
