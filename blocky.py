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

This file contains the different game states for the Blocky game.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import pygame

from actions import ACTION_MESSAGE, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE,\
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE, ACTION_PENALTY
from block import Block
from player import Player
from renderer import Renderer
from settings import ANIMATION_DURATION


def _block_to_squares(board: Block) -> List[Tuple[Tuple[int, int, int],
                                                  Tuple[int, int], int]]:
    """Return a list of tuples describing all of the squares to be drawn
    in order to render this Block.

    For every undivided Block, this includes one square in that Block's
    colour. Each tuple contains:
    - the colour of the block,
    - the (x, y) coordinates of the top left corner of the block,
    - the size of the block,
    in that order.

    The order of the squares does not matter.
    """
    lst = []
    if len(board.children) == 0:
        return [(board.colour, board.position, board.size)]
    else:
        for child in board.children:
            lst.extend(_block_to_squares(child))
        return lst


class GameData:
    """
    A bundle of the data needed for a Blocky game.

    === Public Attributes ===
    max_turns:
        The maximum number of turns for the game.
    board:
        The Blocky board on which this game will be played.
    players:
        The entities that are playing this game.
    smashes:
        The number of smashes done by each player.
    combines:
        The number of combines done by each player.
    paints:
        The number of paints done by each player.

    === Representation Invariants ===
    - len(players) >= 1
    """
    max_turns: int
    board: Block
    players: List[Player]
    smashes: Dict[int, int]
    combines: Dict[int, int]
    paints: Dict[int, int]

    def __init__(self, board: Block, players: List[Player]) -> None:
        """Initialize the game data, saving a reference to <board> and
        <players>.

        Precondition:
            - len(players) >= 1
        """
        self.max_turns = 0
        self.board = board
        self.players = players

        self.smashes = {}
        self.combines = {}
        self.paints = {}

        # Start off all counts at 0
        for player in players:
            self.smashes[player.id] = 0
            self.combines[player.id] = 0
            self.paints[player.id] = 0

    def calculate_score(self, player_id: int) -> Tuple[int, int]:
        """Return a tuple containing first the <player_id>'s score based on
        their goal in the game and second the deductions from their score based
        on the actions they've taken.
        """
        goal_score = self.players[player_id].goal.score(self.board)

        penalty = self.smashes[player_id] * ACTION_PENALTY[SMASH] + \
                  self.combines[player_id] * ACTION_PENALTY[COMBINE] + \
                  self.paints[player_id] * ACTION_PENALTY[PAINT]

        return goal_score, penalty


class GameState:
    """One of the different states that a Blocky game can be in.
    """

    def process_event(self, event: pygame.event.Event) -> None:
        """Process the event from the operating system, if possible.
        """
        raise NotImplementedError

    def update(self) -> GameState:
        """Update this GameState based on past events.

        Return the next GameState that should be updated. This can be self.
        """
        raise NotImplementedError

    def render(self, renderer: Renderer) -> None:
        """Render the current state of the game onto the screen.
        """
        raise NotImplementedError


class MainState(GameState):
    """A GameState that manages the moves made by different players in Blocky.
    """
    # === Private Attributes ===
    # _turn:
    #   The current turn.
    # _data:
    #   A reference to the shared GameData.
    # _current_player_index:
    #   The index of the current player in GameData.players.
    # _current_score:
    #   The score of the current player, including penalties.
    _turn: int
    _data: GameData
    _current_player_index: int
    _current_score: int

    def __init__(self, data: GameData) -> None:
        """Initialize this GameState.
        """
        self._turn = 0
        self._data = data
        self._current_player_index = 0

        score, penalty = self._data.calculate_score(self._current_player().id)
        self._current_score = score - penalty

    def _current_player(self) -> Player:
        """Return the player whose turn it is.
        """
        return self._data.players[self._current_player_index]

    def _update_player(self) -> None:
        """Update the player whose turn it is.
        """
        self._current_player_index = (self._current_player_index + 1) % len(
            self._data.players)

        score, penalty = self._data.calculate_score(self._current_player().id)
        self._current_score = score - penalty

        if self._current_player_index == 0:
            self._turn += 1

    def _do_move(self, move: Tuple[str, Optional[int], Block]) -> bool:
        """Attempt to do the player's requested move.
        """
        action = (move[0], move[1])
        direction = move[1]
        block = move[2]
        player = self._current_player()
        move_successful = False

        if action in [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE]:
            move_successful = block.rotate(direction)
        elif action in [SWAP_HORIZONTAL, SWAP_VERTICAL]:
            move_successful = block.swap(direction)
        elif action == SMASH:
            move_successful = block.smash()
            self._data.smashes[player.id] += int(move_successful)
        elif action == PAINT:
            move_successful = block.paint(self._current_player().goal.colour)
            self._data.paints[player.id] += int(move_successful)
        elif action == COMBINE:
            move_successful = block.combine()
            self._data.combines[player.id] += int(move_successful)
        elif action == PASS:
            # Do nothing
            move_successful = True

        if move_successful:
            self._update_player()

        return move_successful

    def process_event(self, event: pygame.event.Event) -> None:
        """Process the event from the operating system for the current player.
        """
        self._current_player().process_event(event)

    def update(self) -> GameState:
        """Update this GameState based on past events.

        Return the next GameState that should be updated. This can be self.

        The returned GameState will be self if the move requested by the
        player is not valid given the current GameState.
        """
        if self._turn >= self._data.max_turns:
            return GameOverState(self._data)

        # Ask the player to make a move
        move = self._current_player().generate_move(self._data.board)

        if move is None:
            # No move was made, stay in the current state
            return self
        else:
            # Save what the board looks like before the move
            background = _block_to_squares(self._data.board)
            # Also save the current player ID
            player_id = self._current_player().id

            # Do the move
            if self._do_move(move):
                # Animate the move that was just done
                return AnimateMoveState(self, player_id, move, background)
            else:
                # The move was not valid, let the player try again
                return self

    def render(self, renderer: Renderer) -> None:
        """Render the current state of the game onto the screen.
        """
        renderer.draw_board(_block_to_squares(self._data.board))

        b = self._current_player().get_selected_block(self._data.board)
        if b is not None:
            renderer.highlight_block(b.position, b.size)

        p = self._current_player()
        status = f'Turn {self._turn} | Player {p.id} | ' \
                 f'Score {self._current_score} | {p.goal.description()}'
        renderer.draw_status(status)


class AnimateMoveState(GameState):
    """A GameState that animates a move made by a player before returning to its
    parent GameState.
    """
    # === Private Attributes ===
    # _parent:
    #   The GameState to return to after the animation has completed.
    # _player_id:
    #   The ID of the player whose move is being animated.
    # _move:
    #   The move being animated.
    # _start_time:
    #   The time that the animation started.
    # _background:
    #   The board to display behind the animation.
    _parent: GameState
    _player_id: int
    _move: Tuple[str, Optional[int], Block]
    _start_time: int
    _background: List[Tuple[Tuple[int, int, int], Tuple[int, int], int]]

    def __init__(self, parent: GameState, player_id: int,
                 move: Tuple[str, Optional[int], Block],
                 background: List[Tuple[Tuple[int, int, int], Tuple[int, int],
                                        int]]) -> None:
        """Initialize this GameState.
        """
        self._parent = parent
        self._player_id = player_id
        self._move = move
        self._background = background
        self._start_time = pygame.time.get_ticks()

    def process_event(self, event: pygame.event.Event) -> None:
        """Process the event from the operating system. In this case we
        ignore the event.
        """
        return  # Ignore the event

    def update(self) -> GameState:
        """Update this GameState based on past events.

        Return the next GameState that should be updated. This can be self.

        The returned GameState will be self if the animation is still
        running.
        """
        elapsed_seconds = (pygame.time.get_ticks() - self._start_time) / 1000

        if elapsed_seconds > ANIMATION_DURATION:
            # The animation is complete, do the move, go back to the last
            # GameState
            return self._parent
        else:
            # The animation is still running, remain in this GameState
            return self

    def render(self, renderer: Renderer) -> None:
        """Render the current state of the game onto the screen.

        We outline the selected block, display on screen the image representing
        the chosen move, and update the status message for the action being
        performed by the player.
        """
        renderer.draw_board(self._background)

        # Draw an outline around the selected block
        b = self._move[2]
        renderer.highlight_block(b.position, b.size)

        # Draw the image representing the move
        action = (self._move[0], self._move[1])
        renderer.draw_image(action, b.position, b.size)

        # Update the status message based on the action being performed.
        status = f'Player {self._player_id} is {ACTION_MESSAGE[action]}'
        renderer.draw_status(status)


class GameOverState(GameState):
    """A GameState that is displayed when the game is over.
    """
    # === Private Attributes ===
    # _scores:
    #   A list of tuples containing each player ID, goal score, and penalty
    # _winner:
    #   The ID of the winning player
    _scores: List[Tuple[int, int, int]]
    _winner: int

    def __init__(self, data: GameData) -> None:
        """Initialize this GameState.
        """
        self._scores = []
        for p in data.players:
            goal_score, penalty = data.calculate_score(p.id)
            self._scores.append((p.id, goal_score, penalty))

        self._winner = max(self._scores, key=lambda item: item[1] - item[2])[0]

    def process_event(self, event: pygame.event.Event) -> None:
        """Process the event from the operating system. In this case we
        ignore the event.
        """
        # Simply ignore the event
        return

    def update(self) -> GameState:
        """Update the GameState based on past events. Since the game is over,
        this method just returns the current GameState, i.e., self.
        """
        # Nothing to change
        return self

    def render(self, renderer: Renderer) -> None:
        """Render the current state of the game onto the screen.

        Display the score, the penalties, and the final score for each player
        on the screen. Finally, announce the winner.
        """
        x = 10
        y = 10
        for t in self._scores:
            player_id, goal_score, penalty = t
            score = goal_score - penalty
            text = f'Player {player_id}\'s final score is {goal_score} - ' \
                   f'{penalty} = {score}'

            renderer.print(text, x, y)
            y += renderer.text_height()

        renderer.print(f'Player {self._winner} wins!', x, y)


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['run_game'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'pygame', '__future__',
            'block', 'player', 'renderer', 'settings', 'actions'
        ],
        'generated-members': 'pygame.*'
    })
