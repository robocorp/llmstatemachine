from typing import Tuple

from mazelib import Maze
from mazelib.generate.Prims import Prims


class MazePlayer:
    def __init__(self, maze, start):
        """Initialize the maze player with the given maze and start position."""
        self.maze = maze
        self.position = start
        self.directions = {
            'UP': (-1, 0),
            'DOWN': (1, 0),
            'LEFT': (0, -1),
            'RIGHT': (0, 1)
        }

    def move(self, direction):
        dy, dx = self.directions[direction]
        y, x = self.position

        while not self.is_blocked(y, x, direction):
            print(f"Moving {direction}: from ({y}, {x})")  # Debug print
            new_y, new_x = y + dy, x + dx
            if 0 <= new_y < len(self.maze.grid) and 0 <= new_x < len(self.maze.grid[0]):
                y, x = new_y, new_x
                self.position = (y, x)
            else:
                print("Stopped: Out of bounds")  # Debug print
                break

            print(f"Moved to ({y}, {x})")  # Debug print
            if self.is_cross_section(y, x, direction):
                print("Stopped: Cross-section or dead end")
                return self.position

        print("Stopped: Path is blocked")  # Debug print
        return self.position

    def is_cross_section(self, y, x, direction):
        """Check if the current position is a cross-section or if the end 'E' is reached."""
        print(f"Checking cross-section at ({y}, {x}) in direction {direction}")

        if self.is_end_nearby(y, x):
            print("End is nearby")
            return True

        # Check for openings directly adjacent in perpendicular directions
        perp_openings = False
        if direction in ['UP', 'DOWN']:
            # Check LEFT and RIGHT for perpendicular openings
            if x > 0 and self.maze.grid[y][x - 1] == 0:
                perp_openings = True
                print(f"Open path in perpendicular direction LEFT at ({y}, {x - 1})")
            if x < len(self.maze.grid[0]) - 1 and self.maze.grid[y][x + 1] == 0:
                perp_openings = True
                print(f"Open path in perpendicular direction RIGHT at ({y}, {x + 1})")
        elif direction in ['LEFT', 'RIGHT']:
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

    def is_path_open(self, y, x):
        """Check if a given path is open (not a wall) and within the maze bounds."""
        return 0 <= y < len(self.maze.grid) and 0 <= x < len(self.maze.grid[0]) and self.maze.grid[y][x] == 0

    def is_end_nearby(self, y, x):
        """Check if the end 'E' is next to the player's position."""
        end_y, end_x = self.maze.end
        return (abs(end_y - y) <= 1 and end_x == x) or (abs(end_x - x) <= 1 and end_y == y)

    def is_blocked(self, y, x, direction):
        """Check if movement in the current direction is blocked."""
        dy, dx = self.directions[direction]
        next_y, next_x = y + dy, x + dx
        return not (0 <= next_y < len(self.maze.grid) and 0 <= next_x < len(self.maze.grid[0]) and self.maze.grid[next_y][next_x] == 0)

    def is_at_end(self):
        y, x = self.position
        return self.is_end_nearby(y, x)


def display_maze(maze, player):
    start_y, start_x = maze.start
    end_y, end_x = maze.end
    player_y, player_x = player.position

    for y, row in enumerate(maze.grid):
        for x, cell in enumerate(row):
            if (y, x) == (player_y, player_x):
                print('X', end='')
            elif (y, x) == (start_y, start_x):
                print('S', end='')
            elif (y, x) == (end_y, end_x):
                print('E', end='')
            else:
                print('#' if cell == 1 else ' ', end='')
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
while True:
    display_maze(m, player)
    direction = input("Enter direction (UP, DOWN, LEFT, RIGHT) or 'STOP' to end: ").upper()
    if direction == 'STOP':
        break
    new_position = player.move(direction)
    print("New Position:", new_position)
    if player.is_at_end():
        print("Found through the maze!")
        break
