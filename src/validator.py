"""
validator.py - Core data-quality validation logic for the ETL Validator.

Reads a CSV file with Pandas and computes a rich set of quality metrics
that are returned as a plain Python dictionary for easy consumption by
the report generator and the GUI.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Dict, Any

import pandas as pd

from src.logger import setup_logger

logger = setup_logger()


@dataclass
class ValidationResult:
    """
    Container for all quality metrics produced by DataValidator.

    Attributes:
        file_path:        Absolute path of the validated CSV file.
        total_rows:       Number of data rows (excluding header).
        total_columns:    Number of columns.
        column_names:     Ordered list of column names.
        dtypes:           Mapping of column name → pandas dtype string.
        missing_per_col:  Mapping of column name → count of NaN/None values.
        total_missing:    Sum of all missing values across the dataset.
        duplicate_rows:   Number of fully-duplicated rows.
        missing_pct:      Mapping of column name → percentage of missing values.
        numeric_stats:    Mapping of column name → descriptive stats dict
                          (only for numeric columns).
        errors:           List of error messages encountered during validation.
        success:          True when validation completed without fatal errors.
    """

    file_path: str = ""
    total_rows: int = 0
    total_columns: int = 0
    column_names: list = field(default_factory=list)
    dtypes: Dict[str, str] = field(default_factory=dict)
    missing_per_col: Dict[str, int] = field(default_factory=dict)
    total_missing: int = 0
    duplicate_rows: int = 0
    missing_pct: Dict[str, float] = field(default_factory=dict)
    numeric_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: list = field(default_factory=list)
    success: bool = False


class DataValidator:
    """
    Performs comprehensive data-quality validation on a CSV file.

    Usage::

        validator = DataValidator("/path/to/data.csv")
        result = validator.validate()
    """

    def __init__(self, file_path: str) -> None:
        """
        Initialise the validator.

        Args:
            file_path: Path to the CSV file to validate.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        self.file_path = os.path.abspath(file_path)
        self._df: pd.DataFrame | None = None
        logger.info("DataValidator initialised for file: %s", self.file_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self) -> ValidationResult:
        """
        Run all validation checks and return a ValidationResult.

        Returns:
            A populated ValidationResult dataclass.
        """
        result = ValidationResult(file_path=self.file_path)

        try:
            self._load_csv(result)
            self._compute_shape(result)
            self._compute_dtypes(result)
            self._compute_missing(result)
            self._compute_duplicates(result)
            self._compute_numeric_stats(result)
            result.success = True
            logger.info("Validation completed successfully.")
        except Exception as exc:  # noqa: BLE001
            msg = f"Validation failed: {exc}"
            logger.error(msg, exc_info=True)
            result.errors.append(msg)

        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_csv(self, result: ValidationResult) -> None:
        """Load the CSV into a DataFrame."""
        logger.debug("Loading CSV file …")
        self._df = pd.read_csv(self.file_path)
        logger.info("CSV loaded: %d rows × %d columns.", *self._df.shape)

    def _compute_shape(self, result: ValidationResult) -> None:
        """Populate row/column counts and column names."""
        logger.debug("Computing dataset shape …")
        result.total_rows, result.total_columns = self._df.shape
        result.column_names = self._df.columns.tolist()

    def _compute_dtypes(self, result: ValidationResult) -> None:
        """Map each column to its pandas dtype."""
        logger.debug("Inspecting column data types …")
        result.dtypes = {col: str(dtype) for col, dtype in self._df.dtypes.items()}

    def _compute_missing(self, result: ValidationResult) -> None:
        """Count and percentage-ise missing values per column."""
        logger.debug("Counting missing values …")
        missing_series = self._df.isnull().sum()
        result.missing_per_col = missing_series.to_dict()
        result.total_missing = int(missing_series.sum())

        # Percentage (avoid division-by-zero for empty DataFrames)
        if result.total_rows > 0:
            result.missing_pct = {
                col: round((cnt / result.total_rows) * 100, 2)
                for col, cnt in result.missing_per_col.items()
            }
        else:
            result.missing_pct = {col: 0.0 for col in result.missing_per_col}

        logger.info(
            "Total missing values: %d across %d columns.",
            result.total_missing,
            result.total_columns,
        )

    def _compute_duplicates(self, result: ValidationResult) -> None:
        """Count fully-duplicated rows."""
        logger.debug("Checking for duplicate rows …")
        result.duplicate_rows = int(self._df.duplicated().sum())
        logger.info("Duplicate rows found: %d", result.duplicate_rows)

    def _compute_numeric_stats(self, result: ValidationResult) -> None:
        """Compute descriptive statistics for numeric columns."""
        logger.debug("Computing numeric column statistics …")
        numeric_cols = self._df.select_dtypes(include="number").columns.tolist()

        if not numeric_cols:
            logger.info("No numeric columns found; skipping stats.")
            return

        desc = self._df[numeric_cols].describe().to_dict()
        # Round every stat to 4 decimal places for readability
        result.numeric_stats = {
            col: {stat: round(val, 4) for stat, val in stats.items()}
            for col, stats in desc.items()
        }
        logger.info("Numeric stats computed for columns: %s", numeric_cols)
