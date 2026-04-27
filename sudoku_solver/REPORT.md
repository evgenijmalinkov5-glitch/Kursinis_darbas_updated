# Sudoku Solver — OOP Coursework Report

## Table of Contents

1. [Introduction](#introduction)
2. [Body / Analysis](#body--analysis)
3. [Results and Summary](#results-and-summary)
4. [Resources](#resources)

---

## Introduction

### What is this application?

This project implements a **Sudoku Solver** in Python using Object-Oriented Programming principles. The application provides a graphical window where the player can either solve puzzles themselves or watch an algorithm solve them automatically. Every session generates a fresh, unique puzzle — no two games are ever the same.

A Sudoku puzzle is a 9×9 grid partially filled with digits 1–9. The goal is to fill every empty cell so that each row, column, and 3×3 box contains all digits from 1 to 9 without repetition.

### How to run the program

**Prerequisites:** Python 3.10 or higher (no third-party packages required — `tkinter` is included with Python).

```bash
# Clone the repository
git clone https://github.com/<your-username>/sudoku-solver.git
cd sudoku-solver

# Launch the graphical interface (recommended)
python gui.py

# Or use the terminal menu
python main.py

# Run all unit tests
python -m unittest discover tests
```

### How to use the program

When `gui.py` is launched a window opens with two modes selectable at the top:

**🎮 Play yourself mode:**
1. Choose a difficulty (Easy / Medium / Hard) and press **Load Preset** — a unique random puzzle is generated every time.
2. Click any empty cell and type a digit 1–9.
3. Wrong digits are highlighted in red instantly. Each mistake adds to the **❌ 0 / 5** counter.
4. The **⏱ timer** starts on the first keystroke and stops when the puzzle is completed.
5. Reaching 5 mistakes triggers a Game Over popup. Finishing correctly triggers a 🎉 victory popup showing time and mistake count.
6. Press **⏸ Pause** to hide the grid and stop the timer. Press **▶ Resume** to continue.
7. Progress is **autosaved** automatically after every move — press **Resume Saved** to pick up exactly where you left off after restarting the program.
8. Press **💾 Save** to export the puzzle, solution, and your mistake digits to a CSV file.

**🤖 Auto-solve mode:**
1. Choose a difficulty and press **Load Preset**.
2. Pick a solver (Backtracking or Constraint) and press **✔ Solve puzzle**.
3. The algorithm fills the board and the status bar shows how many steps it took.

---

## Body / Analysis

### Project structure

```
sudoku_solver/
├── gui.py                   # Graphical interface (tkinter)
├── main.py                  # Terminal CLI entry point
├── models/
│   ├── cell.py              # SudokuCell  — Encapsulation
│   ├── board.py             # SudokuBoard — Composition
│   └── game.py              # SudokuGame  — Aggregation
├── solvers/
│   ├── base_solver.py       # BaseSolver  — Abstraction
│   ├── backtracking.py      # BacktrackingSolver — Inheritance, Polymorphism
│   └── constraint.py        # ConstraintSolver   — Inheritance, Polymorphism
├── patterns/
│   └── factory.py           # PuzzleFactory — Factory Method pattern
├── utils/
│   └── file_manager.py      # FileManager — Singleton pattern, File I/O
├── tests/
│   └── test_sudoku.py       # 34 unit tests (unittest framework)
└── output/                  # Auto-created; holds saved CSV files and resume.json
```

---

### OOP Pillar 1 — Encapsulation

**What it is:** Bundling data (attributes) and the methods that operate on them into a single class, and restricting direct access to internal state through access modifiers and properties.

**How it works:** In Python, name-mangling (`__attribute`) makes attributes private. Properties (`@property`, `@setter`) expose controlled read/write access with built-in validation logic.

**How it is used:** `SudokuCell` stores its digit as `__value` and its fixed status as `__is_fixed`. Both are private. External code reads and writes the digit only through the `value` property, which enforces two rules: a fixed (given) cell cannot be overwritten, and only digits 0–9 are accepted.

```python
# models/cell.py

class SudokuCell:
    def __init__(self, value: int = 0, is_fixed: bool = False) -> None:
        self.__value: int = value       # Private — cannot be accessed as cell.__value
        self.__is_fixed: bool = is_fixed

    @property
    def value(self) -> int:
        return self.__value

    @value.setter
    def value(self, val: int) -> None:
        if self.__is_fixed:
            raise ValueError("Cannot modify a fixed (given) cell.")
        if not 0 <= val <= 9:
            raise ValueError(f"Value must be 0–9, got {val}.")
        self.__value = val
```

Without encapsulation a solver could accidentally overwrite a clue cell or write an illegal digit — the property prevents both silently.

---

### OOP Pillar 2 — Abstraction

**What it is:** Hiding implementation details behind a clean interface. Callers interact with an abstraction (the interface) and are shielded from the complexity underneath.

**How it works:** Python's `abc` module provides `ABC` (Abstract Base Class) and `@abstractmethod`. A class that inherits from `ABC` and declares an `@abstractmethod` cannot be instantiated — only its concrete subclasses can, after they implement every abstract method.

**How it is used:** `BaseSolver` declares `solve() -> bool` as abstract. Any class that inherits from `BaseSolver` is forced to provide a concrete implementation of `solve()`. `SudokuGame` holds a reference typed as `BaseSolver` — it calls `solver.solve()` without caring whether the object is a `BacktrackingSolver` or a `ConstraintSolver`.

```python
# solvers/base_solver.py

from abc import ABC, abstractmethod

class BaseSolver(ABC):
    def __init__(self, board: SudokuBoard) -> None:
        self._board = board
        self._steps = 0

    @abstractmethod
    def solve(self) -> bool:
        """Subclasses must implement this with a concrete algorithm."""
```

This means adding a third solver in the future (e.g. `DancingLinksSolver`) requires only writing one new class — no changes to `SudokuGame` or any other caller.

---

### OOP Pillar 3 — Inheritance

**What it is:** A class (child) deriving structure and behaviour from another class (parent), and optionally overriding or extending it.

**How it works:** Using `class Child(Parent)`. The child receives all non-private attributes and methods from the parent. `super().__init__()` calls the parent constructor to initialise the shared state.

**How it is used:** Both `BacktrackingSolver` and `ConstraintSolver` inherit from `BaseSolver`. They reuse `__init__`, the `steps` property, and the `board` property without repeating code. Each overrides only `solve()` with a different algorithm.

```python
# solvers/backtracking.py

class BacktrackingSolver(BaseSolver):   # Inherits from BaseSolver
    def __init__(self, board: SudokuBoard) -> None:
        super().__init__(board)         # Reuses parent __init__

    def solve(self) -> bool:            # Overrides abstract method
        empty = self._board.find_empty()
        if empty is None:
            return True
        row, col = empty
        for num in range(1, 10):
            if self._board.is_valid_placement(row, col, num):
                self._board.set_value(row, col, num)
                self._steps += 1        # Uses inherited _steps attribute
                if self.solve():
                    return True
                self._board.set_value(row, col, 0)
        return False
```

`ConstraintSolver` is a second child with a completely different `solve()` body (constraint propagation + backtracking) but the same inherited interface.

---

### OOP Pillar 4 — Polymorphism

**What it is:** The ability to treat objects of different concrete types through a common interface, with each object responding to the same call in its own way.

**How it works:** When `solver.solve()` is called, Python dispatches to whichever concrete class the solver actually is at runtime. The caller never checks the type — it relies on the shared `BaseSolver` interface.

**How it is used:** In the GUI the player picks a solver from a dropdown — the same `_solve()` method handles both without any `if/else` on the type:

```python
# gui.py

solver = (BacktrackingSolver(board)
          if name == "Backtracking" else ConstraintSolver(board))
# Both are called identically — Polymorphism
success = solver.solve()
```

A unit test demonstrates runtime swapping directly:

```python
# tests/test_sudoku.py

def test_solver_can_be_swapped(self):
    new_solver = ConstraintSolver(new_board)
    self.game.solver = new_solver       # Swap at runtime — Polymorphism
    self.assertIsInstance(self.game.solver, ConstraintSolver)
```

---

### Composition and Aggregation

**Composition** — `SudokuBoard` owns its `SudokuCell` objects. The cells are created inside `__build_cells()` at construction time and cannot exist without the board. This is a *strong* ownership relationship.

```python
# models/board.py

class SudokuBoard:
    def __init__(self, grid=None):
        self.__cells = self.__build_cells(grid)   # Board creates its own cells

    def __build_cells(self, grid):
        return [
            [SudokuCell(grid[r][c] if grid else 0,
                        is_fixed=(grid[r][c] != 0 if grid else False))
             for c in range(self.SIZE)]
            for r in range(self.SIZE)
        ]
```

**Aggregation** — `SudokuGame` holds references to a `SudokuBoard`, a `BaseSolver`, and a `FileManager`, but did not create them. They are passed in through the constructor and can outlive the game object. This is a *weak* ownership relationship.

```python
# models/game.py

class SudokuGame:
    def __init__(self, board, solver, file_manager=None):
        self.__board = board            # Aggregated — not created here
        self.__solver = solver          # Aggregated — not created here
        self.__file_manager = file_manager or FileManager()
```

---

### Design Pattern — Factory Method

**What it is:** A creational pattern that delegates object construction to a dedicated factory, hiding the details of how objects are built from callers.

**Why Factory Method?** Each call to `PuzzleFactory.create()` generates a completely unique random puzzle. Without a factory, every caller would need to know the generation algorithm — tight coupling. The factory offers a single stable API: `PuzzleFactory.create("hard")`.

**Why not Singleton?** Singleton ensures only one instance exists globally. We need many independent boards (one per game session), so Singleton does not fit.

**Why not Builder?** Builder is for constructing complex objects step-by-step with many optional parts. A Sudoku board has no optional construction steps — the grid is always the same shape.

The generator works in four stages:

1. **Fill** the three independent diagonal 3×3 boxes with random digits.
2. **Solve** the remaining cells with backtracking using a randomly shuffled digit order — producing a complete random valid board.
3. **Shuffle** the solved board by swapping rows within bands, columns within bands, entire row-bands, and remapping digits — all operations that preserve Sudoku validity.
4. **Remove digits** one by one, verifying after each removal that exactly one solution still exists, until the target clue count for the chosen difficulty is reached.

```python
# patterns/factory.py

class PuzzleFactory:
    _CLUES_TO_REMOVE = {
        "easy":   36,   # ~45 clues remain
        "medium": 46,   # ~35 clues remain
        "hard":   54,   # ~27 clues remain
    }

    @staticmethod
    def create(difficulty: str = "easy") -> SudokuBoard:
        grid = PuzzleFactory._generate()
        PuzzleFactory._remove_digits(grid, PuzzleFactory._CLUES_TO_REMOVE[difficulty])
        return SudokuBoard(grid)
```

---

### Design Pattern — Singleton (FileManager)

`FileManager` guarantees only one instance exists — ensured by overriding `__new__`:

```python
# utils/file_manager.py

class FileManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            os.makedirs("output", exist_ok=True)
        return cls._instance
```

All parts of the application call `FileManager()` and receive the same shared object, preventing race conditions on file writes and ensuring the output directory is created exactly once.

---

### Reading from file and writing to file

`FileManager` handles CSV I/O using the built-in `csv` module. The GUI additionally uses `json` for autosave.

**CSV — puzzle results** (`save_result`): writes the original puzzle, the solution, the player's mistake digits, and metadata into a single timestamped CSV file. Each non-zero value in the mistakes section is the exact wrong digit the player typed, so they can review their errors later.

```
puzzle
5,3,0,0,7,0,...
...
solution
5,3,4,6,7,8,...
...
mistakes
0,0,2,0,0,0,...    ← player typed 2 here (wrong)
0,9,0,0,0,0,...    ← player typed 9 here (wrong)
...
solver,BacktrackingSolver,steps,42,timestamp,20260427_...
```

**JSON — autosave / resume**: during Play mode the full game state (current grid, correct cells, errors, elapsed time, mistake count, difficulty) is saved to `output/resume.json` after each move. When the player restarts and presses **Resume Saved**, the state is restored exactly — timer, mistakes, and all cell colours included.

---

### Graphical User Interface (gui.py)

The GUI is built with Python's built-in `tkinter` library and connects directly to the OOP model layer. The GUI is purely a presentation and interaction layer — all logic lives in the model classes.

**Game modes:**

| Mode | Visible controls | Hidden controls |
|---|---|---|
| 🎮 Play yourself | Error highlighting, timer, mistake counter, Pause | Solve button |
| 🤖 Auto-solve | Solver dropdown, Solve button | Timer, mistakes, Pause |

**Play mode features:**

- **Error highlighting** — wrong digits turn the cell dark red instantly; fixing the digit clears it.
- **Timer** — starts on the first keystroke, pauses with the ⏸ button, stops on completion.
- **Mistake counter** — counts each unique wrong digit placed, maximum 5.
- **Pause / Resume** — hides all cell values so the player cannot see the numbers while paused.
- **Victory popup** — shown on completion; displays time and a mistake rating (Perfect 🏆 if zero mistakes).
- **Game Over popup** — shown at 5 mistakes; the board locks and the player is told to switch to Auto-solve to see the solution.
- **Autosave / Resume** — progress saved to `output/resume.json` after every move, restored on next launch.

**Grid layout** uses a two-level frame hierarchy: outer frames separated by 3 px (thick lines between 3×3 boxes) and inner frames separated by 1 px (thin lines between individual cells), matching the standard printed Sudoku appearance.

---

### Testing

All core classes are covered by 34 unit tests written with the `unittest` framework.

```bash
python -m unittest discover tests
# Ran 34 tests in ~6s — OK
```

| Class | Tests | What is verified |
|---|---|---|
| `SudokuCell` | 7 | Encapsulation: private access, setter validation, fixed-cell guard |
| `SudokuBoard` | 9 | Composition, placement validity, empty-cell search |
| `BacktrackingSolver` | 3 | Solves puzzle, counts steps, inherits `board` property |
| `ConstraintSolver` | 3 | Same contract as Backtracking via Polymorphism |
| `PuzzleFactory` | 5 | All difficulties created, unique puzzles generated, invalid difficulty raises |
| `FileManager` | 4 | Singleton identity, save + load round-trip, error handling |
| `SudokuGame` | 3 | Solve returns True, solver swap (Polymorphism), save to file |

---

## Results and Summary

### Results

- All four OOP pillars are demonstrated in separate, clearly named classes: `SudokuCell` (Encapsulation), `BaseSolver` (Abstraction), `BacktrackingSolver` / `ConstraintSolver` (Inheritance + Polymorphism), `SudokuBoard` (Composition), and `SudokuGame` (Aggregation).
- Two design patterns are implemented: **Factory Method** (`PuzzleFactory`) for random puzzle generation and **Singleton** (`FileManager`) for centralised I/O — both with written justification for why alternative patterns were not chosen.
- The puzzle generator produces a unique, uniquely-solvable puzzle on every load using shuffling and digit-removal with solution-count verification, making the game genuinely replayable across all three difficulty levels.
- The GUI was the most complex part of the implementation — managing cell state (fixed, user, correct, error, solved, paused) across 81 cells simultaneously while keeping the view layer fully separate from the model layer required careful state design.
- 34 unit tests provide regression coverage across all model and utility classes; the autosave, pause, victory, and game-over paths were validated manually through all game states.

### Conclusions

This coursework produced a fully playable Sudoku game that demonstrates all four OOP pillars, two design patterns, file I/O (CSV and JSON), and comprehensive unit testing. The abstract `BaseSolver` interface made it trivial to add a second algorithm without modifying any existing code — a direct demonstration of the Open/Closed principle. The Factory Method pattern's puzzle generator replaced static hardcoded grids, turning a limited demo into a genuinely replayable game. Future extensions could include an online leaderboard using a web API so players can compare times globally, a hint system that reveals one correct cell without counting as a mistake, difficulty rating based on the number of logical deduction steps required before backtracking, and a mobile adaptation using a framework such as Kivy.

---

## Resources

- [PEP8 Style Guide](https://peps.python.org/pep-0008/)
- [Python `abc` module](https://docs.python.org/3/library/abc.html)
- [Python `unittest` framework](https://docs.python.org/3/library/unittest.html)
- [Python `csv` module](https://docs.python.org/3/library/csv.html)
- [Python `json` module](https://docs.python.org/3/library/json.html)
- [Python `tkinter` module](https://docs.python.org/3/library/tkinter.html)
- [Design Patterns — Refactoring Guru](https://refactoring.guru/design-patterns)
- [Markdown syntax](https://www.markdownguide.org/basic-syntax/)
- [Clean Code in Python — book](https://www.packtpub.com/product/clean-code-in-python/9781800560215)
- [Pro Git Book](https://git-scm.com/book/en/v2)
