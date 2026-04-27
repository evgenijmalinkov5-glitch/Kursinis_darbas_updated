"""
main.py — CLI entry point for the Sudoku Solver.

Run:
    python main.py

The menu lets the user:
  1. Choose a puzzle difficulty (Factory Method creates the board).
  2. Choose a solver (Polymorphism — both share the same interface).
  3. Display, solve, and save results to CSV (FileManager Singleton).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from models.board import SudokuBoard
from models.game import SudokuGame
from patterns.factory import PuzzleFactory
from solvers.backtracking import BacktrackingSolver
from solvers.constraint import ConstraintSolver
from utils.file_manager import FileManager


def pick_difficulty() -> SudokuBoard:
    """Let the user choose a puzzle difficulty and return the board."""
    options = PuzzleFactory.available_difficulties()
    print("\nAvailable difficulties:")
    for i, d in enumerate(options, 1):
        print(f"  {i}. {d}")
    while True:
        choice = input("Enter number: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return PuzzleFactory.create(options[int(choice) - 1])
        print("  Invalid choice, try again.")


def pick_solver(board: SudokuBoard):
    """Let the user choose a solver and return a concrete BaseSolver."""
    solvers = {
        "1": ("BacktrackingSolver", lambda: BacktrackingSolver(board)),
        "2": ("ConstraintSolver",   lambda: ConstraintSolver(board)),
    }
    print("\nChoose solver:")
    for key, (name, _) in solvers.items():
        print(f"  {key}. {name}")
    while True:
        choice = input("Enter number: ").strip()
        if choice in solvers:
            name, factory = solvers[choice]
            print(f"  Selected: {name}")
            return factory()
        print("  Invalid choice, try again.")


def main() -> None:
    print("=" * 40)
    print("       Sudoku Solver — OOP Project")
    print("=" * 40)

    board = pick_difficulty()
    solver = pick_solver(board)
    fm = FileManager()  # Singleton — same instance throughout
    game = SudokuGame(board, solver, fm)

    while True:
        print("\n--- Menu ---")
        print("  1. Display current board")
        print("  2. Solve puzzle")
        print("  3. Save result to CSV")
        print("  4. Load puzzle from CSV")
        print("  5. Quit")

        action = input("Choose action: ").strip()

        if action == "1":
            game.display()

        elif action == "2":
            solved = game.solve()
            if solved:
                game.display()

        elif action == "3":
            game.save()

        elif action == "4":
            path = input("Enter CSV file path: ").strip()
            try:
                grid = fm.load_puzzle(path)
                new_board = SudokuBoard(grid)
                new_solver = pick_solver(new_board)
                game = SudokuGame(new_board, new_solver, fm)
                print("Puzzle loaded successfully.")
                game.display()
            except (FileNotFoundError, ValueError) as exc:
                print(f"Error: {exc}")

        elif action == "5":
            print("Goodbye!")
            break

        else:
            print("Unknown action.")


if __name__ == "__main__":
    main()
