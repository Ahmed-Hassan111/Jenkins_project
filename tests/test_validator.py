"""
tests/test_validator.py - Unit tests for DataValidator and ReportGenerator.

Run with:  pytest tests/ -v
"""

from __future__ import annotations

import csv
import os
import tempfile
import textwrap

import pandas as pd
import pytest

from src.validator import DataValidator, ValidationResult
from src.report_generator import ReportGenerator


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def clean_csv(tmp_path) -> str:
    """CSV with no missing values or duplicates."""
    path = tmp_path / "clean.csv"
    path.write_text(
        textwrap.dedent("""\
            id,name,age,salary
            1,Alice,30,70000
            2,Bob,25,55000
            3,Carol,35,90000
        """)
    )
    return str(path)


@pytest.fixture()
def dirty_csv(tmp_path) -> str:
    """CSV with missing values and a duplicate row."""
    path = tmp_path / "dirty.csv"
    path.write_text(
        textwrap.dedent("""\
            id,name,age,salary
            1,Alice,30,70000
            2,,25,
            3,Carol,,90000
            1,Alice,30,70000
        """)
    )
    return str(path)


@pytest.fixture()
def output_dir(tmp_path) -> str:
    d = tmp_path / "output"
    d.mkdir()
    return str(d)


# ─────────────────────────────────────────────────────────────────────────────
# DataValidator tests
# ─────────────────────────────────────────────────────────────────────────────

class TestDataValidatorInit:
    def test_raises_for_missing_file(self):
        with pytest.raises(FileNotFoundError):
            DataValidator("/nonexistent/path/data.csv")

    def test_accepts_existing_file(self, clean_csv):
        v = DataValidator(clean_csv)
        assert os.path.isabs(v.file_path)


class TestValidateCleanFile:
    @pytest.fixture(autouse=True)
    def run(self, clean_csv):
        self.result: ValidationResult = DataValidator(clean_csv).validate()

    def test_success_flag(self):
        assert self.result.success is True

    def test_no_errors(self):
        assert self.result.errors == []

    def test_row_count(self):
        assert self.result.total_rows == 3

    def test_column_count(self):
        assert self.result.total_columns == 4

    def test_column_names(self):
        assert self.result.column_names == ["id", "name", "age", "salary"]

    def test_no_missing(self):
        assert self.result.total_missing == 0
        assert all(v == 0 for v in self.result.missing_per_col.values())

    def test_no_duplicates(self):
        assert self.result.duplicate_rows == 0

    def test_dtypes_populated(self):
        assert set(self.result.dtypes.keys()) == {"id", "name", "age", "salary"}

    def test_numeric_stats_present(self):
        # id, age, salary are numeric
        assert "age" in self.result.numeric_stats
        assert "mean" in self.result.numeric_stats["age"]

    def test_missing_pct_all_zero(self):
        for col, pct in self.result.missing_pct.items():
            assert pct == 0.0


class TestValidateDirtyFile:
    @pytest.fixture(autouse=True)
    def run(self, dirty_csv):
        self.result: ValidationResult = DataValidator(dirty_csv).validate()

    def test_success_flag(self):
        assert self.result.success is True

    def test_row_count(self):
        assert self.result.total_rows == 4

    def test_missing_name(self):
        assert self.result.missing_per_col["name"] == 1

    def test_missing_salary(self):
        assert self.result.missing_per_col["salary"] == 1

    def test_missing_age(self):
        assert self.result.missing_per_col["age"] == 1

    def test_total_missing(self):
        assert self.result.total_missing == 3

    def test_duplicate_rows(self):
        assert self.result.duplicate_rows == 1

    def test_missing_pct_name(self):
        # 1 out of 4 rows → 25 %
        assert self.result.missing_pct["name"] == pytest.approx(25.0)


# ─────────────────────────────────────────────────────────────────────────────
# ReportGenerator tests
# ─────────────────────────────────────────────────────────────────────────────

class TestReportGenerator:
    @pytest.fixture(autouse=True)
    def setup(self, clean_csv, output_dir):
        result = DataValidator(clean_csv).validate()
        gen = ReportGenerator(output_dir)
        self.txt_path, self.csv_path = gen.generate(result)
        self.output_dir = output_dir

    def test_txt_file_created(self):
        assert os.path.isfile(self.txt_path)

    def test_csv_file_created(self):
        assert os.path.isfile(self.csv_path)

    def test_latest_txt_exists(self):
        assert os.path.isfile(os.path.join(self.output_dir, "report.txt"))

    def test_latest_csv_exists(self):
        assert os.path.isfile(os.path.join(self.output_dir, "report.csv"))

    def test_txt_contains_overview(self):
        content = open(self.txt_path, encoding="utf-8").read()
        assert "DATASET OVERVIEW" in content
        assert "Total Rows" in content

    def test_csv_has_header(self):
        with open(self.csv_path, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader)
        assert header == ["metric", "column", "value"]

    def test_csv_contains_total_rows(self):
        with open(self.csv_path, newline="", encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        metrics = {r[0]: r[2] for r in rows if len(r) == 3}
        assert metrics.get("total_rows") == "3"

    def test_txt_reports_no_missing(self):
        content = open(self.txt_path, encoding="utf-8").read()
        assert "No missing values detected" in content
