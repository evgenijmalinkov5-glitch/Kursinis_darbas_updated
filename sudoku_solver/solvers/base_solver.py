"""
BaseSolver module.
Demonstrates:
  - Abstraction: defines the interface every solver must honour without
    specifying how it works.
  - Polymorphism: SudokuGame calls solver.solve() without knowing which
    concrete class it is talking to — the call behaves differently
    depending on the actual object (BacktrackSolver vs ConstraintSolver).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from models.board import SudokuBoard


class BaseSolver(ABC):
    """Abstract base class for all Sudoku solving strategies.

    Abstraction: callers only need to know solve() exists and returns bool.
    They never depend on BacktrackingSolver or ConstraintSolver directly.

    Polymorphism: different subclasses implement solve() differently.
    A SudokuGame can switch solvers at runtime without changing its own code.
    """

    def __init__(self, board: SudokuBoard) -> None:
        """Store a reference to the board and reset the step counter."""
        self._board: SudokuBoard = board
        self._steps: int = 0

    @abstractmethod
    def solve(self) -> bool:
        """Attempt to solve the board in-place.

        Subclasses must override this method with a concrete algorithm.

        Returns:
            True if the puzzle was solved, False if no solution exists.
        """

    # ------------------------------------------------------------------
    # Shared properties (inherited by all subclasses)
    # ------------------------------------------------------------------

    @property
    def steps(self) -> int:
        """Number of cell assignments made during solving."""
        return self._steps

    @property
    def board(self) -> SudokuBoard:
        """The board being operated on."""
        return self._board
