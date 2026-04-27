"""
FileManager module.
Demonstrates:
  - Singleton pattern: only one FileManager instance exists at runtime.
    All parts of the application share the same object, which centralises
    all I/O logic and prevents accidental parallel file writes.
  - File I/O requirement: save puzzles to CSV and load them back.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime


class FileManager:
    """Handles all file I/O for the Sudoku application.

    Singleton pattern:
      __new__ checks whether an instance already exists.  If it does, the
      existing object is returned instead of creating a new one.  This
      guarantees a single, shared I/O manager throughout the program.

    Why Singleton here?
      - File writes from multiple objects to the same path risk corruption.
      - Centralising I/O means output directory management happens once.
      - Simpler than passing a manager reference everywhere.

    Why not Factory or Builder?
      - Factory creates *different* objects for each call (many boards).
      - Builder assembles a complex object step-by-step.
      Neither fits the "exactly one shared manager" requirement.
    """

    _instance: FileManager | None = None

    def __new__(cls) -> FileManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._output_dir = "output"
            os.makedirs(cls._instance._output_dir, exist_ok=True)
        return cls._instance

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------

    def save_puzzle(
        self,
        grid: list[list[int]],
        label: str = "puzzle",
    ) -> str:
        """Save a 9×9 grid to a timestamped CSV file.

        Args:
            grid: The 9×9 integer grid to save.
            label: Filename prefix (e.g. 'solution', 'puzzle').

        Returns:
            The full path to the written file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{label}_{timestamp}.csv"
        filepath = os.path.join(self._output_dir, filename)

        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerows(grid)

        return filepath

    def save_result(
        self,
        puzzle: list[list[int]],
        solution: list[list[int]],
        solver_name: str,
        steps: int,
        player_grid: list[list[int]] | None = None,
        is_correct: list[list[bool]] | None = None,
        is_error: list[list[bool]] | None = None,
        elapsed_seconds: int = 0,
        mistakes: int = 0,
    ) -> str:
        """Save puzzle, solution, and full player progress to one CSV.

        Format:
          - 'puzzle'           → 9 rows of original clues
          - 'player'           → 9 rows of what the player typed (0 = empty)
          - 'correct'          → 9 rows of 0/1 flags (1 = player confirmed correct)
          - 'error'            → 9 rows of 0/1 flags (1 = cell currently wrong/red)
          - 'solution'         → 9 rows of full solution
          - 'meta'             → solver, steps, elapsed_seconds, mistakes, timestamp

        Returns:
            Path of the written file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(self._output_dir, f"result_{timestamp}.csv")

        empty = [[0]*9 for _ in range(9)]
        empty_flags = [[0]*9 for _ in range(9)]

        pg = player_grid if player_grid is not None else empty
        ic = [[1 if v else 0 for v in row] for row in is_correct] if is_correct is not None else empty_flags
        ie = [[1 if v else 0 for v in row] for row in is_error]   if is_error   is not None else empty_flags

        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["puzzle"])
            writer.writerows(puzzle)
            writer.writerow(["player"])
            writer.writerows(pg)
            writer.writerow(["correct"])
            writer.writerows(ic)
            writer.writerow(["error"])
            writer.writerows(ie)
            writer.writerow(["solution"])
            writer.writerows(solution)
            writer.writerow(["meta", solver_name, "steps", steps,
                             "elapsed", elapsed_seconds, "mistakes", mistakes,
                             "timestamp", timestamp])

        return filepath

    def load_session(self, filepath: str) -> dict:
        """Load a full saved session from a CSV written by save_result.

        Returns a dict with keys:
          puzzle, player, is_correct, is_error, solution,
          elapsed_seconds, mistakes.
        Raises FileNotFoundError or ValueError on bad input.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        with open(filepath, "r", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))

        def _extract(rows, header):
            """Return the 9 data rows that follow *header* label row."""
            for i, row in enumerate(rows):
                if row and row[0] == header:
                    chunk = rows[i+1 : i+10]
                    return [[int(v) for v in r] for r in chunk if len(r) == 9]
            return None

        puzzle   = _extract(rows, "puzzle")
        player   = _extract(rows, "player")
        correct  = _extract(rows, "correct")
        error    = _extract(rows, "error")
        solution = _extract(rows, "solution")

        if not puzzle or len(puzzle) != 9:
            raise ValueError("Could not read puzzle grid from file.")

        # Parse meta row
        elapsed  = 0
        mistakes = 0
        for row in rows:
            if row and row[0] == "meta":
                try:
                    elapsed  = int(row[row.index("elapsed")  + 1])
                    mistakes = int(row[row.index("mistakes") + 1])
                except (ValueError, IndexError):
                    pass
                break

        return {
            "puzzle":          puzzle,
            "player":          player  or [[0]*9 for _ in range(9)],
            "is_correct":      [[bool(v) for v in r] for r in correct] if correct else [[False]*9]*9,
            "is_error":        [[bool(v) for v in r] for r in error]   if error   else [[False]*9]*9,
            "solution":        solution or [[0]*9 for _ in range(9)],
            "elapsed_seconds": elapsed,
            "mistakes":        mistakes,
        }

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------

    def load_puzzle(self, filepath: str) -> list[list[int]]:
        """Load a 9×9 puzzle from a CSV file.

        Supports two formats:
          - Plain: exactly 9 rows of 9 digits.
          - save_result format: 'puzzle' header row, then 9 puzzle rows,
            then 'solution' header row, then 9 solution rows. Only the
            puzzle section is loaded.

        Args:
            filepath: Path to the CSV file.

        Returns:
            A 9×9 list of integers.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file does not contain a valid 9×9 grid.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Puzzle file not found: {filepath}")

        rows: list[list[str]] = []
        with open(filepath, "r", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))

        # Detect save_result format: first row is ['puzzle']
        if rows and rows[0] == ["puzzle"]:
            # Extract only the 9 rows after the 'puzzle' header
            data_rows = [r for r in rows[1:10] if len(r) == 9]
        else:
            data_rows = [r for r in rows if len(r) == 9]

        grid: list[list[int]] = []
        for row in data_rows:
            try:
                grid.append([int(v) for v in row])
            except ValueError as exc:
                raise ValueError(f"Non-integer value in puzzle file: {exc}") from exc

        if len(grid) != 9:
            raise ValueError(
                f"Expected 9 rows, found {len(grid)} in '{filepath}'."
            )
        return grid
