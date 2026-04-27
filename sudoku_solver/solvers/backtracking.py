"""
BacktrackingSolver module.
Demonstrates:
  - Inheritance: reuses __init__, steps, and board from BaseSolver.
  - Polymorphism: overrides solve() with a backtracking algorithm.
    A SudokuGame using BaseSolver will transparently get this behaviour
    when a BacktrackingSolver is assigned.
"""

from __future__ import annotations

from models.board import SudokuBoard
from solvers.base_solver import BaseSolver


class BacktrackingSolver(BaseSolver):
    """Solves Sudoku by recursive backtracking.

    Algorithm:
      1. Find the first empty cell.
      2. Try digits 1–9; skip any that break the Sudoku rules.
      3. Place a digit and recurse.
      4. If the recursion fails, erase the digit and try the next (backtrack).
      5. If all digits fail, return False — the caller must backtrack too.
      6. If no empty cell remains, the puzzle is solved.

    Inheritance: __init__, steps, and board property are inherited from
    BaseSolver. Only solve() is new.
    """

    def __init__(self, board: SudokuBoard) -> None:
        super().__init__(board)

    def solve(self) -> bool:
        """Solve the board using recursive backtracking (overrides BaseSolver)."""
        empty = self._board.find_empty()
        if empty is None:
            return True  # All cells filled — solved!

        row, col = empty
        for num in range(1, 10):
            if self._board.is_valid_placement(row, col, num):
                self._board.set_value(row, col, num)
                self._steps += 1

                if self.solve():
                    return True

                self._board.set_value(row, col, 0)  # Undo — backtrack

        return False  # No digit worked; signal backtrack to the caller.
