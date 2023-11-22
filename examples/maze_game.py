from itertools import combinations
from typing import Callable

from mazelib import Maze
from mazelib.generate.Prims import Prims
from dotenv import load_dotenv

load_dotenv()

from llmstatemachine import WorkflowAgentBuilder, set_next_state


class MazePlayer:
    def __init__(self, maze, start):
        """Initialize the maze player with the given maze and start position."""
        self.maze = maze
        self.position = start
        self.directions = {
            "UP": (-1, 0),
            "DOWN": (1, 0),
            "LEFT": (0, -1),
            "RIGHT": (0, 1),
        }

    def move(self, direction: str) -> list[str]:
        dy, dx = self.directions[direction]
        y, x = self.position
        steps: list[str] = []

        while not self.is_blocked(y, x, direction):
            new_y, new_x = y + dy, x + dx
            if 0 <= new_y < len(self.maze.grid) and 0 <= new_x < len(self.maze.grid[0]):
                y, x = new_y, new_x
                self.position = (y, x)
                steps.append(f"Moving {direction}: from ({y}, {x})")
            else:
                steps.append("Stopped: Out of bounds")  # Debug print
                return steps

            if self.is_end_nearby(y, x):
                steps.append("Stopped: At the end")
                return steps

            print(f"Moved to ({y}, {x})")
            if self.is_cross_section(y, x, direction):
                steps.append("Stopped: at a cross-section")
                steps.append(
                    f"From current location ({y}, {x}) you may move: {self.free_directions().replace(':', ', ')}"
                )
                return steps

        steps.append("Stopped: Path is blocked")
        steps.append(
            f"From current location ({y}, {x}) you may move: {self.free_directions().replace(':', ', ')}"
        )
        return steps

    def is_cross_section(self, y, x, direction):
        """Check if the current position is a cross-section or if the end 'E' is reached."""
        print(f"Checking cross-section at ({y}, {x}) in direction {direction}")

        # Check for openings directly adjacent in perpendicular directions
        perp_openings = False
        if direction in ["UP", "DOWN"]:
            # Check LEFT and RIGHT for perpendicular openings
            if x > 0 and self.maze.grid[y][x - 1] == 0:
                perp_openings = True
                print(f"Open path in perpendicular direction LEFT at ({y}, {x - 1})")
            if x < len(self.maze.grid[0]) - 1 and self.maze.grid[y][x + 1] == 0:
                perp_openings = True
                print(f"Open path in perpendicular direction RIGHT at ({y}, {x + 1})")
        elif direction in ["LEFT", "RIGHT"]:
            # Check UP and DOWN for perpendicular openings
            if y > 0 and self.maze.grid[y - 1][x] == 0:
                perp_openings = True
                print(f"Open path in perpendicular direction UP at ({y - 1}, {x})")
            if y < len(self.maze.grid) - 1 and self.maze.grid[y + 1][x] == 0:
                perp_openings = True
                print(f"Open path in perpendicular direction DOWN at ({y + 1}, {x})")

        if perp_openings:
            print("Cross-section found")
            return True

        print("No cross-section or dead end found")
        return False

    def is_end_nearby(self, y, x):
        """Check if the end 'E' is next to the player's position."""
        end_y, end_x = self.maze.end
        return (abs(end_y - y) <= 1 and end_x == x) or (
            abs(end_x - x) <= 1 and end_y == y
        )

    def is_blocked(self, y, x, direction: str) -> bool:
        """Check if movement in the current direction is blocked."""
        dy, dx = self.directions[direction]
        next_y, next_x = y + dy, x + dx
        if not self.is_in_bounds(next_y, next_x):
            return True
        return self.maze.grid[next_y][next_x] == 1

    def is_in_bounds(self, y, x):
        return 0 <= y < len(self.maze.grid) and 0 <= x < len(self.maze.grid[0])

    def is_at_end(self):
        y, x = self.position
        return self.is_end_nearby(y, x)

    def free_directions(self) -> str:
        free_dirs = []
        y, x = self.position

        for direction, (dy, dx) in self.directions.items():
            new_y, new_x = y + dy, x + dx
            if self.is_in_bounds(new_y, new_x) and not self.is_blocked(y, x, direction):
                free_dirs.append(direction)

        return ":".join(sorted(free_dirs))

    def all_direction_combinations(self) -> list[tuple[str]]:
        free_dirs = sorted(self.directions.keys())
        all_combinations = []

        for r in range(1, len(free_dirs) + 1):
            for combo in combinations(free_dirs, r):
                all_combinations.append(combo)

        return all_combinations


def display_maze(maze, player):
    start_y, start_x = maze.start
    end_y, end_x = maze.end
    player_y, player_x = player.position

    for y, row in enumerate(maze.grid):
        for x, cell in enumerate(row):
            if (y, x) == (player_y, player_x):
                print("X", end="")
            elif (y, x) == (start_y, start_x):
                print("S", end="")
            elif (y, x) == (end_y, end_x):
                print("E", end="")
            else:
                print("#" if cell == 1 else " ", end="")
        print()  # New line after each row


m = Maze()
m.generator = Prims(10, 10)
m.generate()
m.generate_entrances()
print("-" * 80)
print(m.tostring(True))

print(m.grid)
print(m.start)
print(m.end)


def find_start_position_near_s(maze):
    """Find the start position near 'S' in the maze."""
    s_y, s_x = maze.start
    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Left, Right, Up, Down

    for dy, dx in directions:
        new_y, new_x = s_y + dy, s_x + dx
        if 0 <= new_y < len(maze.grid) and 0 <= new_x < len(maze.grid[0]):
            if maze.grid[new_y][new_x] == 0:
                return new_y, new_x

    return None  # No adjacent empty space found


player = MazePlayer(m, find_start_position_near_s(m))
# Example of moving the player
is_manual = False
while is_manual:
    display_maze(m, player)
    direction = input(
        "Enter direction (UP, DOWN, LEFT, RIGHT) or 'STOP' to end: "
    ).upper()
    if direction == "STOP":
        break
    new_position = player.move(direction)
    print("New Position:", new_position)
    if player.is_at_end():
        print("Found through the maze!")
        break


def move_up(argument: str) -> str:
    steps = player.move("UP")
    if player.is_at_end():
        set_next_state("DONE")
    else:
        set_next_state(player.free_directions())
    return "\n".join(steps)


def move_down(argument: str) -> str:
    steps = player.move("DOWN")
    if player.is_at_end():
        set_next_state("DONE")
    else:
        set_next_state(player.free_directions())
    return "\n".join(steps)


def move_left(argument: str) -> str:
    steps = player.move("LEFT")
    if player.is_at_end():
        set_next_state("DONE")
    else:
        set_next_state(player.free_directions())
    return "\n".join(steps)


def move_right(argument: str) -> str:
    steps = player.move("RIGHT")
    if player.is_at_end():
        set_next_state("DONE")
    else:
        set_next_state(player.free_directions())
    return "\n".join(steps)


def start(argument: str) -> str:
    set_next_state(player.free_directions())
    return f"You have just entered the maze. Your position is {player.position}. You can move from here: {player.free_directions().replace(':', ', ')}."


maze_game_agent_builder = (
    WorkflowAgentBuilder()
    .add_system_message(
        "You are a player in a 2 dimensional 10x10 maze. "
        + "Find your way through the maze."
    )
    .add_end_state("DONE")
)


def match_directions_to_callables(direction_combination) -> set[Callable]:
    callables = set()
    direction_to_function = {
        "UP": move_up,
        "DOWN": move_down,
        "LEFT": move_left,
        "RIGHT": move_right,
    }

    for direction in direction_combination:
        if direction in direction_to_function:
            callables.add(direction_to_function[direction])

    return callables


for state in player.all_direction_combinations():
    state_str = ":".join(sorted(state))
    print(state_str)
    maze_game_agent_builder.add_state_and_transitions(
        state_str, match_directions_to_callables(state)
    )


maze_game_agent_builder.add_state_and_transitions("INIT", {start})

memory_game_agent = maze_game_agent_builder.build()

print("=" * 80)
display_maze(m, player)
print("=" * 80)
memory_game_agent.run()
print("=" * 80)
display_maze(m, player)
print("=" * 80)
print("-= OK =-")
