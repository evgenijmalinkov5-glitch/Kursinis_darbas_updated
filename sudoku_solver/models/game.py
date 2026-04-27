"""
SudokuGame module.
Demonstrates: Aggregation — SudokuGame holds references to a SudokuBoard,
a BaseSolver, and a FileManager, but does not own or create them.
Each object can exist independently; SudokuGame merely coordinates them.
"""

from __future__ import annotations

import copy

from models.board import SudokuBoard
from solvers.base_solver import BaseSolver
from utils.file_manager import FileManager


class SudokuGame:
    """High-level controller that coordinates board, solver, and file I/O.

    Aggregation:
      SudokuBoard, BaseSolver, and FileManager are injected via the
      constructor.  SudokuGame holds references to them but does not
      create or destroy them — they can outlive any one SudokuGame instance.
      (Contrast with Composition, where SudokuBoard *owns* its SudokuCell
      objects and destroying the board destroys the cells.)

    This class is also the entry point for the menu-driven CLI.
    """

    def __init__(
        self,
        board: SudokuBoard,
        solver: BaseSolver,
        file_manager: FileManager | None = None,
    ) -> None:
        """Set up the game.

        Args:
            board: The puzzle board to play on.
            solver: Any concrete BaseSolver (Polymorphism in action).
            file_manager: Shared I/O manager; creates one if not provided.
        """
        self.__board: SudokuBoard = board
        self.__solver: BaseSolver = solver
        self.__file_manager: FileManager = file_manager or FileManager()
        # Keep a snapshot of the original puzzle for save/display purposes.
        self.__original_grid: list[list[int]] = copy.deepcopy(board.get_grid())

    # ------------------------------------------------------------------
    # Core actions
    # ------------------------------------------------------------------

    def display(self) -> None:
        """Print the current board state."""
        print("\nCurrent board:")
        self.__board.display()

    def solve(self) -> bool:
        """Run the injected solver and return True if successful."""
        print(f"\nSolving with {self.__solver.__class__.__name__}…")
        success = self.__solver.solve()
        if success:
            print(f"Solved in {self.__solver.steps} steps!")
        else:
            print("No solution exists for this puzzle.")
        return success

    def save(self) -> str:
        """Persist the puzzle and solution to CSV via FileManager."""
        path = self.__file_manager.save_result(
            puzzle=self.__original_grid,
            solution=self.__board.get_grid(),
            solver_name=self.__solver.__class__.__name__,
            steps=self.__solver.steps,
        )
        print(f"Result saved to: {path}")
        return path

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def board(self) -> SudokuBoard:
        return self.__board

    @property
    def solver(self) -> BaseSolver:
        return self.__solver

    @solver.setter
    def solver(self, new_solver: BaseSolver) -> None:
        """Swap the solver at runtime (Polymorphism demo)."""
        self.__solver = new_solver
        print(f"Solver switched to {new_solver.__class__.__name__}.")
