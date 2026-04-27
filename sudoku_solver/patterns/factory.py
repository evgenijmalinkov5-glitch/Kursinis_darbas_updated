"""
PuzzleFactory module.
Demonstrates: Factory Method design pattern.

Why Factory Method?
  Creating SudokuBoard objects requires knowing the specific grid data for
  each difficulty level. If callers constructed boards directly they would
  need access to that data everywhere — tight coupling.
  The factory centralises board construction: callers ask for a difficulty
  level and receive a ready board, with no knowledge of the internal data.

  Other patterns considered:
  - Singleton: unsuitable — we need many independent board instances per
    session, not one shared object.
  - Builder: would add complexity (step-by-step construction) that gains
    nothing over a simple static factory here.

v2 — Puzzle generator:
  Instead of returning the same hardcoded grid every time, create() now
  generates a unique random puzzle on every call. The difficulty controls
  how many cells are removed from a freshly shuffled solved board.
"""

from __future__ import annotations

import copy
import random

from models.board import SudokuBoard


class PuzzleFactory:
    """Creates SudokuBoard objects for different difficulty levels.

    Factory Method pattern: create() decides which board configuration to
    instantiate based on a simple string argument, decoupling board
    creation from the rest of the application.

    Puzzle generation algorithm:
      1. Fill the diagonal three 3x3 boxes independently (they do not
         share a row, column, or box with each other, so any valid fill
         works without any checking).
      2. Solve the rest of the board with backtracking to produce a
         complete, valid solution.
      3. Shuffle the board: swap rows within boxes, swap columns within
         boxes, swap entire box-rows, swap entire box-columns, and
         permute digits. All of these operations preserve Sudoku validity.
      4. Remove digits one by one, checking after each removal that the
         puzzle still has exactly one solution.  Stop when the target
         number of empty cells is reached.
    """

    # How many cells to remove per difficulty
    _CLUES_TO_REMOVE: dict[str, int] = {
        "easy":   36,   # ~45 clues remain
        "medium": 46,   # ~35 clues remain
        "hard":   54,   # ~27 clues remain
        "empty":  81,   # all cells removed
    }

    # ── Public API ────────────────────────────────────────────────────────────

    @staticmethod
    def create(difficulty: str = "easy") -> SudokuBoard:
        """Generate and return a unique random SudokuBoard.

        Every call produces a different puzzle at the requested difficulty.

        Args:
            difficulty: One of 'easy', 'medium', 'hard', 'empty'.

        Returns:
            A new SudokuBoard with a freshly generated puzzle.

        Raises:
            ValueError: If difficulty is not recognised.
        """
        key = difficulty.lower()
        if key not in PuzzleFactory._CLUES_TO_REMOVE:
            valid = ", ".join(PuzzleFactory._CLUES_TO_REMOVE)
            raise ValueError(
                f"Unknown difficulty '{difficulty}'. Choose from: {valid}."
            )

        if key == "empty":
            return SudokuBoard([[0] * 9 for _ in range(9)])

        grid = PuzzleFactory._generate()
        PuzzleFactory._remove_digits(grid, PuzzleFactory._CLUES_TO_REMOVE[key])
        return SudokuBoard(grid)

    @staticmethod
    def available_difficulties() -> list[str]:
        """Return all supported difficulty names."""
        return list(PuzzleFactory._CLUES_TO_REMOVE.keys())

    # ── Step 1 — build a complete solved board ────────────────────────────────

    @staticmethod
    def _generate() -> list[list[int]]:
        """Return a fully filled, randomly shuffled valid 9x9 grid."""
        grid = [[0] * 9 for _ in range(9)]

        # Fill the three independent diagonal boxes first (no conflicts possible)
        for box in range(3):
            PuzzleFactory._fill_box(grid, box * 3, box * 3)

        # Solve the remaining cells with backtracking
        PuzzleFactory._solve(grid)

        # Shuffle to randomise layout while keeping validity
        PuzzleFactory._shuffle(grid)
        return grid

    @staticmethod
    def _fill_box(grid: list[list[int]], row: int, col: int) -> None:
        """Fill a 3x3 box starting at (row, col) with a random permutation of 1-9."""
        digits = random.sample(range(1, 10), 9)
        idx = 0
        for r in range(row, row + 3):
            for c in range(col, col + 3):
                grid[r][c] = digits[idx]
                idx += 1

    @staticmethod
    def _is_valid(grid: list[list[int]], row: int, col: int, num: int) -> bool:
        """Return True if placing num at (row, col) breaks no Sudoku rule."""
        if num in grid[row]:
            return False
        if num in (grid[r][col] for r in range(9)):
            return False
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if grid[r][c] == num:
                    return False
        return True

    @staticmethod
    def _solve(grid: list[list[int]]) -> bool:
        """Fill empty cells using backtracking (used during generation)."""
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    digits = list(range(1, 10))
                    random.shuffle(digits)   # random order → different solutions each time
                    for num in digits:
                        if PuzzleFactory._is_valid(grid, r, c, num):
                            grid[r][c] = num
                            if PuzzleFactory._solve(grid):
                                return True
                            grid[r][c] = 0
                    return False
        return True

    # ── Step 2 — shuffle the solved board ─────────────────────────────────────

    @staticmethod
    def _shuffle(grid: list[list[int]]) -> None:
        """Apply random validity-preserving transformations to the solved grid."""
        # Swap rows within the same 3-row band
        for band in range(3):
            rows = random.sample(range(band * 3, band * 3 + 3), 3)
            for i, r in enumerate(rows):
                grid[band * 3 + i], grid[r] = grid[r], grid[band * 3 + i]

        # Swap columns within the same 3-column band (transpose, swap rows, transpose)
        grid[:] = [list(row) for row in zip(*grid)]  # transpose
        for band in range(3):
            cols = random.sample(range(band * 3, band * 3 + 3), 3)
            for i, c in enumerate(cols):
                grid[band * 3 + i], grid[c] = grid[c], grid[band * 3 + i]
        grid[:] = [list(row) for row in zip(*grid)]  # transpose back

        # Swap entire row-bands
        bands = random.sample(range(3), 3)
        new_grid = []
        for b in bands:
            new_grid.extend(grid[b * 3: b * 3 + 3])
        grid[:] = new_grid

        # Permute digits (1→a, 2→b … 9→i) — changes numbers, not structure
        perm = random.sample(range(1, 10), 9)
        mapping = {old: new for old, new in enumerate(perm, 1)}
        for r in range(9):
            for c in range(9):
                grid[r][c] = mapping[grid[r][c]]

    # ── Step 3 — remove digits ────────────────────────────────────────────────

    @staticmethod
    def _count_solutions(grid: list[list[int]], limit: int = 2) -> int:
        """Count solutions up to limit (stops early — we only need to know
        if there are 0, 1, or 2+)."""
        for r in range(9):
            for c in range(9):
                if grid[r][c] == 0:
                    count = 0
                    for num in range(1, 10):
                        if PuzzleFactory._is_valid(grid, r, c, num):
                            grid[r][c] = num
                            count += PuzzleFactory._count_solutions(grid, limit - count)
                            grid[r][c] = 0
                            if count >= limit:
                                return count
                    return count
        return 1   # no empty cell found — this is a complete solution

    @staticmethod
    def _remove_digits(grid: list[list[int]], count: int) -> None:
        """Remove count digits from the grid, keeping exactly one solution."""
        cells = [(r, c) for r in range(9) for c in range(9)]
        random.shuffle(cells)
        removed = 0
        for r, c in cells:
            if removed >= count:
                break
            backup = grid[r][c]
            grid[r][c] = 0
            # Verify uniqueness — put the digit back if uniqueness is lost
            check = copy.deepcopy(grid)
            if PuzzleFactory._count_solutions(check) != 1:
                grid[r][c] = backup
            else:
                removed += 1
