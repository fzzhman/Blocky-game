"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin

=== Module Description ===

This file contains the Game class, which is the main class for the
Blocky game.

At the bottom of the file, there are some function that you
can call to try playing the game in several different configurations.
"""
from typing import List
import pygame

from block import generate_board
from blocky import GameData, GameState, MainState
from player import create_players
from renderer import Renderer
from settings import BOARD_SIZE


class Game:
    """A game of Blocky.
    """
    # === Private Attributes ===
    # _renderer:
    #   The object that is capable of drawing our Blocky board on the screen.
    # _data:
    #   The data of the game that can be shared with other GameState objects.
    # _state:
    #   The current GameState.
    _renderer: Renderer
    _data: GameData
    _state: GameState

    def __init__(self, max_depth: int,
                 num_human: int,
                 num_random: int,
                 smart_players: List[int]) -> None:
        """Initialize this game, as described in the Assignment 2 handout.

        Precondition:
            2 <= max_depth <= 5
        """
        board = generate_board(max_depth, BOARD_SIZE)
        players = create_players(num_human, num_random, smart_players)

        self._renderer = Renderer(BOARD_SIZE)
        self._data = GameData(board, players)
        self._state = MainState(self._data)

    def run_game(self, num_turns: int) -> None:
        """Start the main game loop and stop after num_turns.
        """
        self._data.max_turns = num_turns
        clock = pygame.time.Clock()

        while True:
            clock.tick(30)

            # Process events
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return
                else:
                    self._state.process_event(e)

            # Update the state of the game
            self._state = self._state.update()

            # Render the new state of the game
            self._renderer.clear()
            self._state.render(self._renderer)

            # Update the screen
            pygame.display.flip()


def create_auto_game() -> Game:
    """Run a game with two computer players of different "difficulty".
    """
    return Game(3, 0, 0, [5, 10])


def create_two_player_game() -> Game:
    """Run a game with two human players.
    """
    return Game(3, 2, 0, [])


def create_solitaire_game() -> Game:
    """Run a game with one human player.
    """
    return Game(3, 1, 0, [])


def create_sample_game() -> Game:
    """Run a sample game with one human player, one random player,
    and one smart player.
    """
    return Game(3, 1, 1, [6])


if __name__ == '__main__':
    import python_ta
    python_ta.check_all(config={
        'allowed-io': ['run_game'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'pygame', 'blocky',
            'block', 'goal', 'player', 'renderer', 'settings'
        ],
        'generated-members': 'pygame.*'
    })

    pygame.init()

    # If you want to run the same game sequence each time, to assist with
    # debugging, uncomment-out the call to random.seed.
    # import random
    # random.seed(1001)

    # game = create_sample_game()
    # game = create_auto_game()
    # game = create_two_player_game()
    game = create_solitaire_game()

    # Run the game for 5 turns
    game.run_game(5)

    pygame.quit()
