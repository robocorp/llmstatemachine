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
