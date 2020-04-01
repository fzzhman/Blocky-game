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
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    players = []

    total = num_human + num_random + len(smart_players)
    goals = generate_goals(total)

    for i in range(num_human):
        goal = random.choice(goals)
        goals.remove(goal)
        p = HumanPlayer(i, goal)
        players.append(p)

    for j in range(num_human, num_random + num_human):
        goal = random.choice(goals)
        goals.remove(goal)
        p = RandomPlayer(j, goal)
        players.append(p)

    for k in range(len(smart_players)):
        goal = random.choice(goals)
        goals.remove(goal)
        p = SmartPlayer(k + num_human + num_random, goal, smart_players[k])
        players.append(p)

    return players


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth
    """
    if block.level == level:
        size = block.size
        x, y = block.position[0], block.position[1]
        if x <= location[0] < x + size and y <= location[1] < y + size:
            return block
    elif block.level > level:
        return None
    else:
        for child in block.children:
            b = _get_block(child, location, level)
            if b is not None:
                return b

    return None


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    return action[0], action[1], block


class HumanPlayer(Player):
    """A human player.
    """
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given, <player_id> and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, min(self._level, board.max_depth))

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


class RandomPlayer(Player):
    """A random player in the Blocky game.

    === Public Attributes ===
    id:
        This random player's number.
    goal:
        This random player's assigned goal for the game.
    """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    id: int
    goal: Goal
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        actions_ = [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, SWAP_HORIZONTAL,
                    SWAP_VERTICAL, SMASH, PAINT, COMBINE]
        b = board.create_copy()
        move = random.choice(actions_)
        valid_move = False
        if move == SMASH:
            valid_move = b.smash()
        elif move == SWAP_VERTICAL:
            valid_move = b.swap(1)
        elif move == SWAP_HORIZONTAL:
            valid_move = b.swap(0)
        elif move == ROTATE_COUNTER_CLOCKWISE:
            valid_move = b.rotate(3)
        elif move == ROTATE_CLOCKWISE:
            valid_move = b.rotate(1)
        elif move == COMBINE:
            valid_move = b.combine()
        elif move == PAINT:
            valid_move = b.paint(self.goal.colour)

        self._proceed = False  # Must set to False before returning!

        if valid_move:
            return move
        else:
            return self.generate_move(board)


class SmartPlayer(Player):
    """A smart player in the Blocky game.

    === Public Attributes ===
    id:
        This smart player's number.
    goal:
        This smart player's assigned goal for the game.
    difficulty:
        The difficulty level of this smart player.
    """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    id: int
    goal: Goal
    difficulty: int
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        Player.__init__(self, player_id, goal)
        self.difficulty = difficulty
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) ->\
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove

        curr_score = self.goal.score(board.create_copy())

        copy = board.create_copy()
        if copy.smash():
            smash_score = self.goal.score(copy)
        else:
            smash_score = -1
        copy = board.create_copy()
        if copy.swap(1):
            swap_score_1 = self.goal.score(copy)
        else:
            swap_score_1 = -1
        copy = board.create_copy()
        if copy.swap(0):
            swap_score_0 = self.goal.score(copy)
        else:
            swap_score_0 = -1
        copy = board.create_copy()
        if copy.rotate(1):
            rotate_score_1 = self.goal.score(copy)
        else:
            rotate_score_1 = -1
        copy = board.create_copy()
        if copy.rotate(3):
            rotate_score_3 = self.goal.score(copy)
        else:
            rotate_score_3 = -1
        copy = board.create_copy()
        if copy.paint(self.goal.colour):
            paint_score = self.goal.score(copy)
        else:
            paint_score = -1
        copy = board.create_copy()
        if copy.combine():
            combine_score = self.goal.score(copy)
        else:
            combine_score = -1

        max_ = max(curr_score, smash_score, swap_score_0, swap_score_1,
                   rotate_score_3, rotate_score_1, paint_score, combine_score)

        self._proceed = False  # Must set to False before returning!

        if max_ == curr_score:
            return PASS
        elif max_ == smash_score:
            return SMASH
        elif max_ == swap_score_0:
            return SWAP_HORIZONTAL
        elif max_ == swap_score_1:
            return SWAP_VERTICAL
        elif max_ == rotate_score_3:
            return ROTATE_COUNTER_CLOCKWISE
        elif max_ == rotate_score_1:
            return ROTATE_CLOCKWISE
        elif max_ == paint_score:
            return PAINT
        else:
            return COMBINE


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
