"""
gui.py — Tkinter GUI for the Sudoku Solver.

Run:
    python gui.py

Integrates with all existing OOP classes:
  - PuzzleFactory  (Factory Method) — loads and generates puzzles
  - BacktrackingSolver / ConstraintSolver (Polymorphism) — selectable at runtime
  - SudokuBoard + SudokuCell (Composition / Encapsulation) — board model
  - SudokuGame (Aggregation) — coordinates solving and saving
  - FileManager (Singleton) — CSV save / load

Features:
  v2 — Error checking with Auto and Manual modes; soft red highlights.
  v3 — Game mode toggle: Play yourself vs Auto-solve.
  v4 — Solver dropdown moved into Auto-solve row (hidden in Play mode).
       Play mode: timer + mistake counter (max 5 mistakes).
"""

import sys
import os
import copy
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

sys.path.insert(0, os.path.dirname(__file__))

from models.board import SudokuBoard
from models.game import SudokuGame
from patterns.factory import PuzzleFactory
from solvers.backtracking import BacktrackingSolver
from solvers.constraint import ConstraintSolver
from utils.file_manager import FileManager


# ── Colour palette ─────────────────────────────────────────────────────────
BG          = "#1e1e2e"   # window background
GRID_BG     = "#2a2a3d"   # normal empty / user cell
FIXED_BG    = "#313150"   # given clue cell
SOLVED_BG   = "#1e3a2f"   # cell after solve
CORRECT_BG  = "#1e3550"   # player-entered correct digit — blue-tinted
CORRECT_FG  = "#7aa2f7"   # player-entered correct digit text — soft blue
FOCUS_BG    = "#3a3a5c"   # cell while focused (no error)

ERR_BG      = "#3b1a1a"   # wrong cell background — dark muted red
ERR_FG      = "#d97070"   # wrong cell digit      — light red, readable
ERR_FOCUS   = "#4a2020"   # wrong cell while focused

BTN_BG      = "#7c3aed"   # primary button (Solve)
BTN_HOV     = "#6d28d9"
BTN2_BG     = "#0f766e"   # secondary button (Load, Save)
BTN2_HOV    = "#0d6b63"

MODE_PLAY_BG   = "#0f766e"   # active: Play yourself
MODE_PLAY_HOV  = "#0d6b63"
MODE_AUTO_BG   = "#7c3aed"   # active: Auto-solve
MODE_AUTO_HOV  = "#6d28d9"
MODE_INACT_BG  = "#2e2e45"   # inactive mode button

TEXT_FIXED  = "#c0caf5"   # digit colour for clue cells
TEXT_USER   = "#a9b1d6"   # digit colour for user-entered cells
TEXT_SOLVED = "#9ece6a"   # digit colour after solve

BORDER_BOLD  = "#bd93f9"   # thick box-boundary lines
BORDER_INNER = "#3d3d5c"   # thin lines between cells inside a box
STATUS_OK    = "#9ece6a"
STATUS_ERR   = "#f7768e"
STATUS_INFO  = "#7aa2f7"


class SudokuGUI:
    """Main application window — view layer only.

    Keeps the tkinter view layer separate from the OOP model layer.
    SudokuBoard, solvers, and FileManager are used exactly as in main.py —
    the GUI is just a different way to present and interact with them.

    Game modes:
      "play" — the user fills in the grid; timer and mistake counter active.
      "auto" — the solver fills in the grid; only the Solve button is shown.
    """

    CELL        = 58
    PAD         = 18
    FONT_DIGIT  = ("Segoe UI", 22, "bold")
    FONT_LABEL  = ("Segoe UI", 10)
    FONT_STATUS = ("Segoe UI", 10)
    FONT_TITLE  = ("Segoe UI", 16, "bold")
    MAX_MISTAKES = 5

    def __init__(self, root: tk.Tk) -> None:
        """Set up state, build the UI, attach traces, and load the first puzzle."""
        self.root = root
        self.root.title("Sudoku Solver")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self._file_manager = FileManager()
        self._board: SudokuBoard | None = None
        self._original_grid: list[list[int]] = []

        self._vars:           list[list[tk.StringVar]] = [
            [tk.StringVar() for _ in range(9)] for _ in range(9)
        ]
        self._entries:        list[list[tk.Entry]] = [[None]*9 for _ in range(9)]
        self._is_fixed:       list[list[bool]]     = [[False]*9 for _ in range(9)]
        self._is_error:       list[list[bool]]     = [[False]*9 for _ in range(9)]
        self._is_solved_cell: list[list[bool]]     = [[False]*9 for _ in range(9)]
        self._is_correct:     list[list[bool]]     = [[False]*9 for _ in range(9)]
        # Solution grid — populated when a preset is loaded, used to validate entries
        self._solution_grid:  list[list[int]]      = [[0]*9 for _ in range(9)]

        # "play" or "auto"
        self._game_mode = "play"

        # Timer state
        self._timer_running    = False
        self._elapsed_seconds  = 0
        self._timer_job        = None

        # Mistake tracking
        self._mistakes         = 0
        self._counted_errors: set[tuple[int, int]] = set()

        # Pause state
        self._paused           = False

        # True once the player has chosen a mode and loaded a puzzle
        self._puzzle_loaded    = False

        # Save-file for resume
        self._save_path = os.path.join(os.path.dirname(__file__), "output", "resume.json")

        self._build_ui()

        for r in range(9):
            for c in range(9):
                self._vars[r][c].trace_add(
                    "write",
                    lambda *_, row=r, col=c: self._on_cell_changed(row, col),
                )

        # Don't auto-load — wait for the player to choose mode first
        self._status("Choose a mode to begin!", STATUS_INFO)

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self._outer = tk.Frame(self.root, bg=BG)
        self._outer.pack(padx=self.PAD, pady=self.PAD)

        # Title
        tk.Label(self._outer, text="Sudoku Solver", font=self.FONT_TITLE,
                 bg=BG, fg=BORDER_BOLD).pack(pady=(0, 10))

        # ── Mode toggle ─────────────────────────────────────────────────────
        toggle_row = tk.Frame(self._outer, bg=BG)
        toggle_row.pack(fill="x", pady=(0, 10))

        tk.Label(toggle_row, text="Mode:", font=self.FONT_LABEL,
                 bg=BG, fg=TEXT_USER).pack(side="left", padx=(0, 8))

        self._btn_play = tk.Button(
            toggle_row, text="🎮  Play yourself",
            command=lambda: self._set_game_mode("play"),
            font=("Segoe UI", 10, "bold"),
            bg=MODE_PLAY_BG, fg="white",
            activebackground=MODE_PLAY_HOV, activeforeground="white",
            relief="flat", padx=14, pady=6, cursor="hand2", bd=0,
        )
        self._btn_play.pack(side="left", padx=(0, 4))

        self._btn_auto = tk.Button(
            toggle_row, text="🤖  Auto-solve",
            command=lambda: self._set_game_mode("auto"),
            font=("Segoe UI", 10, "bold"),
            bg=MODE_INACT_BG, fg="#6b7280",
            activebackground=MODE_AUTO_HOV, activeforeground="white",
            relief="flat", padx=14, pady=6, cursor="hand2", bd=0,
        )
        self._btn_auto.pack(side="left")

        # ── Shared row: Difficulty + Load Preset | right side switches by mode ─
        shared_row = tk.Frame(self._outer, bg=BG)
        shared_row.pack(fill="x", pady=(0, 6))

        tk.Label(shared_row, text="Difficulty:", font=self.FONT_LABEL,
                 bg=BG, fg=TEXT_USER).pack(side="left")
        self._diff_var = tk.StringVar(value="easy")
        ttk.Combobox(
            shared_row, textvariable=self._diff_var,
            values=PuzzleFactory.available_difficulties(),
            width=9, state="readonly", font=self.FONT_LABEL,
        ).pack(side="left", padx=(4, 10))
        self._styled_btn(shared_row, "Load Preset",
                         lambda: self._load_preset(self._diff_var.get()),
                         BTN2_BG, BTN2_HOV).pack(side="left", padx=(0, 16))

        # Right side — Play: timer + mistakes + pause | Auto: solver dropdown
        self._timer_var = tk.StringVar(value="⏱  00:00")
        self._timer_label = tk.Label(shared_row, textvariable=self._timer_var,
                                     font=("Segoe UI", 11, "bold"), bg=BG, fg=TEXT_USER)
        self._mistake_var = tk.StringVar(value="❌  0 / 5")
        self._mistake_label = tk.Label(
            shared_row, textvariable=self._mistake_var,
            font=("Segoe UI", 11, "bold"), bg=BG, fg=TEXT_USER,
        )
        self._pause_btn = self._styled_btn(
            shared_row, "⏸  Pause", self._toggle_pause, "#4c1d95", "#3b0f78"
        )

        # Solver dropdown + Solve button (Auto mode)
        self._solver_var = tk.StringVar(value="Backtracking")
        self._solver_label = tk.Label(shared_row, text="Solver:", font=self.FONT_LABEL,
                                      bg=BG, fg=TEXT_USER)
        self._solver_combo = ttk.Combobox(
            shared_row, textvariable=self._solver_var,
            values=["Backtracking", "Constraint"],
            width=12, state="readonly", font=self.FONT_LABEL,
        )


        # ── Grid ────────────────────────────────────────────────────────────
        grid_frame = tk.Frame(self._outer, bg=BORDER_BOLD, padx=2, pady=2)
        grid_frame.pack(pady=8)
        self._build_grid(grid_frame)

        # ── Shared bottom row ────────────────────────────────────────────────
        bot = tk.Frame(self._outer, bg=BG)
        bot.pack(fill="x", pady=(4, 0))

        self._styled_btn(bot, "✖  Clear",
                         self._clear_user, "#b45309", "#92400e").pack(side="left", padx=3)
        self._styled_btn(bot, "💾 Save",
                         self._save, BTN2_BG, BTN2_HOV).pack(side="right", padx=3)
        self._load_csv_btn = self._styled_btn(bot, "📂 Load CSV",
                         self._load_csv, "#374151", "#1f2937")
        self._load_csv_btn.pack(side="right", padx=3)
        BTN_SOLVE_BG  = "#0e7490"
        BTN_SOLVE_HOV = "#0c6a82"
        self._solve_btn = self._styled_btn(
            bot, "✔  Solve puzzle", self._solve, BTN_SOLVE_BG, BTN_SOLVE_HOV,
        )

        # ── Status bar ───────────────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Choose a mode, load a puzzle, and play!")
        self._status_label = tk.Label(
            self._outer, textvariable=self._status_var,
            font=self.FONT_STATUS, bg=BG, fg=STATUS_INFO,
            wraplength=self.CELL * 9,
        )
        self._status_label.pack(pady=(10, 0))

        # Apply initial mode layout
        self._set_game_mode("play")

    def _build_grid(self, parent: tk.Frame) -> None:
        """Build the 9x9 grid with thick lines between 3x3 boxes and thin lines
        between individual cells inside each box.

        Level 1 — outer_grid (3x3 of box frames), bg=BORDER_BOLD, gap=3px (thick).
        Level 2 — each box frame (3x3 of cells), bg=BORDER_INNER, gap=1px (thin).
        """
        THICK = 3
        THIN  = 1

        outer_grid = tk.Frame(parent, bg=BORDER_BOLD)
        outer_grid.pack()

        for box_r in range(3):
            for box_c in range(3):
                pad_right  = 0 if box_c == 2 else THICK
                pad_bottom = 0 if box_r == 2 else THICK

                box_frame = tk.Frame(
                    outer_grid, bg=BORDER_INNER,
                    padx=THIN, pady=THIN,
                )
                box_frame.grid(
                    row=box_r, column=box_c,
                    padx=(0, pad_right), pady=(0, pad_bottom),
                )

                for cell_r in range(3):
                    for cell_c in range(3):
                        row = box_r * 3 + cell_r
                        col = box_c * 3 + cell_c

                        pad_r = 0 if cell_r == 2 else THIN
                        pad_c = 0 if cell_c == 2 else THIN

                        e = tk.Entry(
                            box_frame,
                            textvariable=self._vars[row][col],
                            width=2, font=self.FONT_DIGIT,
                            justify="center",
                            bg=GRID_BG, fg=TEXT_USER,
                            insertbackground=TEXT_USER,
                            relief="flat", bd=0, highlightthickness=0,
                        )
                        e.configure(
                            validate="key",
                            validatecommand=(
                                e.register(self._validate_key), "%P", row, col
                            ),
                        )
                        e.grid(
                            row=cell_r, column=cell_c,
                            padx=(0, pad_c), pady=(0, pad_r),
                            ipadx=4, ipady=6,
                        )
                        e.bind("<FocusIn>",
                               lambda ev, r=row, c=col: self._on_focus(r, c))
                        e.bind("<FocusOut>",
                               lambda ev, r=row, c=col: self._on_blur(r, c))
                        self._entries[row][col] = e

    @staticmethod
    def _styled_btn(parent, text, cmd, bg, hover_bg) -> tk.Button:
        btn = tk.Button(
            parent, text=text, command=cmd,
            font=("Segoe UI", 10, "bold"),
            bg=bg, fg="white",
            activebackground=hover_bg, activeforeground="white",
            relief="flat", padx=12, pady=6, cursor="hand2", bd=0,
        )
        btn.bind("<Enter>", lambda _: btn.configure(bg=hover_bg))
        btn.bind("<Leave>", lambda _: btn.configure(bg=bg))
        return btn

    # ── Game mode switching ───────────────────────────────────────────────────

    def _set_game_mode(self, mode: str) -> None:
        """Switch between Play and Auto-solve modes."""
        prev_mode       = self._game_mode
        self._game_mode = mode

        play_widgets = [self._mistake_label, self._timer_label]
        auto_widgets = [self._solver_combo, self._solver_label]

        if mode == "play":
            self._btn_play.configure(bg=MODE_PLAY_BG, fg="white")
            self._btn_auto.configure(bg=MODE_INACT_BG, fg="#6b7280")

            for w in auto_widgets:
                w.pack_forget()
            self._solve_btn.pack_forget()
            self._pause_btn.pack(side="right", padx=(8, 0))
            self._mistake_label.pack(side="right", padx=(4, 0))
            self._timer_label.pack(side="right", padx=(0, 8))

            self._clear_all_errors()
            if self._puzzle_loaded:
                # Switching back from auto — keep current progress, reset timer
                self._reset_play_stats()
            self._paused = False
            self._status(
                "Play mode — load a puzzle and fill in the grid yourself."
                if not self._puzzle_loaded
                else "Play mode — fill in the grid yourself.",
                STATUS_INFO,
            )

        else:
            self._btn_auto.configure(bg=MODE_AUTO_BG, fg="white")
            self._btn_play.configure(bg=MODE_INACT_BG, fg="#6b7280")

            for w in play_widgets:
                w.pack_forget()
            self._pause_btn.pack_forget()
            self._solver_combo.pack(side="right", padx=(4, 4))
            self._solver_label.pack(side="right", padx=(8, 0))
            self._solve_btn.pack(side="left", padx=3)

            self._stop_timer()
            self._paused = False
            self._clear_all_errors()
            self._status(
                "Auto-solve mode — load a puzzle, then press Solve."
                if not self._puzzle_loaded
                else "Auto-solve mode — press Solve to let the computer solve it.",
                STATUS_INFO,
            )

    # ── Timer ─────────────────────────────────────────────────────────────────

    def _start_timer(self) -> None:
        """Start the elapsed-time counter (no-op if already running or paused)."""
        if not self._timer_running and self._puzzle_loaded and not self._paused:
            self._timer_running = True
            self._tick()

    def _stop_timer(self) -> None:
        """Stop the timer and cancel any pending tick."""
        self._timer_running = False
        if self._timer_job:
            self.root.after_cancel(self._timer_job)
            self._timer_job = None

    def _tick(self) -> None:
        """Increment elapsed seconds and update the display every second."""
        if not self._timer_running:
            return
        self._elapsed_seconds += 1
        mins, secs = divmod(self._elapsed_seconds, 60)
        self._timer_var.set(f"⏱  {mins:02d}:{secs:02d}")
        self._timer_job = self.root.after(1000, self._tick)

    def _reset_play_stats(self) -> None:
        """Reset timer and mistake counter for a fresh game."""
        self._stop_timer()
        self._elapsed_seconds = 0
        self._timer_var.set("⏱  00:00")
        self._mistakes = 0
        self._counted_errors = set()
        self._mistake_var.set(f"❌  0 / {self.MAX_MISTAKES}")
        self._mistake_label.configure(fg=TEXT_USER)

    def _toggle_pause(self) -> None:
        """Pause or resume the timer and hide/show the grid."""
        if not self._puzzle_loaded or self._game_mode != "play":
            return
        self._paused = not self._paused
        if self._paused:
            self._stop_timer()
            self._pause_btn.configure(text="▶  Resume")
            # Dim every non-fixed cell so the grid is unreadable while paused
            for r in range(9):
                for c in range(9):
                    if not self._is_fixed[r][c]:
                        self._entries[r][c].configure(state="disabled",
                            disabledbackground=BG, disabledforeground=BG)
            self._status("⏸  Game paused — press Resume to continue.", STATUS_INFO)
        else:
            self._pause_btn.configure(text="⏸  Pause")
            # Restore cells
            for r in range(9):
                for c in range(9):
                    if self._is_fixed[r][c] or self._is_solved_cell[r][c]:
                        continue
                    if self._is_correct[r][c]:
                        self._entries[r][c].configure(state="disabled",
                            disabledbackground=CORRECT_BG, disabledforeground=CORRECT_FG)
                    elif self._is_error[r][c]:
                        self._entries[r][c].configure(state="normal",
                            bg=ERR_BG, fg=ERR_FG)
                    else:
                        self._entries[r][c].configure(state="normal",
                            bg=GRID_BG, fg=TEXT_USER)
            self._start_timer()
            self._status("▶  Resumed — good luck!", STATUS_INFO)

    # ── Mistake tracking ───────────────────────────────────────────────────────

    def _register_mistake(self, row: int, col: int) -> None:
        """Count a new mistake for (row, col) if not already counted.

        Starts the timer on the first entry. Locks the board and shows a
        game-over message when the mistake limit is reached.
        """
        if (row, col) in self._counted_errors:
            return
        self._counted_errors.add((row, col))
        self._mistakes += 1

        colour = STATUS_ERR if self._mistakes >= self.MAX_MISTAKES else "#f59e0b"
        self._mistake_var.set(f"❌  {self._mistakes} / {self.MAX_MISTAKES}")
        self._mistake_label.configure(fg=colour)

        if self._mistakes >= self.MAX_MISTAKES:
            self._stop_timer()
            self._lock_board()
            self._show_game_over()

    def _lock_board(self) -> None:
        """Disable all non-fixed cells after game-over.

        Correct cells keep their blue style.
        Empty / wrong cells are shown with the dark-red error style so the
        player can see which spots were never filled correctly before
        switching to Auto-solve.
        """
        for r in range(9):
            for c in range(9):
                if self._is_fixed[r][c] or self._is_solved_cell[r][c]:
                    continue
                if self._is_correct[r][c]:
                    # Already disabled with blue style — leave it
                    pass
                else:
                    self._entries[r][c].configure(
                        state="disabled",
                        disabledbackground=ERR_BG,
                        disabledforeground=ERR_FG,
                    )

    # ── Error detection ───────────────────────────────────────────────────────

    def _get_int(self, row: int, col: int) -> int:
        v = self._vars[row][col].get()
        return int(v) if v.isdigit() else 0

    def _has_conflict(self, row: int, col: int, val: int) -> bool:
        """Return True if val at (row, col) conflicts with any other filled cell
        in the same row, column, or 3x3 box.
        """
        if val == 0:
            return False
        for c in range(9):
            if c != col and self._get_int(row, c) == val:
                return True
        for r in range(9):
            if r != row and self._get_int(r, col) == val:
                return True
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                if (r, c) != (row, col) and self._get_int(r, c) == val:
                    return True
        return False

    def _on_cell_changed(self, row: int, col: int) -> None:
        """StringVar trace — fires on every keystroke."""
        if self._is_fixed[row][col] or self._is_solved_cell[row][col]:
            return
        if self._paused:
            return
        if self._is_correct[row][col]:
            sol = self._solution_grid[row][col]
            self._vars[row][col].set(str(sol))
            return
        if self._game_mode == "play":
            val = self._get_int(row, col)
            if val == 0:
                return
            correct_val = self._solution_grid[row][col] if self._solution_grid else 0
            if correct_val and val == correct_val:
                # ── Correct entry ──────────────────────────────────────────
                self._is_correct[row][col] = True
                self._is_error[row][col]   = False
                self._counted_errors.discard((row, col))
                e = self._entries[row][col]
                e.configure(
                    bg=CORRECT_BG, fg=CORRECT_FG,
                    state="disabled",
                    disabledbackground=CORRECT_BG,
                    disabledforeground=CORRECT_FG,
                )
                self._recheck_neighbours(row, col)
                self._autosave()
                self._check_victory()
            else:
                # ── Wrong entry ────────────────────────────────────────────
                self._register_mistake(row, col)
                self._is_error[row][col] = True
                self._apply_cell_style(row, col)
                self._autosave()

    def _check_cell(self, row: int, col: int) -> None:
        if self._is_correct[row][col]:
            return  # Correct cells never become errors
        val = self._get_int(row, col)
        self._is_error[row][col] = self._has_conflict(row, col, val)
        self._apply_cell_style(row, col)

    def _recheck_neighbours(self, row: int, col: int) -> None:
        """Re-evaluate all cells sharing a row, column, or box with (row, col).
        Fixing one digit may resolve errors in neighbouring cells.
        """
        cells: set[tuple[int, int]] = set()
        for i in range(9):
            cells.add((row, i))
            cells.add((i, col))
        br, bc = 3 * (row // 3), 3 * (col // 3)
        for r in range(br, br + 3):
            for c in range(bc, bc + 3):
                cells.add((r, c))
        cells.discard((row, col))
        for r, c in cells:
            if not self._is_fixed[r][c] and not self._is_solved_cell[r][c]:
                self._check_cell(r, c)

    def _check_all(self, silent: bool = False) -> None:
        """Highlight all conflicting cells. Called by Check button or mode switch."""
        error_count = 0
        for r in range(9):
            for c in range(9):
                if not self._is_fixed[r][c] and not self._is_solved_cell[r][c]:
                    self._check_cell(r, c)
                    if self._is_error[r][c]:
                        error_count += 1
        if not silent:
            if error_count == 0:
                self._status("✔ No errors found!", STATUS_OK)
            else:
                noun = "conflict" if error_count == 1 else "conflicts"
                self._status(
                    f"✖ {error_count} {noun} found — highlighted in red.",
                    STATUS_ERR,
                )

    def _clear_all_errors(self) -> None:
        for r in range(9):
            for c in range(9):
                self._is_error[r][c] = False
                if not self._is_fixed[r][c] and not self._is_solved_cell[r][c]:
                    self._apply_cell_style(r, c)

    # ── Cell styling ──────────────────────────────────────────────────────────

    def _apply_cell_style(self, row: int, col: int) -> None:
        e = self._entries[row][col]
        if self._is_fixed[row][col] or self._is_solved_cell[row][col]:
            return
        if self._is_correct[row][col]:
            e.configure(bg=CORRECT_BG, fg=CORRECT_FG)
            return
        e.configure(
            bg=ERR_BG if self._is_error[row][col] else GRID_BG,
            fg=ERR_FG if self._is_error[row][col] else TEXT_USER,
        )

    def _on_focus(self, row: int, col: int) -> None:
        if self._is_fixed[row][col] or self._is_solved_cell[row][col]:
            return
        if self._is_error[row][col] and self._game_mode == "play":
            # Clear the wrong digit so the player can type a fresh guess
            self._vars[row][col].set("")
            self._is_error[row][col] = False
            self._counted_errors.discard((row, col))
            self._entries[row][col].configure(bg=FOCUS_BG, fg=TEXT_USER)
            self._recheck_neighbours(row, col)
        else:
            self._entries[row][col].configure(
                bg=ERR_FOCUS if self._is_error[row][col] else FOCUS_BG
            )

    def _on_blur(self, row: int, col: int) -> None:
        if self._is_fixed[row][col] or self._is_solved_cell[row][col]:
            return
        self._apply_cell_style(row, col)

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_key(self, new_val: str, row: int, col: int) -> bool:
        """Allow only a single digit 1-9 (or empty) in each cell."""
        if self._is_fixed[row][col]:
            return False
        return new_val == "" or (len(new_val) == 1 and new_val in "123456789")

    # ── Grid helpers ──────────────────────────────────────────────────────────

    def _read_grid_from_entries(self) -> list[list[int]]:
        return [[self._get_int(r, c) for c in range(9)] for r in range(9)]

    def _write_grid_to_entries(
        self,
        grid: list[list[int]],
        fixed: list[list[bool]],
        solved: bool = False,
    ) -> None:
        """Push a grid into the Entry widgets and apply correct styling.

        Args:
            grid:   9x9 integer grid to display.
            fixed:  9x9 bool grid; True means the cell is a puzzle clue.
            solved: If True, newly filled cells are styled as solved (green).
        """
        for r in range(9):
            for c in range(9):
                val = grid[r][c]
                self._vars[r][c].set(str(val) if val else "")
                self._is_fixed[r][c]       = fixed[r][c]
                self._is_error[r][c]       = False
                self._is_solved_cell[r][c] = solved and not fixed[r][c]

                e = self._entries[r][c]
                if solved and not fixed[r][c]:
                    e.configure(
                        bg=SOLVED_BG, fg=TEXT_SOLVED, state="disabled",
                        disabledforeground=TEXT_SOLVED,
                        disabledbackground=SOLVED_BG,
                    )
                elif fixed[r][c]:
                    e.configure(
                        bg=FIXED_BG, fg=TEXT_FIXED, state="disabled",
                        disabledforeground=TEXT_FIXED,
                        disabledbackground=FIXED_BG,
                    )
                else:
                    e.configure(bg=GRID_BG, fg=TEXT_USER, state="normal")

    # ── Actions ───────────────────────────────────────────────────────────────

    def _load_preset(self, difficulty: str) -> None:
        try:
            board = PuzzleFactory.create(difficulty)
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return
        grid  = board.get_grid()
        fixed = [[grid[r][c] != 0 for c in range(9)] for r in range(9)]
        self._original_grid = copy.deepcopy(grid)
        self._board = board
        sol_board = SudokuBoard(copy.deepcopy(grid))
        BacktrackingSolver(sol_board).solve()
        self._solution_grid = sol_board.get_grid()
        self._is_correct    = [[False]*9 for _ in range(9)]
        self._puzzle_loaded = True
        self._paused        = False
        self._write_grid_to_entries(grid, fixed)
        if self._game_mode == "play":
            self._reset_play_stats()
            self._start_timer()
        hint = ("fill in the grid yourself"
                if self._game_mode == "play"
                else "press Solve to let the computer solve it")
        self._status(f"Loaded '{difficulty}' puzzle — {hint}.", STATUS_INFO)
        self._autosave()

    def _solve(self) -> None:
        """Read the grid, run the selected solver, and update the display.

        Uses Polymorphism — BacktrackingSolver or ConstraintSolver are both
        called through the shared BaseSolver.solve() interface.
        """
        self._clear_all_errors()
        grid  = self._read_grid_from_entries()
        fixed = [[grid[r][c] != 0 for c in range(9)] for r in range(9)]
        board = SudokuBoard(grid)

        name   = self._solver_var.get()
        solver = (BacktrackingSolver(board)
                  if name == "Backtracking" else ConstraintSolver(board))

        self._status("Solving…", STATUS_INFO)
        self.root.update_idletasks()
        success = solver.solve()

        if success:
            self._board = board
            self._original_grid = copy.deepcopy(grid)
            self._write_grid_to_entries(board.get_grid(), fixed, solved=True)
            if self._game_mode == "play":
                self._stop_timer()
            self._status(
                f"✔ Solved in {solver.steps} steps using {name}Solver!",
                STATUS_OK,
            )
        else:
            self._status("✖ No solution exists for this puzzle.", STATUS_ERR)
            messagebox.showerror("No Solution", "This puzzle has no solution.")

    def _clear_user(self) -> None:
        for r in range(9):
            for c in range(9):
                if not self._is_fixed[r][c]:
                    self._vars[r][c].set("")
                    self._is_error[r][c]       = False
                    self._is_solved_cell[r][c] = False
                    self._is_correct[r][c]     = False
                    self._entries[r][c].configure(
                        bg=GRID_BG, fg=TEXT_USER, state="normal"
                    )
        if self._game_mode == "play":
            self._reset_play_stats()
        # Remove autosave so Resume doesn't restore the cleared state
        try:
            if os.path.exists(self._save_path):
                os.remove(self._save_path)
        except OSError:
            pass
        self._status("Board cleared.", STATUS_INFO)

    def _save(self) -> None:
        """Save puzzle + player progress + solution to CSV."""
        if self._board is None:
            self._status("No puzzle loaded to save.", STATUS_ERR)
            return
        player_grid = [[self._get_int(r, c) for c in range(9)] for r in range(9)]
        path = self._file_manager.save_result(
            puzzle=self._original_grid,
            solution=self._solution_grid if self._solution_grid else self._board.get_grid(),
            solver_name=self._solver_var.get() + "Solver",
            steps=0,
            player_grid=player_grid,
            is_correct=self._is_correct,
            is_error=self._is_error,
            elapsed_seconds=self._elapsed_seconds,
            mistakes=self._mistakes,
        )
        self._status(f"💾 Saved to {os.path.basename(path)}", STATUS_OK)

    def _load_csv(self) -> None:
        """Open a file picker and load a saved session or plain puzzle CSV."""
        path = filedialog.askopenfilename(
            title="Open puzzle CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        # Try loading as a full saved session first
        try:
            session = self._file_manager.load_session(path)
        except (FileNotFoundError, ValueError):
            session = None

        if session:
            grid  = session["puzzle"]
            fixed = [[grid[r][c] != 0 for c in range(9)] for r in range(9)]
            self._original_grid  = copy.deepcopy(grid)
            self._solution_grid  = session["solution"]
            self._is_correct     = session["is_correct"]
            self._is_error       = session["is_error"]
            self._board          = SudokuBoard(copy.deepcopy(grid))
            self._puzzle_loaded  = True
            self._paused         = False

            # Write original clues
            self._write_grid_to_entries(grid, fixed)

            # Restore player entries with correct styling
            pg = session["player"]
            for r in range(9):
                for c in range(9):
                    if fixed[r][c]:
                        continue
                    val = pg[r][c]
                    if self._is_correct[r][c] and val:
                        self._vars[r][c].set(str(val))
                        e = self._entries[r][c]
                        e.configure(state="disabled",
                                    disabledbackground=CORRECT_BG,
                                    disabledforeground=CORRECT_FG)
                    elif self._is_error[r][c] and val:
                        self._vars[r][c].set(str(val))
                        self._entries[r][c].configure(
                            state="normal", bg=ERR_BG, fg=ERR_FG)

            # Restore timer and mistakes
            self._elapsed_seconds = session["elapsed_seconds"]
            self._mistakes        = session["mistakes"]
            mins, secs = divmod(self._elapsed_seconds, 60)
            self._timer_var.set(f"⏱  {mins:02d}:{secs:02d}")
            self._mistake_var.set(f"❌  {self._mistakes} / {self.MAX_MISTAKES}")
            colour = (STATUS_ERR if self._mistakes >= self.MAX_MISTAKES
                      else "#f59e0b" if self._mistakes > 0 else TEXT_USER)
            self._mistake_label.configure(fg=colour)

            if self._game_mode != "play":
                self._set_game_mode("play")
            else:
                # Re-pack play widgets if already in play mode
                self._mistake_label.pack(side="right", padx=(4, 0))
                self._timer_label.pack(side="right", padx=(0, 8))

            if self._mistakes < self.MAX_MISTAKES:
                self._start_timer()

            self._status(
                f"▶  Session restored — {self._mistakes} mistake(s), "
                f"time {mins:02d}:{secs:02d}.", STATUS_OK
            )
        else:
            # Fall back to plain puzzle load
            try:
                grid = self._file_manager.load_puzzle(path)
            except (FileNotFoundError, ValueError) as exc:
                messagebox.showerror("Load error", str(exc))
                return
            fixed = [[grid[r][c] != 0 for c in range(9)] for r in range(9)]
            self._original_grid = copy.deepcopy(grid)
            self._board         = SudokuBoard(copy.deepcopy(grid))
            self._puzzle_loaded = True
            sol_board = SudokuBoard(copy.deepcopy(grid))
            BacktrackingSolver(sol_board).solve()
            self._solution_grid = sol_board.get_grid()
            self._is_correct    = [[False]*9 for _ in range(9)]
            self._is_error      = [[False]*9 for _ in range(9)]
            self._write_grid_to_entries(grid, fixed)
            if self._game_mode == "play":
                self._reset_play_stats()
                self._start_timer()
            self._status(f"Loaded puzzle from {os.path.basename(path)}.", STATUS_INFO)

    # ── Victory ───────────────────────────────────────────────────────────────

    def _check_victory(self) -> None:
        """Check if all non-fixed cells are correctly filled."""
        for r in range(9):
            for c in range(9):
                if not self._is_fixed[r][c] and not self._is_correct[r][c]:
                    return  # Still empty or wrong cells
        self._show_victory()

    def _show_victory(self) -> None:
        """Show a congratulations dialog with time and mistake stats."""
        self._stop_timer()
        mins, secs = divmod(self._elapsed_seconds, 60)
        time_str   = f"{mins:02d}:{secs:02d}"
        mistakes   = self._mistakes
        # Clear the autosave — game is over
        try:
            if os.path.exists(self._save_path):
                os.remove(self._save_path)
        except OSError:
            pass

        win = tk.Toplevel(self.root)
        win.title("Puzzle Complete!")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="🎉", font=("Segoe UI", 48), bg=BG).pack(pady=(24, 4))
        tk.Label(win, text="Puzzle Complete!", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg=STATUS_OK).pack()
        tk.Label(win, text=f"Time:  {time_str}", font=("Segoe UI", 13),
                 bg=BG, fg=TEXT_USER).pack(pady=(12, 2))
        rating = "Perfect! 🏆" if mistakes == 0 else f"{mistakes} mistake{'s' if mistakes != 1 else ''}"
        tk.Label(win, text=f"Mistakes:  {rating}", font=("Segoe UI", 13),
                 bg=BG, fg=STATUS_OK if mistakes == 0 else "#f59e0b").pack(pady=(2, 16))

        self._styled_btn(win, "Close", win.destroy, BTN2_BG, BTN2_HOV).pack(pady=(0, 20))
        self._status(f"🎉 Puzzle complete! Time: {time_str} | Mistakes: {mistakes}", STATUS_OK)

    def _show_game_over(self) -> None:
        """Show a game-over dialog when the player reaches 5 mistakes."""
        mins, secs = divmod(self._elapsed_seconds, 60)
        time_str   = f"{mins:02d}:{secs:02d}"

        win = tk.Toplevel(self.root)
        win.title("Game Over")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.grab_set()

        tk.Label(win, text="💀", font=("Segoe UI", 48), bg=BG).pack(pady=(24, 4))
        tk.Label(win, text="Game Over!", font=("Segoe UI", 20, "bold"),
                 bg=BG, fg=STATUS_ERR).pack()
        tk.Label(win, text="You made 5 mistakes.", font=("Segoe UI", 13),
                 bg=BG, fg="#f87171").pack(pady=(12, 2))
        tk.Label(win, text=f"Time survived:  {time_str}",
                 font=("Segoe UI", 13), bg=BG, fg=TEXT_USER).pack(pady=(2, 16))
        tk.Label(win, text="Switch to Auto-solve to see the solution.",
                 font=("Segoe UI", 11), bg=BG, fg="#6b7280").pack(pady=(0, 12))

        self._styled_btn(win, "Close", win.destroy, "#7f1d1d", "#991b1b").pack(pady=(0, 20))
        self._status("💀 Game over — 5 mistakes! Switch to Auto-solve to see the solution.", STATUS_ERR)

    # ── Save / Resume ─────────────────────────────────────────────────────────

    def _autosave(self) -> None:
        """Persist current play state to output/resume.json."""
        if not self._puzzle_loaded or self._game_mode != "play":
            return
        try:
            os.makedirs(os.path.dirname(self._save_path), exist_ok=True)
            state = {
                "original_grid":  self._original_grid,
                "solution_grid":  self._solution_grid,
                "current_grid":   [[self._get_int(r, c) for c in range(9)] for r in range(9)],
                "is_correct":     self._is_correct,
                "is_error":       self._is_error,
                "elapsed_seconds": self._elapsed_seconds,
                "mistakes":       self._mistakes,
                "difficulty":     self._diff_var.get(),
            }
            with open(self._save_path, "w") as f:
                json.dump(state, f)
        except OSError:
            pass

    def _resume_saved(self) -> None:
        """Load a previously saved game from output/resume.json, if it exists."""
        if not os.path.exists(self._save_path):
            self._status("No saved game found.", STATUS_ERR)
            return
        try:
            with open(self._save_path) as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError):
            self._status("Could not load saved game.", STATUS_ERR)
            return

        grid     = state["original_grid"]
        fixed    = [[grid[r][c] != 0 for c in range(9)] for r in range(9)]
        self._original_grid   = grid
        self._solution_grid   = state["solution_grid"]
        self._is_correct      = state["is_correct"]
        self._is_error        = state["is_error"]
        self._puzzle_loaded   = True
        self._paused          = False
        self._diff_var.set(state.get("difficulty", "easy"))

        # Write original clues first
        self._write_grid_to_entries(grid, fixed)

        # Restore player progress
        cur = state["current_grid"]
        for r in range(9):
            for c in range(9):
                if fixed[r][c]:
                    continue
                val = cur[r][c]
                if self._is_correct[r][c] and val:
                    self._vars[r][c].set(str(val))
                    e = self._entries[r][c]
                    e.configure(state="disabled",
                                disabledbackground=CORRECT_BG,
                                disabledforeground=CORRECT_FG)
                elif self._is_error[r][c] and val:
                    self._vars[r][c].set(str(val))
                    self._entries[r][c].configure(bg=ERR_BG, fg=ERR_FG, state="normal")

        # Restore timer and mistakes (don't start ticking yet)
        self._elapsed_seconds = state.get("elapsed_seconds", 0)
        mins, secs = divmod(self._elapsed_seconds, 60)
        self._timer_var.set(f"⏱  {mins:02d}:{secs:02d}")
        self._mistakes = state.get("mistakes", 0)
        self._mistake_var.set(f"❌  {self._mistakes} / {self.MAX_MISTAKES}")
        colour = STATUS_ERR if self._mistakes >= self.MAX_MISTAKES else (
            "#f59e0b" if self._mistakes > 0 else TEXT_USER)
        self._mistake_label.configure(fg=colour)

        if self._game_mode != "play":
            self._set_game_mode("play")

        self._status(
            f"▶  Resumed — {self._mistakes} mistake(s), time {mins:02d}:{secs:02d}. "
            "Start typing to resume the timer.", STATUS_OK
        )

    # ── Status bar ────────────────────────────────────────────────────────────

    def _status(self, msg: str, colour: str = STATUS_INFO) -> None:
        self._status_var.set(msg)
        self._status_label.configure(fg=colour)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    root = tk.Tk()
    try:
        root.iconbitmap("icon.ico")
    except Exception:
        pass
    SudokuGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
