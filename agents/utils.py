from copy import deepcopy
from pprint import pprint
from typing import Any, Dict, List, Tuple

import numpy as np


class TickSate:
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        
        # defaults
        self._body = None
        self._sight = None
        self._range = None
        self._step = None
        self._traverse = None
        self._score = None

        self._processed_sight = None
            
    @property
    def body(self) -> List[Tuple[int, int]]:
        if self._body is None:
            self._body = list(map(tuple, self.state.get('body', [])))
        
        return self._body 
    
    @property
    def sight(self) -> Dict[str, Dict[str, int]]:
        if self._sight is None:
            self._sight = self.state.get('sight', {})
        
        return self._sight 
    
    @property
    def processed_sight(self) -> Dict[Tuple[int, int], int]:
        if self._processed_sight is not None:
            return self._processed_sight

        resp = {}
        for y in self.sight:
            y_int = int(y)
            for x in self.sight[y]:
                resp[y_int, int(x)] = self.sight[y][x]

        self._processed_sight = resp
        return self._processed_sight
    
    @property
    def range(self) -> int:
        if self._range is None:
            self._range = self.state.get('range', 1)
        
        return self._range 

    @property
    def step(self) -> int:
        if self._step is None:
            self._step = self.state.get('step', 0)
        
        return self._step 
    
    @property
    def traverse(self) -> bool:
        if self._traverse is None:
            self._traverse = self.state.get('traverse', True)
        
        return self._traverse 

    @property
    def score(self) -> int:
        if self._score is None:
            self._score = self.state.get('score', 0)
        
        return self._score

    def print(self, *, width=100):
        pprint(self.state, width=width)

class Maze:
    def __init__(self, maze: List[Tuple[int, int]]):
        self.height = len(maze)
        self.width = len(maze[0])

        self.maze = np.asarray(maze, np.int8)

        self._last_update = 0
        
    def update_maze(self, tick_info: TickSate):
        # check if map already updated
        if self._last_update >= tick_info.step:
            return
        self._last_update = tick_info.step
        
        # remove snake remenants
        self.maze[self.maze == 4] = 0

        # sight
        for (y, x), val in tick_info.processed_sight.items():
            self.maze[y, x] = val

    def verbose_print(self, tick_info: TickSate = None):
        inverse = lambda x: "\033[;7m" + x + '\033[0m'
        normal = lambda x: x

        sight_elems = tick_info.processed_sight if tick_info is not None else set()

        maze = self.maze.transpose()

        print("#"*(len(maze[0]) + 2))

        for i, row in enumerate(maze):
            print("#", end="")

            for j, cell in enumerate(row):
                color_f = inverse if (j, i) in sight_elems else normal

                print(color_f(" #AFS?"[cell]), end='')
                
            print("#")
        
        print("#"*(len(maze[0]) + 2))


def print_maze(maze, snake_body=None):
    maze = deepcopy(maze)
    maze = [list(row) for row in zip(*maze)]

    if snake_body is None:
        snake_body = []

    print("#"*(len(maze[0]) + 2))

    for i, row in enumerate(maze):
        print("#", end="")

        for j, cell in enumerate(row):
            if cell == 1:
                print("#", end='')
            elif (j, i) in snake_body or cell == 4:
                print("S", end='')
            elif cell == -1:
                print("?", end='')
            else:
                print(" ", end='')
        print("#")
    
    print("#"*(len(maze[0]) + 2))

def print_mazes(mazes, snake_bodys):
    mazes = deepcopy(mazes)

    mazes = [[list(row) for row in zip(*maze)] for maze in mazes]

    out = ['']*len(mazes[0])
    top = "#"*(len(mazes[0][0]) + 2)
    print(f"{top} "*len(mazes))
    for maze, snake_body in zip(mazes, snake_bodys):
        for i, row in enumerate(maze):
            out[i] += "#"

            for j, cell in enumerate(row):
                if cell == 1:
                    out[i] += "#"
                elif cell == 2:
                    out[i] += "A"
                elif cell == 3:
                    out[i] += "F"
                elif (j, i) in snake_body or cell == 4:
                    out[i] += "S"
                elif cell == -1:
                    out[i] += "?"
                else:
                    out[i] += " "
            
            out[i] += "# "

    for i in out:
        print(i)

    print(f"{top} "*len(mazes))