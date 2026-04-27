"""
SudokuBoard module.
Demonstrates: Composition — SudokuBoard owns and manages its SudokuCell
objects. The cells are created inside the board and cannot exist without it.
"""

from __future__ import annotations

from models.cell import SudokuCell


class SudokuBoard:
    """9×9 Sudoku grid composed of SudokuCell instances.

    Composition: the board is responsible for creating and containing its
    cells. Destroying the board destroys all cells with it.
    """

    SIZE: int = 9
    BOX_SIZE: int = 3

    def __init__(self, grid: list[list[int]] | None = None) -> None:
        """Build the board from an optional 9×9 integer grid.

        Args:
            grid: 2-D list where 0 means an empty cell.
                  If None, an all-empty board is created.
        """
        self.__cells: list[list[SudokuCell]] = self.__build_cells(grid)

    def __build_cells(
        self, grid: list[list[int]] | None
    ) -> list[list[SudokuCell]]:
        """Create the 9×9 matrix of SudokuCell objects (Composition)."""
        cells = []
        for row in range(self.SIZE):
            cell_row = []
            for col in range(self.SIZE):
                val = grid[row][col] if grid else 0
                cell_row.append(SudokuCell(val, is_fixed=(val != 0)))
            cells.append(cell_row)
        return cells

    # ------------------------------------------------------------------
    # Cell access
    # ------------------------------------------------------------------

    def get_cell(self, row: int, col: int) -> SudokuCell:
        """Return the SudokuCell at (row, col)."""
        return self.__cells[row][col]

    def get_value(self, row: int, col: int) -> int:
        """Return the integer digit at (row, col)."""
        return self.__cells[row][col].value

    def set_value(self, row: int, col: int, value: int) -> None:
        """Place a digit at (row, col).

        Args:
            row: Row index 0–8.
            col: Column index 0–8.
            value: Digit 0–9 (0 erases).
        """
        self.__cells[row][col].value = value

    def get_grid(self) -> list[list[int]]:
        """Return a plain 9×9 list of integers (no SudokuCell objects)."""
        return [
            [self.__cells[r][c].value for c in range(self.SIZE)]
            for r in range(self.SIZE)
        ]

    # ------------------------------------------------------------------
    # Solver helpers
    # ------------------------------------------------------------------

    def find_empty(self) -> tuple[int, int] | None:
        """Return (row, col) of the first empty cell, or None if the board is full."""
        for r in range(self.SIZE):
            for c in range(self.SIZE):
                if self.__cells[r][c].is_empty():
                    return r, c
        return None

    def is_valid_placement(self, row: int, col: int, num: int) -> bool:
        """Return True if placing num at (row, col) satisfies all Sudoku rules."""
        # Check row
        for c in range(self.SIZE):
            if self.get_value(row, c) == num:
                return False
        # Check column
        for r in range(self.SIZE):
            if self.get_value(r, col) == num:
                return False
        # Check 3×3 box
        box_r = self.BOX_SIZE * (row // self.BOX_SIZE)
        box_c = self.BOX_SIZE * (col // self.BOX_SIZE)
        for r in range(box_r, box_r + self.BOX_SIZE):
            for c in range(box_c, box_c + self.BOX_SIZE):
                if self.get_value(r, c) == num:
                    return False
        return True

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def display(self) -> None:
        """Print the board to stdout with box separators."""
        sep = "-" * 21
        for r in range(self.SIZE):
            if r % self.BOX_SIZE == 0 and r != 0:
                print(sep)
            parts: list[str] = []
            for c in range(self.SIZE):
                if c % self.BOX_SIZE == 0 and c != 0:
                    parts.append("|")
                parts.append(repr(self.__cells[r][c]))
            print(" ".join(parts))

    def __repr__(self) -> str:
        return f"SudokuBoard({self.get_grid()!r})"
