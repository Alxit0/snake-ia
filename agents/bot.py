"""
Alxito Sanke Bot Main File

TODO:
    -- Automate snake

Changelog:
    -- Version 0.1 Alxito
        --- Processing snake senses
        --- Initial code release

"""

import asyncio
import getpass
import json
import os
from pprint import pprint
from typing import Literal
import numpy as np
import websockets

from utils import Maze, TickSate, print_maze, print_mazes

import pygame


async def suicide(websocket: websockets.WebSocketClientProtocol):
    await send_key(websocket, "a")
    await websocket.recv()
    await send_key(websocket, "d")

async def send_key(websocket: websockets.WebSocketClientProtocol, key: Literal['w','a','s','d','']):
    # send key command to server - you must implement this send in the AI agent 
    await websocket.send(json.dumps({"cmd": "key", "key": key}))

async def agent_loop(server_address="localhost:8000", agent_name="student"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:
        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))

        # Next 3 lines are not needed for AI agent
        SCREEN = pygame.display.set_mode((299, 123))
        SPRITES = pygame.image.load("data/pad.png").convert_alpha()
        SCREEN.blit(SPRITES, (0, 0))

        maze = None

        while True:
            try:
                # info capture
                state = json.loads(await websocket.recv())

                if 'map' in state:
                    if maze is None:
                        maze = Maze(state['map'])
                    continue

                tick_state = TickSate(state)

                # logic
                if tick_state.step > 1000:
                    await suicide(websocket)
                    break

                maze.update_maze(tick_state)

                key = ""
                await send_key(websocket, key)
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()

                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_UP:
                            key = "w"
                        elif event.key == pygame.K_LEFT:
                            key = "a"
                        elif event.key == pygame.K_DOWN:
                            key = "s"
                        elif event.key == pygame.K_RIGHT:
                            key = "d"
                        elif event.key == pygame.K_SPACE:
                            key = " "
                        elif event.key == pygame.K_a:
                            key = "A"
                        elif event.key == pygame.K_b:
                            key = "B"

                        elif event.key == pygame.K_d:
                            pprint(state)

                        await send_key(websocket, key)
                        break

                # prints
                os.system('cls' if os.name == 'nt' else 'clear')
                pprint(tick_state.sight, width= 200)
                print(f'step: {tick_state.step}')
                print(f'traverse: {tick_state.traverse}')
                print(len(tick_state.processed_sight), "/", sum(map(len, tick_state.sight.values())))
                maze.verbose_print(tick_state)
                # print_mazes([maze, temp], [tick_state.body, []])
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                break
            
            pygame.display.flip()
        # end prints
        print("#"*100)


# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='arrumador' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", "Alxito v0.1"))
