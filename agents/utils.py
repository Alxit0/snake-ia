from pprint import pprint
from typing import Any, Dict, List, Tuple


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

    def print(self):
        pprint(self.state, width=100)
    
def print_maze(maze, food=None, snake_body=None):
    # maze = deepcopy(maze)
    # maze = [list(row) for row in zip(*maze)]

    if snake_body is None:
        snake_body = []

    print(f"height: {len(maze)}\nwidth: {len(maze[0])}")
    print("#"*(len(maze[0]) + 2))

    for i, row in enumerate(maze):
        print("#", end="")

        for j, cell in enumerate(row):
            if cell == 1:
                print("#", end='')
            elif food is not None and food == [i, j]:
                print("A", end='')
            elif (i, j) in snake_body or cell > 1:
                print("S", end='')
            elif cell < -5:
                print("P", end='')
            else:
                print(" ", end='')
        print("#")
    
    print("#"*(len(maze[0]) + 2))


class Sepuku(Exception): ...