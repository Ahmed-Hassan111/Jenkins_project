"""
report_generator.py - Converts a ValidationResult into human-readable
report files (TXT and CSV) saved to the project's output/ directory.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import List, Tuple

from src.logger import setup_logger
from src.validator import ValidationResult

logger = setup_logger()


class ReportGenerator:
    """
    Generates TXT and CSV quality-report files from a ValidationResult.

    The output directory is created automatically when it does not exist.

    Usage::

        gen = ReportGenerator("/path/to/project/output")
        txt_path, csv_path = gen.generate(result)
    """

    def __init__(self, output_dir: str) -> None:
        """
        Initialise the generator.

        Args:
            output_dir: Directory where report files will be written.
        """
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info("ReportGenerator ready. Output dir: %s", self.output_dir)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(self, result: ValidationResult) -> Tuple[str, str]:
        """
        Write report.txt and report.csv from the given ValidationResult.

        Args:
            result: Populated ValidationResult from DataValidator.

        Returns:
            Tuple of (txt_path, csv_path) for the written files.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        txt_path = os.path.join(self.output_dir, f"report_{timestamp}.txt")
        csv_path = os.path.join(self.output_dir, f"report_{timestamp}.csv")

        # Also write the canonical "latest" files (overwritten each run)
        latest_txt = os.path.join(self.output_dir, "report.txt")
        latest_csv = os.path.join(self.output_dir, "report.csv")

        logger.info("Generating TXT report …")
        txt_content = self._build_txt(result)
        for path in (txt_path, latest_txt):
            self._write_text(path, txt_content)

        logger.info("Generating CSV report …")
        rows = self._build_csv_rows(result)
        for path in (csv_path, latest_csv):
            self._write_csv(path, rows)

        logger.info("Reports saved → %s | %s", txt_path, csv_path)
        return txt_path, csv_path

    # ------------------------------------------------------------------
    # TXT helpers
    # ------------------------------------------------------------------

    def _build_txt(self, r: ValidationResult) -> str:
        """Compose the full text report as a string."""
        lines: List[str] = []
        sep = "=" * 60

        def section(title: str) -> None:
            lines.append("")
            lines.append(sep)
            lines.append(f"  {title}")
            lines.append(sep)

        # Header
        lines.append(sep)
        lines.append("       DATA QUALITY & ETL VALIDATION REPORT")
        lines.append(sep)
        lines.append(f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  File      : {r.file_path}")
        lines.append(f"  Status    : {'✓ SUCCESS' if r.success else '✗ FAILED'}")

        # Overview
        section("1. DATASET OVERVIEW")
        lines.append(f"  Total Rows       : {r.total_rows:,}")
        lines.append(f"  Total Columns    : {r.total_columns:,}")
        lines.append(f"  Total Missing    : {r.total_missing:,}")
        lines.append(f"  Duplicate Rows   : {r.duplicate_rows:,}")

        # Column info
        section("2. COLUMN NAMES & DATA TYPES")
        for col in r.column_names:
            lines.append(f"  {col:<35} {r.dtypes.get(col, 'unknown')}")

        # Missing values
        section("3. MISSING VALUES PER COLUMN")
        any_missing = False
        for col, cnt in r.missing_per_col.items():
            if cnt > 0:
                any_missing = True
                pct = r.missing_pct.get(col, 0.0)
                lines.append(f"  {col:<35} {cnt:>6,}  ({pct:.2f}%)")
        if not any_missing:
            lines.append("  ✓ No missing values detected.")

        # Numeric stats
        if r.numeric_stats:
            section("4. NUMERIC COLUMN STATISTICS")
            for col, stats in r.numeric_stats.items():
                lines.append(f"\n  [ {col} ]")
                for stat, val in stats.items():
                    lines.append(f"    {stat:<10} : {val}")

        # Errors
        if r.errors:
            section("ERRORS")
            for err in r.errors:
                lines.append(f"  ✗ {err}")

        lines.append("")
        lines.append(sep)
        lines.append("  END OF REPORT")
        lines.append(sep)
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # CSV helpers
    # ------------------------------------------------------------------

    def _build_csv_rows(self, r: ValidationResult) -> List[List[str]]:
        """Build a flat list-of-lists suitable for csv.writer."""
        rows: List[List[str]] = [
            ["metric", "column", "value"],
            ["generated_at", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["file_path", "", r.file_path],
            ["status", "", "SUCCESS" if r.success else "FAILED"],
            ["total_rows", "", str(r.total_rows)],
            ["total_columns", "", str(r.total_columns)],
            ["total_missing", "", str(r.total_missing)],
            ["duplicate_rows", "", str(r.duplicate_rows)],
        ]

        # Per-column dtype
        for col, dtype in r.dtypes.items():
            rows.append(["dtype", col, dtype])

        # Per-column missing counts
        for col, cnt in r.missing_per_col.items():
            rows.append(["missing_count", col, str(cnt)])

        # Per-column missing %
        for col, pct in r.missing_pct.items():
            rows.append(["missing_pct", col, str(pct)])

        # Numeric stats
        for col, stats in r.numeric_stats.items():
            for stat, val in stats.items():
                rows.append([f"stat_{stat}", col, str(val)])

        return rows

    # ------------------------------------------------------------------
    # File writers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_text(path: str, content: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        logger.debug("Wrote TXT report: %s", path)

    @staticmethod
    def _write_csv(path: str, rows: List[List[str]]) -> None:
        with open(path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerows(rows)
        logger.debug("Wrote CSV report: %s", path)
