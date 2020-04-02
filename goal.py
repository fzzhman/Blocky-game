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

This file contains the hierarchy of Goal classes.
"""
from __future__ import annotations
import random
from typing import List, Tuple
from block import Block
from settings import colour_name, COLOUR_LIST


def generate_goals(num_goals: int) -> List[Goal]:
    """Return a randomly generated list of goals with length num_goals.

    All elements of the list must be the same type of goal, but each goal
    must have a different randomly generated colour from COLOUR_LIST. No two
    goals can have the same colour.

    Precondition:
        - num_goals <= len(COLOUR_LIST)
    """
    goals = []
    colour_choices = []
    while len(colour_choices) != num_goals:
        index = random.randint(0, len(COLOUR_LIST)-1)
        colour = COLOUR_LIST[index]
        if colour not in colour_choices:
            colour_choices.append(colour)
    goal_index = random.randint(0, 2)
    if goal_index == 0:
        for c in colour_choices:
            goals.append(PerimeterGoal(c))
        assert len(goals) == num_goals
        return goals
    else:
        for c in colour_choices:
            goals.append(BlobGoal(c))
        assert len(goals) == num_goals
        return goals


def _flatten(block: Block) -> List[List[Tuple[int, int, int]]]:
    """Return a two-dimensional list representing <block> as rows and columns of
    unit cells.

    Return a list of lists L, where,
    for 0 <= i, j < 2^{max_depth - self.level}
        - L[i] represents column i and
        - L[i][j] represents the unit cell at column i and row j.

    Each unit cell is represented by a tuple of 3 ints, which is the colour
    of the block at the cell location[i][j]

    L[0][0] represents the unit cell in the upper left corner of the Block.
    """
    lst = []
    for i in range(2**(block.max_depth - block.level)):
        lst.append([])

    if len(block.children) == 0:
        for item in lst:
            for i in range(len(lst)):
                item.append(block.colour)
    else:
        child0 = _flatten(block.children[0])
        child1 = _flatten(block.children[1])
        child2 = _flatten(block.children[2])
        child3 = _flatten(block.children[3])
        for i in range(len(child1)):
            lst[i].extend(child1[i])
            lst[i].extend(child2[i])
        for j in range(len(child0)):
            lst[j+len(child1)].extend(child0[j])
            lst[j+len(child1)].extend(child3[j])

    return lst


class Goal:
    """A player goal in the game of Blocky.

    This is an abstract class. Only child classes should be instantiated.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which
        this goal applies.
    """
    colour: Tuple[int, int, int]

    def __init__(self, target_colour: Tuple[int, int, int]) -> None:
        """Initialize this goal to have the given target colour.
        """
        self.colour = target_colour

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given board.

        The score is always greater than or equal to 0.
        """
        raise NotImplementedError

    def description(self) -> str:
        """Return a description of this goal.
        """
        raise NotImplementedError


class PerimeterGoal(Goal):
    """A perimeter goal in the game of Blocky.

    The player must aim to put the most possible units of a given colour,
    known as the target colour, on the outer perimeter of the board.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which this goal
        applies.
    """
    colour: Tuple[int, int, int]

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given <board>.

        Each unit cell on the outer perimeter of <board> of the target colour
        is attributed a point. Any unit cells on the corner of the boards are
        appointed two points.

        We do not account for the penalties associated with Rotating,
        Swapping, Smashing, Painting, Combining, or Passing here (if any).

        The score returned must always be greater than or equal to zero.
        """
        score = 0
        flat = _flatten(board)

        perimeter = []
        perimeter.extend(flat[0][1:-1])
        perimeter.extend(flat[-1][1:-1])
        for i in range(1, len(flat) - 1):
            perimeter.append(flat[i][0])
            perimeter.append(flat[i][-1])

        if flat[0][0] == self.colour:
            score += 2
        if flat[0][-1] == self.colour:
            score += 2
        if flat[-1][0] == self.colour:
            score += 2
        if flat[-1][-1] == self.colour:
            score += 2

        for element in perimeter:
            if element == self.colour:
                score += 1

        return score

    def description(self) -> str:
        """Return a description of this goal.
        """
        description = "The player must aim to put the most possible units " + \
                      "of " + colour_name(self.colour) + " on the outer" +\
                      " perimeter."
        return description


class BlobGoal(Goal):
    """A blob goal in the game of Blocky.

    The player must aim to put together the largest 'blob' of the target colour.
    A blob is a group of connected blocks of the same colour.

    === Attributes ===
    colour:
        The target colour for this goal, that is the colour to which this goal
        applies.
    """
    colour: Tuple[int, int, int]

    def score(self, board: Block) -> int:
        """Return the current score for this goal on the given <board>.

        The player's score is the number of unit cells in the largest blob
        of the target colour. A block is connected if its sides touch. Touching
        corners does not count.

        We do not account for the penalties associated with Rotating,
        Swapping, Smashing, Painting, Combining, or Passing here (if any).

        The score returned must always be greater than or equal to zero.
        """
        flattened = _flatten(board)
        curr_max = 0
        visited = []

        for item in flattened:
            row = [-1] * len(item)
            visited.append(row)

        for col in range(len(flattened)):
            for row in range(len(flattened[0])):
                poss_blob = self._undiscovered_blob_size((row, col),
                                                         flattened, visited)
                if poss_blob > curr_max:
                    curr_max = poss_blob

        return curr_max

    def _undiscovered_blob_size(self, pos: Tuple[int, int],
                                board: List[List[Tuple[int, int, int]]],
                                visited: List[List[int]]) -> int:
        """Return the size of the largest connected blob that
        (a) is of this Goal's target colour,
        (b) includes the cell at <pos>, and
        (c) involves only cells that have never been visited.

        If <pos> is out of bounds for <board>, return 0.

        <board> is the flattened board on which to search for the blob.
        <visited> is a parallel structure that, in each cell, contains:
            -1 if this cell has never been visited
            0  if this cell has been visited and discovered
               not to be of the target colour
            1  if this cell has been visited and discovered
               to be of the target colour

        Update <visited> so that all cells that are visited are marked with
        either 0 or 1.
        """
        col = pos[1]
        row = pos[0]
        blob_size = 0

        if col >= len(board) or col < 0 or row >= len(board[0]) or row < 0:
            return 0
        else:
            if board[col][row] == self.colour and visited[col][row] == -1:
                blob_size += 1
                visited[col][row] = 1
                blob_size += self._undiscovered_blob_size((row, col+1),
                                                          board, visited)
                blob_size += self._undiscovered_blob_size((row, col - 1),
                                                          board, visited)
                blob_size += self._undiscovered_blob_size((row + 1, col),
                                                          board, visited)
                blob_size += self._undiscovered_blob_size((row - 1, col),
                                                          board, visited)
            elif board[col][row] != self.colour:
                if visited[col][row] == -1:
                    visited[col][row] = 0
        return blob_size

    def description(self) -> str:
        description = "The player must aim for the largest group of " +\
                      "connected blocks of " + colour_name(self.colour) + "."
        return description


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'block', 'settings',
            'math', '__future__'
        ],
        'max-attributes': 15
    })
