# Sudoku Solver — OOP Coursework

A fully playable Sudoku game in Python demonstrating all four OOP pillars, Factory Method and Singleton patterns, file I/O, and unit testing.

## Quick start

```bash
python gui.py                          # Graphical window (recommended)
python main.py                         # Terminal menu
python -m unittest discover tests      # Run 34 unit tests
```

## Features

- **Random puzzle generator** — unique puzzle every time, guaranteed one solution
- **Two game modes** — Play yourself or Auto-solve
- **Play mode** — timer, mistake counter (max 5), pause/resume, autosave/resume
- **Error highlighting** — wrong digits turn red instantly
- **Victory & Game Over popups** — with time and mistake stats
- **Two solvers** — Backtracking and Constraint (selectable in Auto-solve mode)
- **CSV export** — saves puzzle, solution, and player mistake digits
- **JSON autosave** — resumes exactly where you left off

## Project structure

| File | OOP concept |
|---|---|
| `models/cell.py` | Encapsulation |
| `models/board.py` | Composition |
| `models/game.py` | Aggregation |
| `solvers/base_solver.py` | Abstraction |
| `solvers/backtracking.py` | Inheritance, Polymorphism |
| `solvers/constraint.py` | Inheritance, Polymorphism |
| `patterns/factory.py` | Factory Method pattern + puzzle generator |
| `utils/file_manager.py` | Singleton pattern, CSV / JSON File I/O |
| `gui.py` | tkinter graphical interface |
| `main.py` | Terminal CLI |
| `tests/test_sudoku.py` | 34 unit tests (unittest) |

## Requirements

Python 3.10+. No third-party packages — `tkinter`, `csv`, `json`, and `abc` are all part of the Python standard library.
