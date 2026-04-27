"""
SudokuCell module.
Demonstrates: Encapsulation — value and is_fixed are private; access
is controlled through properties with validation logic.
"""


class SudokuCell:
    """Represents a single cell in a Sudoku grid.

    Encapsulation example:
      - __value and __is_fixed are private (name-mangled).
      - External code must use the value property, which enforces rules:
        no writing to a fixed cell, no out-of-range digits.
    """

    def __init__(self, value: int = 0, is_fixed: bool = False) -> None:
        """Initialise a cell.

        Args:
            value: Starting digit (0 means empty).
            is_fixed: True if the cell is part of the original puzzle clue.
        """
        self.__value: int = value
        self.__is_fixed: bool = is_fixed

    # ------------------------------------------------------------------
    # Properties (controlled access — Encapsulation)
    # ------------------------------------------------------------------

    @property
    def value(self) -> int:
        """Return the cell's current digit."""
        return self.__value

    @value.setter
    def value(self, val: int) -> None:
        """Set the digit with validation.

        Args:
            val: New digit in range 0–9 (0 clears the cell).

        Raises:
            ValueError: If the cell is fixed or the value is out of range.
        """
        if self.__is_fixed:
            raise ValueError("Cannot modify a fixed (given) cell.")
        if not 0 <= val <= 9:
            raise ValueError(f"Value must be 0–9, got {val}.")
        self.__value = val

    @property
    def is_fixed(self) -> bool:
        """Return True if this digit is a puzzle clue (read-only)."""
        return self.__is_fixed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def is_empty(self) -> bool:
        """Return True when no digit has been placed (value == 0)."""
        return self.__value == 0

    def __repr__(self) -> str:
        return str(self.__value) if self.__value != 0 else "."
