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
    x, y = block.position[0], block.position[1]
    size = block.size
    within_bounds = x <= location[0] < x + size and y <= location[1] < y + size
    if (block.level == level and within_bounds) or \
            (block.children == [] and within_bounds and block.level < level):
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
    """Return a tuple representing the move made by performing <action>
    on <block>.
    """
    return action[0], action[1], block


class HumanPlayer(Player):
    """A human player.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    id: int
    goal: Goal
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given, <player_id> and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _desired_action to None.
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


def _generate_random_valid_moves(board: Block, goal: Goal) -> \
        Optional[Tuple[str, Optional[int], Block]]:
    """Return a randomly generated, valid move.

    A valid move is a move other than PASS that can be successfully performed
    on the <board>.

    This function does not mutate <board>.
    """
    x = random.randint(board.position[0], board.position[0] + board.size - 1)
    y = random.randint(board.position[1], board.position[1] + board.size - 1)
    level = random.randint(0, board.max_depth)
    block = None
    while block is None:
        block = _get_block(board, (x, y), level)
    actions_ = [ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, SWAP_HORIZONTAL,
                SWAP_VERTICAL, SMASH, PAINT, COMBINE]

    b = block.create_copy()
    move = random.choice(actions_)
    valid_move = False

    if move == SMASH:
        valid_move = b.smash()
    elif move == SWAP_VERTICAL:
        valid_move = b.swap(SWAP_VERTICAL[1])
    elif move == SWAP_HORIZONTAL:
        valid_move = b.swap(SWAP_HORIZONTAL[1])
    elif move == ROTATE_COUNTER_CLOCKWISE:
        valid_move = b.rotate(ROTATE_COUNTER_CLOCKWISE[1])
    elif move == ROTATE_CLOCKWISE:
        valid_move = b.rotate(ROTATE_CLOCKWISE[1])
    elif move == COMBINE:
        valid_move = b.combine()
    elif move == PAINT:
        valid_move = b.paint(goal.colour)

    if valid_move:
        return _create_move(move, block)
    else:
        return _generate_random_valid_moves(board, goal)


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
        """Initialise this random player with the given <player_id> and
        <goal>.

        Initially, _proceed is set to False as it is not the player's turn.
        """
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block on the <board> that has been selected.

        Since the moves are randomly generated, a block within <board> has not
        been selected, and instead will be chosen randomly. So, <board> is not
        used by the function and the function returns None.
        """
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the clicking of the mouse on the game board by
        making it the random player's turn.
        """
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

        move = _generate_random_valid_moves(board, self.goal)

        self._proceed = False  # Must set to False before returning!

        return move


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
        """Initialise this smart player with <player_id>, <goal>, and
        <difficulty>.

        Difficulty determines the number of moves this smart player will try
        before deciding on a move that yields the highest score.

        Precondition: difficulty > 0
        """
        Player.__init__(self, player_id, goal)
        self.difficulty = difficulty
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block on the <board> that has been selected.

        Since the moves are randomly generated, a block within <board> has not
        been selected, and instead will be chosen randomly. So, this function
        returns None.
        """
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the clicking of the mouse on the game board by
        making it the random player's turn.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def _get_score(self, board: Block, block: Block,
                   move: Tuple[str, Optional[int]]) -> int:
        """Return the score of <board> when <move> is performed on the
        given block.

        The scoring is done using the score() method for <self.goal>.
        """
        board_copy = board.create_copy()
        block_copy = _get_block(board_copy, block.position, block.level)
        if move == SWAP_HORIZONTAL:
            block_copy.swap(SWAP_HORIZONTAL[1])
        elif move == SWAP_VERTICAL:
            block_copy.swap(SWAP_VERTICAL[1])
        elif move == SMASH:
            block_copy.smash()
        elif move == PAINT:
            block_copy.paint(self.goal.colour)
        elif move == ROTATE_CLOCKWISE:
            block_copy.rotate(ROTATE_CLOCKWISE[1])
        elif move == ROTATE_COUNTER_CLOCKWISE:
            block_copy.rotate(ROTATE_COUNTER_CLOCKWISE[1])
        elif move == COMBINE:
            block_copy.combine()
        return self.goal.score(board_copy)

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

        valid_moves = []

        for _ in range(self.difficulty):
            move = _generate_random_valid_moves(board, self.goal)
            valid_moves.append(move)

        scores = []

        for move in valid_moves:
            block_ = move[2]
            m = (move[0], move[1])
            s = self._get_score(board, block_, m)
            scores.append(s)

        scores.append(curr_score)
        max_ = max(scores)

        self._proceed = False  # Must set to False before returning!

        if max_ == curr_score:
            return PASS[0], PASS[1], board
        else:
            return valid_moves[scores.index(max_)]


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
