import asyncio
from collections import deque
from copy import deepcopy
from enum import Enum
import getpass
import json
import os
from pprint import pprint as print_better
from typing import List, Tuple
import websockets

from utils import GamePacket, Sepuku, print_maze

"""
TODO:
    DONE - basic bfs search
    DONE - pick closest food
    DONE - ignore wall in TRAVERSE mode
    DONE - make side traversing acepted
    DONE - make snake do detours to closer food that apeared mid path 
    DONE - calculate bfs counting snake movement
    
    - calc closest food counting side traversing
    - make panic mode (fruit under snake)

"""


class SnakeDirection(Enum):
    Right = "s"
    Down = "d"
    Left = "w"
    Up = "a"
    Pass = " "

# general
def _calc_closest_food(game_info: GamePacket, height, width):
    hx, hy = game_info.body[0]

    def dst_to_food(pos):
        x, y, *_ = pos
        dst = abs(x - hx) + abs(y - hy)
        if not game_info.traverse:
            return dst

        for i in range(-1, 2):
            for j in range(-1, 2):
                dst = min(dst, abs((x + height * i) - hx) + abs((y + width * j) - hy))
        
        return dst

    return min(game_info.food, key=dst_to_food)


# path algo
def bfs_path(maze, start, goals, snake_body: List[Tuple[int, int]], ignore_walls=False):
    # Directions for moving in the grid: right, down, left, up
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    rows, cols = len(maze), len(maze[0])
    visited = [[False] * cols for _ in range(rows)]
    parent = [[None] * cols for _ in range(rows)]
    
    # Queue for BFS
    queue = deque([(start, 0)])
    visited[start[0]][start[1]] = True
    
    snake_search_level = 0

    maze[snake_body[-1][0]][snake_body[-1][1]] += 2
    snake_body.append(snake_body[-1])

    while queue:
        current, cur_search_lvl = queue.popleft()
        real_cur = (current[0]%rows, current[1]%cols)
        
        # If we reach the goal, reconstruct the path
        # if real_cur == goal and maze[goal[0]][goal[1]] == 0:
        if real_cur in goals:
            path = []
            while current is not None:
                path.append(current)
                current = parent[current[0]%rows][current[1]%cols]
            return path[::-1]  # Return reversed path
        
        # Explore neighbors
        for direction in directions:
            neighbor = (current[0] + direction[0], current[1] + direction[1])
            real_neighbor = (neighbor[0]%rows, neighbor[1]%cols)
            
            # Check if neighbor is within bounds and not visited
            is_inbounds = 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols
            if not (ignore_walls or is_inbounds):continue

            not_visited = not visited[real_neighbor[0]][real_neighbor[1]]
            is_empty = maze[real_neighbor[0]][real_neighbor[1]] < 1 + ignore_walls
            
            if not_visited and is_empty:

                visited[real_neighbor[0]][real_neighbor[1]] = True
                parent[real_neighbor[0]][real_neighbor[1]] = current
                queue.append((neighbor, cur_search_lvl + 1))
    
        if len(snake_body) > 0 and snake_search_level != cur_search_lvl:
            freed_pos = snake_body.pop()
            maze[freed_pos[0]][freed_pos[1]] -= 2
            snake_search_level += 1
    
    return None  # No path found

# generators
def default_gen():
    i = 0
    moves = [i for i in SnakeDirection]
    while True:
        yield moves[i%4]
        i += 1

def bfs_path_gen(maze, game_info: GamePacket):

    body = game_info.body
    start = body[0]
    goal = _calc_closest_food(game_info, len(maze), len(maze[0]))[:-1]

    # prep maze
    dynamic_body = deepcopy(body)
    maze[goal[0]][goal[1]] = 0
    for x, y in dynamic_body:
        maze[x][y] += 2

    # calc path
    goals = set((i,j) for i, j, _ in game_info.food)
    path = bfs_path(maze, start, goals, dynamic_body, ignore_walls=game_info.traverse)

    # revert maze
    for x, y in dynamic_body:
        maze[x][y] -= 2
    
    if path is None:
        raise Sepuku

    # prepare directions
    orders = []
    cur = None
    for next_pos in path:
        if cur is None:
            cur = next_pos
            continue
        
        # [x, y]
        move = " "
        if cur[0] == next_pos[0]:
            # horizontal move
            if cur[1] < next_pos[1]:
                move = SnakeDirection.Right
            else:
                move = SnakeDirection.Left
        else:
            # vertical move
            if cur[0] < next_pos[0]:
                move = SnakeDirection.Down
            else:
                move = SnakeDirection.Up
            pass
        
        cur = next_pos
        orders.append(move)
    
    # give directions
    rows, cols = len(maze), len(maze[0])
    _real_path = [(i%rows, j%cols) for i, j in path]
    for i,j in _real_path:
        maze[i][j] -= 10


    for i in orders:
        yield i
        # print(*map(lambda x: x.value, orders))

    for i,j in _real_path:
        maze[i][j] += 10

# client
async def send_key(websocket, key: str):
    await websocket.send(
        json.dumps({"cmd": "key", "key": key})
    )  # send key command to server - you must implement this send in the AI agent

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    """Example client loop."""
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        maze = None
        keys_gen = None
        current_food = None
        
        food_change = 0
        m_couter = 0
        suicide_flag = False

        death_gen = default_gen()

        while True:
            try:
                # receive game update, this must be called timely or your game will get out of sync with the server
                _state: dict = json.loads(await websocket.recv())
                frame_info = GamePacket(_state)
                
                # ignore map packets 
                if 'map' in _state:
                    if maze is None:
                        maze = _state['map']
                        # maze = [list(row) for row in zip(*_state['map'])]
                        
                    m_couter += 1
                    continue

                # clear prev output
                os.system('cls' if os.name == 'nt' else 'clear')

                # suicide
                if frame_info.step > 4000:
                    next(death_gen)
                    key = next(death_gen)
                    await send_key(websocket, key.value)
                    suicide_flag = True
                    continue
                
                if not frame_info.body:
                    send_key(websocket, " ")

                # calc next move
                _temp_a = _calc_closest_food(frame_info, len(maze), len(maze[0]))
                if keys_gen is None or current_food != _temp_a:
                    
                    # to go to the final of gen (redo the -10 in map)
                    if current_food is not None and current_food != _temp_a:
                        for _ in keys_gen:pass
                    
                    keys_gen = bfs_path_gen(maze, frame_info)
                    current_food = _temp_a

                _out_flag = True
                while _out_flag:
                    try:
                        key: SnakeDirection = next(keys_gen)
                        _out_flag = False
                    except StopIteration:
                        keys_gen = bfs_path_gen(maze, frame_info)
                        current_food = _calc_closest_food(frame_info, len(maze), len(maze[0]))
                    except Sepuku:
                        keys_gen = default_gen()
                        key = next(keys_gen)
                        next(keys_gen)
                        _out_flag = False
                        suicide_flag = True

                
                # relevent prints
                filter_info = {i:_state[i] for i in ['traverse', 'score', 'level', 'name', 'step']}
                filter_info['food'] = frame_info.food
                filter_info['head'] = frame_info.body[0]
                
                print_better(filter_info)
                print("Move:", key.name)
                # print_maze(maze, frame_info.food[0][:-1], frame_info.body)
                
                await send_key(websocket, key.value)

            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                break
        
        print("############################################################")
        print(f"{m_couter=}")
        print(f"{suicide_flag=}")
        print(agent_name)
        print(f"{food_change = }")


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", "Alxito v1.6 (BFS)"))
