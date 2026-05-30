"""
app.py - Data Quality & ETL Validator
Main entry point: builds and runs the CustomTkinter desktop GUI.

Layout
------
┌──────────────────────────────────────────────────────┐
│  Header / Title bar                                  │
├──────────────────────────────────────────────────────┤
│  [Browse CSV]  path label          [Run Validation]  │
├──────────────────────────────────────────────────────┤
│  Progress bar (hidden until validation starts)       │
├──────────────────────────────────────────────────────┤
│  Results text area (scrollable)                      │
├──────────────────────────────────────────────────────┤
│  Status bar                                          │
└──────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.logger import setup_logger
from src.report_generator import ReportGenerator
from src.validator import DataValidator

# ── Appearance ────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

logger = setup_logger()

# Project root (one level up from this file)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")


class ETLValidatorApp(ctk.CTk):
    """
    Main application window for the Data Quality & ETL Validator.

    Responsibilities:
    - Render all UI widgets.
    - Coordinate file selection, validation, and report generation.
    - Run validation in a background thread so the GUI stays responsive.
    """

    # ── Window constants ──────────────────────────────────────────────────────
    WINDOW_TITLE = "Data Quality & ETL Validator"
    WINDOW_WIDTH = 960
    WINDOW_HEIGHT = 720
    MIN_WIDTH = 720
    MIN_HEIGHT = 540

    def __init__(self) -> None:
        super().__init__()
        self._csv_path: str = ""
        self._setup_window()
        self._build_ui()
        logger.info("Application window created.")

    # ──────────────────────────────────────────────────────────────────────────
    # Window setup
    # ──────────────────────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        """Configure the root window."""
        self.title(self.WINDOW_TITLE)
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)

        # Center the window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() - self.WINDOW_WIDTH) // 2
        y = (self.winfo_screenheight() - self.WINDOW_HEIGHT) // 2
        self.geometry(f"+{x}+{y}")

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Assemble all UI sections."""
        self._build_header()
        self._build_file_row()
        self._build_progress()
        self._build_results_area()
        self._build_status_bar()

    def _build_header(self) -> None:
        """Top banner with title and subtitle."""
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#1a1a2e", "#0f0f1e"))
        header_frame.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            header_frame,
            text="⚡  Data Quality & ETL Validator",
            font=ctk.CTkFont(family="Courier New", size=22, weight="bold"),
            text_color=("#4fc3f7", "#4fc3f7"),
        ).pack(side="left", padx=24, pady=16)

        ctk.CTkLabel(
            header_frame,
            text="Powered by Pandas · CustomTkinter",
            font=ctk.CTkFont(size=11),
            text_color="gray",
        ).pack(side="right", padx=24, pady=16)

    def _build_file_row(self) -> None:
        """Row containing Browse button, file path label, and Run button."""
        row = ctk.CTkFrame(self, corner_radius=10)
        row.pack(fill="x", padx=16, pady=(12, 4))

        # Browse button
        self._browse_btn = ctk.CTkButton(
            row,
            text="📂  Browse CSV",
            width=140,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._browse_file,
        )
        self._browse_btn.pack(side="left", padx=(12, 8), pady=10)

        # File path display
        self._path_var = tk.StringVar(value="No file selected …")
        path_label = ctk.CTkEntry(
            row,
            textvariable=self._path_var,
            state="readonly",
            font=ctk.CTkFont(size=12),
            height=38,
        )
        path_label.pack(side="left", fill="x", expand=True, padx=8, pady=10)

        # Run Validation button
        self._run_btn = ctk.CTkButton(
            row,
            text="▶  Run Validation",
            width=160,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=("#2e7d32", "#2e7d32"),
            hover_color=("#1b5e20", "#1b5e20"),
            command=self._start_validation,
            state="disabled",
        )
        self._run_btn.pack(side="right", padx=(8, 12), pady=10)

        # Clear button
        ctk.CTkButton(
            row,
            text="🗑  Clear",
            width=90,
            height=38,
            font=ctk.CTkFont(size=12),
            fg_color=("gray40", "gray25"),
            hover_color=("gray30", "gray20"),
            command=self._clear_results,
        ).pack(side="right", padx=(0, 4), pady=10)

    def _build_progress(self) -> None:
        """Indeterminate progress bar shown during validation."""
        self._progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._progress_frame.pack(fill="x", padx=16, pady=2)

        self._progress = ctk.CTkProgressBar(self._progress_frame, mode="indeterminate")
        self._progress.pack(fill="x", padx=4)
        self._progress_frame.pack_forget()  # hidden until needed

    def _build_results_area(self) -> None:
        """Scrollable text area for displaying validation results."""
        results_frame = ctk.CTkFrame(self, corner_radius=10)
        results_frame.pack(fill="both", expand=True, padx=16, pady=8)

        ctk.CTkLabel(
            results_frame,
            text="Validation Results",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 4))

        self._results_text = ctk.CTkTextbox(
            results_frame,
            font=ctk.CTkFont(family="Courier New", size=12),
            wrap="none",
            corner_radius=6,
        )
        self._results_text.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._results_text.configure(state="disabled")

        self._display_welcome()

    def _build_status_bar(self) -> None:
        """Bottom status bar."""
        bar = ctk.CTkFrame(self, corner_radius=0, height=28, fg_color=("gray85", "gray18"))
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self._status_var = tk.StringVar(value="Ready — select a CSV file to begin.")
        ctk.CTkLabel(
            bar,
            textvariable=self._status_var,
            font=ctk.CTkFont(size=11),
            anchor="w",
        ).pack(side="left", padx=12)

    # ──────────────────────────────────────────────────────────────────────────
    # Event handlers
    # ──────────────────────────────────────────────────────────────────────────

    def _browse_file(self) -> None:
        """Open a file-chooser dialog and store the chosen CSV path."""
        path = filedialog.askopenfilename(
            title="Select a CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return

        self._csv_path = path
        self._path_var.set(path)
        self._run_btn.configure(state="normal")
        self._set_status(f"File selected: {os.path.basename(path)}")
        logger.info("File selected: %s", path)

    def _start_validation(self) -> None:
        """Kick off validation in a daemon thread to keep the GUI responsive."""
        if not self._csv_path:
            messagebox.showwarning("No File", "Please select a CSV file first.")
            return

        logger.info("Validation started for: %s", self._csv_path)
        self._toggle_controls(running=True)
        self._clear_results(keep_message="⏳  Running validation …\n")

        thread = threading.Thread(target=self._run_validation, daemon=True)
        thread.start()

    def _run_validation(self) -> None:
        """
        Validation worker (runs in background thread).
        Posts results back to the GUI via after().
        """
        try:
            # ── Validate ──────────────────────────────────────────────────────
            self._set_status("Validating data …")
            validator = DataValidator(self._csv_path)
            result = validator.validate()

            # ── Generate reports ──────────────────────────────────────────────
            self._set_status("Generating reports …")
            gen = ReportGenerator(OUTPUT_DIR)
            txt_path, csv_path = gen.generate(result)

            # ── Build display text ────────────────────────────────────────────
            display = self._format_result(result, txt_path, csv_path)

        except Exception as exc:  # noqa: BLE001
            logger.error("Unhandled error during validation: %s", exc, exc_info=True)
            display = f"❌  Error:\n{exc}"
            txt_path = csv_path = ""

        # Schedule GUI update on the main thread
        self.after(0, self._on_validation_done, display)

    def _on_validation_done(self, display: str) -> None:
        """Called on the main thread when the background worker finishes."""
        self._toggle_controls(running=False)
        self._append_text(display)
        self._set_status("Validation complete — reports saved to output/")

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _format_result(self, result, txt_path: str, csv_path: str) -> str:
        """Format ValidationResult into a readable string for the text area."""
        sep = "─" * 56
        lines = [
            f"{'='*56}",
            "  DATA QUALITY & ETL VALIDATION — SUMMARY",
            f"{'='*56}",
            f"  File    : {os.path.basename(result.file_path)}",
            f"  Status  : {'✅ SUCCESS' if result.success else '❌ FAILED'}",
            "",
            f"  {sep}",
            "  DATASET OVERVIEW",
            f"  {sep}",
            f"  Total Rows       : {result.total_rows:,}",
            f"  Total Columns    : {result.total_columns:,}",
            f"  Total Missing    : {result.total_missing:,}",
            f"  Duplicate Rows   : {result.duplicate_rows:,}",
            "",
            f"  {sep}",
            "  COLUMNS & DATA TYPES",
            f"  {sep}",
        ]

        for col in result.column_names:
            lines.append(f"  {'  ' + col:<37} {result.dtypes.get(col, '?')}")

        lines += [
            "",
            f"  {sep}",
            "  MISSING VALUES",
            f"  {sep}",
        ]
        any_missing = False
        for col, cnt in result.missing_per_col.items():
            if cnt > 0:
                any_missing = True
                pct = result.missing_pct.get(col, 0.0)
                lines.append(f"  {'  ' + col:<37} {cnt:>6,}  ({pct:.2f}%)")
        if not any_missing:
            lines.append("  ✅  No missing values detected.")

        if result.numeric_stats:
            lines += [
                "",
                f"  {sep}",
                "  NUMERIC STATISTICS",
                f"  {sep}",
            ]
            for col, stats in result.numeric_stats.items():
                lines.append(f"\n  ▸ {col}")
                for stat, val in stats.items():
                    lines.append(f"      {stat:<12}: {val}")

        if result.errors:
            lines += ["", f"  {sep}", "  ERRORS", f"  {sep}"]
            for err in result.errors:
                lines.append(f"  ✗  {err}")

        lines += [
            "",
            f"  {sep}",
            "  REPORTS SAVED",
            f"  {sep}",
            f"  TXT : {txt_path}",
            f"  CSV : {csv_path}",
            f"{'='*56}",
            "",
        ]
        return "\n".join(lines)

    def _toggle_controls(self, running: bool) -> None:
        """Enable/disable controls and show/hide the progress bar."""
        state = "disabled" if running else "normal"
        self._browse_btn.configure(state=state)
        self._run_btn.configure(state=state)

        if running:
            self._progress_frame.pack(fill="x", padx=16, pady=2)
            self._progress.start()
        else:
            self._progress.stop()
            self._progress_frame.pack_forget()

    def _clear_results(self, keep_message: str = "") -> None:
        """Clear the results text area, optionally showing a placeholder."""
        self._results_text.configure(state="normal")
        self._results_text.delete("0.0", "end")
        if keep_message:
            self._results_text.insert("0.0", keep_message)
        self._results_text.configure(state="disabled")

    def _append_text(self, text: str) -> None:
        """Append text to the results area."""
        self._results_text.configure(state="normal")
        self._results_text.delete("0.0", "end")
        self._results_text.insert("0.0", text)
        self._results_text.configure(state="disabled")

    def _set_status(self, message: str) -> None:
        """Update the bottom status bar (thread-safe via StringVar)."""
        self._status_var.set(message)
        logger.debug("Status: %s", message)

    def _display_welcome(self) -> None:
        """Show a welcome / help message in the results area on startup."""
        welcome = (
            "Welcome to the Data Quality & ETL Validator\n"
            "─────────────────────────────────────────────\n\n"
            "  Steps:\n"
            "   1. Click  📂 Browse CSV  to select a data file.\n"
            "   2. Click  ▶ Run Validation  to analyse the file.\n"
            "   3. Review the quality summary displayed here.\n"
            "   4. Find saved reports in the  output/  folder.\n\n"
            "  Reports generated:\n"
            "   • output/report.txt  — Human-readable summary\n"
            "   • output/report.csv  — Machine-readable metrics\n\n"
            "  Logs are written to  logs/app.log\n"
        )
        self._results_text.configure(state="normal")
        self._results_text.insert("0.0", welcome)
        self._results_text.configure(state="disabled")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Create and run the application."""
    logger.info("Starting ETL Validator application …")
    app = ETLValidatorApp()
    app.mainloop()
    logger.info("Application closed.")


if __name__ == "__main__":
    main()
