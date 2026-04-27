"""
ConstraintSolver module.
Demonstrates:
  - Inheritance: extends BaseSolver, reusing __init__, steps, board.
  - Polymorphism: a completely different solve() strategy than
    BacktrackingSolver — yet SudokuGame can call .solve() on either.
"""

from __future__ import annotations

from models.board import SudokuBoard
from solvers.base_solver import BaseSolver


class ConstraintSolver(BaseSolver):
    """Solves Sudoku using constraint propagation, then backtracking.

    Phase 1 — Naked singles:
      Scan every empty cell. If only one digit is still legal for that cell,
      fill it in. Repeat until no more naked singles can be resolved.
      (This is often enough to complete easy and some medium puzzles without
      any search at all.)

    Phase 2 — Backtracking fallback:
      If naked singles leave some cells unsolved, apply recursive
      backtracking on the remaining cells using the reduced search space
      produced by Phase 1.

    Compared with BacktrackingSolver, this tends to use fewer steps on
    easy puzzles and visits far fewer branches on harder ones.

    Polymorphism: the board, steps property, and overall contract are
    identical to BacktrackingSolver — only the internal logic differs.
    """

    def __init__(self, board: SudokuBoard) -> None:
        super().__init__(board)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _possible_values(self, row: int, col: int) -> set[int]:
        """Return the set of digits still legal at (row, col)."""
        used: set[int] = set()
        size = self._board.SIZE
        box_size = self._board.BOX_SIZE

        for c in range(size):
            used.add(self._board.get_value(row, c))
        for r in range(size):
            used.add(self._board.get_value(r, col))

        box_r = box_size * (row // box_size)
        box_c = box_size * (col // box_size)
        for r in range(box_r, box_r + box_size):
            for c in range(box_c, box_c + box_size):
                used.add(self._board.get_value(r, c))

        return set(range(1, 10)) - used

    def _propagate(self) -> bool:
        """Fill all naked-single cells.

        Returns:
            False if any empty cell has no legal digit (dead end),
            True otherwise.
        """
        changed = True
        while changed:
            changed = False
            for r in range(self._board.SIZE):
                for c in range(self._board.SIZE):
                    if self._board.get_cell(r, c).is_empty():
                        possible = self._possible_values(r, c)
                        if len(possible) == 0:
                            return False  # Contradiction — dead end.
                        if len(possible) == 1:
                            self._board.set_value(r, c, possible.pop())
                            self._steps += 1
                            changed = True
        return True

    # ------------------------------------------------------------------
    # solve() — overrides BaseSolver (Polymorphism)
    # ------------------------------------------------------------------

    def solve(self) -> bool:
        """Solve using constraint propagation, then backtracking fallback."""
        if not self._propagate():
            return False  # Contradiction discovered — no solution on this path.

        empty = self._board.find_empty()
        if empty is None:
            return True  # Fully solved by propagation alone.

        # Backtracking phase — guided by reduced domains
        row, col = empty
        for num in self._possible_values(row, col):
            self._board.set_value(row, col, num)
            self._steps += 1
            if self.solve():
                return True
            self._board.set_value(row, col, 0)

        return False
