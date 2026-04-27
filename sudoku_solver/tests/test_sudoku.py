"""
Unit tests for the Sudoku Solver project.
Covers: SudokuCell, SudokuBoard, BacktrackingSolver, ConstraintSolver,
        PuzzleFactory, FileManager, SudokuGame.
Run with: python -m unittest discover tests
"""

import os
import sys
import tempfile
import unittest

# Make sure the project root is on the path when tests are run directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models.board import SudokuBoard
from models.cell import SudokuCell
from models.game import SudokuGame
from patterns.factory import PuzzleFactory
from solvers.backtracking import BacktrackingSolver
from solvers.constraint import ConstraintSolver
from utils.file_manager import FileManager


# ---------------------------------------------------------------------------
# SudokuCell tests
# ---------------------------------------------------------------------------

class TestSudokuCell(unittest.TestCase):
    """Tests for Encapsulation in SudokuCell."""

    def test_initial_value(self):
        cell = SudokuCell(5)
        self.assertEqual(cell.value, 5)

    def test_empty_cell_is_empty(self):
        cell = SudokuCell()
        self.assertTrue(cell.is_empty())

    def test_non_empty_cell_not_empty(self):
        cell = SudokuCell(3)
        self.assertFalse(cell.is_empty())

    def test_set_value(self):
        cell = SudokuCell(0)
        cell.value = 7
        self.assertEqual(cell.value, 7)

    def test_fixed_cell_raises_on_write(self):
        cell = SudokuCell(5, is_fixed=True)
        with self.assertRaises(ValueError):
            cell.value = 3

    def test_out_of_range_raises(self):
        cell = SudokuCell(0)
        with self.assertRaises(ValueError):
            cell.value = 10

    def test_negative_raises(self):
        cell = SudokuCell(0)
        with self.assertRaises(ValueError):
            cell.value = -1


# ---------------------------------------------------------------------------
# SudokuBoard tests
# ---------------------------------------------------------------------------

class TestSudokuBoard(unittest.TestCase):
    """Tests for SudokuBoard, including Composition with SudokuCell."""

    def setUp(self):
        self.empty_board = SudokuBoard()
        self.partial = SudokuBoard([
            [5, 3, 0, 0, 7, 0, 0, 0, 0],
            [6, 0, 0, 1, 9, 5, 0, 0, 0],
            [0, 9, 8, 0, 0, 0, 0, 6, 0],
            [8, 0, 0, 0, 6, 0, 0, 0, 3],
            [4, 0, 0, 8, 0, 3, 0, 0, 1],
            [7, 0, 0, 0, 2, 0, 0, 0, 6],
            [0, 6, 0, 0, 0, 0, 2, 8, 0],
            [0, 0, 0, 4, 1, 9, 0, 0, 5],
            [0, 0, 0, 0, 8, 0, 0, 7, 9],
        ])

    def test_get_value(self):
        self.assertEqual(self.partial.get_value(0, 0), 5)

    def test_find_empty_returns_empty_position(self):
        pos = self.partial.find_empty()
        self.assertIsNotNone(pos)
        r, c = pos
        self.assertEqual(self.partial.get_value(r, c), 0)

    def test_empty_board_has_empty(self):
        self.assertEqual(self.empty_board.find_empty(), (0, 0))

    def test_valid_placement(self):
        self.assertTrue(self.empty_board.is_valid_placement(0, 0, 1))

    def test_invalid_placement_row(self):
        self.assertFalse(self.partial.is_valid_placement(0, 2, 5))

    def test_invalid_placement_col(self):
        self.assertFalse(self.partial.is_valid_placement(1, 0, 6))

    def test_invalid_placement_box(self):
        self.assertFalse(self.partial.is_valid_placement(1, 1, 5))

    def test_set_value(self):
        self.empty_board.set_value(0, 0, 9)
        self.assertEqual(self.empty_board.get_value(0, 0), 9)

    def test_get_grid_shape(self):
        grid = self.empty_board.get_grid()
        self.assertEqual(len(grid), 9)
        self.assertTrue(all(len(row) == 9 for row in grid))


# ---------------------------------------------------------------------------
# Solver tests (Polymorphism / Inheritance)
# ---------------------------------------------------------------------------

EASY_GRID = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],
    [6, 0, 0, 1, 9, 5, 0, 0, 0],
    [0, 9, 8, 0, 0, 0, 0, 6, 0],
    [8, 0, 0, 0, 6, 0, 0, 0, 3],
    [4, 0, 0, 8, 0, 3, 0, 0, 1],
    [7, 0, 0, 0, 2, 0, 0, 0, 6],
    [0, 6, 0, 0, 0, 0, 2, 8, 0],
    [0, 0, 0, 4, 1, 9, 0, 0, 5],
    [0, 0, 0, 0, 8, 0, 0, 7, 9],
]


class TestBacktrackingSolver(unittest.TestCase):

    def test_solves_easy_puzzle(self):
        board = SudokuBoard(EASY_GRID)
        solver = BacktrackingSolver(board)
        self.assertTrue(solver.solve())
        self.assertIsNone(board.find_empty())

    def test_steps_incremented(self):
        board = SudokuBoard(EASY_GRID)
        solver = BacktrackingSolver(board)
        solver.solve()
        self.assertGreater(solver.steps, 0)

    def test_inherits_board_property(self):
        board = SudokuBoard()
        solver = BacktrackingSolver(board)
        self.assertIs(solver.board, board)


class TestConstraintSolver(unittest.TestCase):

    def test_solves_easy_puzzle(self):
        board = SudokuBoard(EASY_GRID)
        solver = ConstraintSolver(board)
        self.assertTrue(solver.solve())
        self.assertIsNone(board.find_empty())

    def test_steps_incremented(self):
        board = SudokuBoard(EASY_GRID)
        solver = ConstraintSolver(board)
        solver.solve()
        self.assertGreater(solver.steps, 0)

    def test_inherits_board_property(self):
        board = SudokuBoard()
        solver = ConstraintSolver(board)
        self.assertIs(solver.board, board)


# ---------------------------------------------------------------------------
# PuzzleFactory tests (Factory Method pattern)
# ---------------------------------------------------------------------------

class TestPuzzleFactory(unittest.TestCase):

    def test_creates_easy_board(self):
        board = PuzzleFactory.create("easy")
        self.assertIsInstance(board, SudokuBoard)

    def test_creates_medium_board(self):
        board = PuzzleFactory.create("medium")
        self.assertIsInstance(board, SudokuBoard)

    def test_creates_hard_board(self):
        board = PuzzleFactory.create("hard")
        self.assertIsInstance(board, SudokuBoard)

    def test_invalid_difficulty_raises(self):
        with self.assertRaises(ValueError):
            PuzzleFactory.create("impossible")

    def test_available_difficulties(self):
        difficulties = PuzzleFactory.available_difficulties()
        self.assertIn("easy", difficulties)
        self.assertIn("hard", difficulties)


# ---------------------------------------------------------------------------
# FileManager tests (Singleton + File I/O)
# ---------------------------------------------------------------------------

class TestFileManager(unittest.TestCase):

    def test_singleton_same_instance(self):
        fm1 = FileManager()
        fm2 = FileManager()
        self.assertIs(fm1, fm2)

    def test_save_and_load_puzzle(self):
        fm = FileManager()
        grid = [[i + j for j in range(9)] for i in range(9)]
        path = fm.save_puzzle(grid, label="test")
        self.assertTrue(os.path.exists(path))
        loaded = fm.load_puzzle(path)
        self.assertEqual(loaded, grid)
        os.remove(path)

    def test_load_nonexistent_raises(self):
        fm = FileManager()
        with self.assertRaises(FileNotFoundError):
            fm.load_puzzle("does_not_exist.csv")

    def test_save_result_creates_file(self):
        fm = FileManager()
        grid = [[0] * 9 for _ in range(9)]
        path = fm.save_result(grid, grid, "BacktrackingSolver", 42)
        self.assertTrue(os.path.exists(path))
        os.remove(path)


# ---------------------------------------------------------------------------
# SudokuGame tests (Aggregation)
# ---------------------------------------------------------------------------

class TestSudokuGame(unittest.TestCase):

    def setUp(self):
        self.board = PuzzleFactory.create("easy")
        self.solver = BacktrackingSolver(self.board)
        self.game = SudokuGame(self.board, self.solver)

    def test_solve_returns_true(self):
        self.assertTrue(self.game.solve())

    def test_solver_can_be_swapped(self):
        """Polymorphism: replacing solver at runtime works seamlessly."""
        new_board = PuzzleFactory.create("easy")
        new_solver = ConstraintSolver(new_board)
        self.game.solver = new_solver
        self.assertIsInstance(self.game.solver, ConstraintSolver)

    def test_save_creates_file(self):
        self.game.solve()
        path = self.game.save()
        self.assertTrue(os.path.exists(path))
        os.remove(path)


if __name__ == "__main__":
    unittest.main()
