# ⚡ Data Quality & ETL Validator

A professional-grade desktop application for automated CSV data quality analysis and ETL pipeline validation. Built with **Python**, **CustomTkinter**, and **Pandas**.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🖥️ Modern GUI | Dark-themed CustomTkinter desktop UI |
| 📊 Data Quality Checks | Rows, columns, missing values, duplicates, dtypes, numeric stats |
| 📄 Auto Reports | Saves `report.txt` and `report.csv` to `output/` on every run |
| 📝 Structured Logging | Timestamped logs written to `logs/app.log` |
| ✅ Unit Tests | Full pytest suite with coverage reporting |
| 🐳 Docker Ready | Dockerfile + docker-compose for containerised runs |
| 🔧 Jenkins CI/CD | Multi-stage pipeline with test publishing and artifact archiving |

---

## 📁 Project Structure

```
project/
├── app.py                  # Main entry point (GUI)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Jenkinsfile
├── README.md
├── src/
│   ├── __init__.py
│   ├── validator.py        # DataValidator — core quality checks
│   ├── report_generator.py # ReportGenerator — TXT & CSV output
│   └── logger.py           # Centralised logging setup
├── tests/
│   ├── __init__.py
│   └── test_validator.py   # pytest unit tests
├── output/                 # Generated reports (auto-created)
└── logs/                   # Application logs (auto-created)
```

---

## 🚀 Quick Start (Local)

### Prerequisites

- Python **3.10+**
- `pip`
- A display / desktop environment (for the GUI)

### 1. Clone / download the project

```bash
git clone https://github.com/your-org/etl-validator.git
cd etl-validator
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the application

```bash
python app.py
```

The GUI will open. Click **Browse CSV** to select a file, then **Run Validation**.

---

## 🧪 Running Tests

```bash
# Basic run
pytest tests/ -v

# With coverage report
pytest tests/ -v --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

---

## 🐳 Docker

### Build the image

```bash
docker build -t etl-validator .
```

### Run tests in Docker (headless — no display needed)

```bash
docker-compose run etl-tests
```

### Run the GUI in Docker (requires X11)

**Linux:**
```bash
xhost +local:docker
docker-compose up etl-validator
```

**macOS (XQuartz required):**
```bash
brew install --cask xquartz
open -a XQuartz
xhost +localhost
DISPLAY=host.docker.internal:0 docker-compose up etl-validator
```

**Windows (VcXsrv required):**
```bash
# Install VcXsrv, start it with "Disable access control" checked
set DISPLAY=host.docker.internal:0.0
docker-compose up etl-validator
```

---

## 🔧 Jenkins CI/CD

### Pipeline stages

| # | Stage | What it does |
|---|---|---|
| 1 | **Checkout** | Clones the repository |
| 2 | **Install Dependencies** | Creates a venv and installs `requirements.txt` |
| 3 | **Code Quality** | Runs `flake8` lint checks |
| 4 | **Run Tests** | Executes the full pytest suite; publishes JUnit XML |
| 5 | **Run Application Validation** | Headless validation on a generated sample CSV |
| 6 | **Archive Reports** | Archives `output/`, `logs/`, and test result files |

### Setup

1. Create a new **Pipeline** job in Jenkins.
2. Point it at your repository and set "Script Path" to `Jenkinsfile`.
3. Ensure the build agent has Python 3.11+ and the label `python`.
4. (Optional) Install the **Cobertura** and **JUnit** Jenkins plugins for richer reporting.

---

## 📊 Sample Output

### Console / Results area

```
========================================================
  DATA QUALITY & ETL VALIDATION — SUMMARY
========================================================
  File    : sales_data.csv
  Status  : ✅ SUCCESS

  ────────────────────────────────────────────────────────
  DATASET OVERVIEW
  ────────────────────────────────────────────────────────
  Total Rows       :    200
  Total Columns    :      6
  Total Missing    :     27
  Duplicate Rows   :      1

  ────────────────────────────────────────────────────────
  MISSING VALUES
  ────────────────────────────────────────────────────────
    name                                     14  (7.00%)
    age                                      13  (6.50%)

  REPORTS SAVED
  ────────────────────────────────────────────────────────
  TXT : /path/to/project/output/report_20240601_143022.txt
  CSV : /path/to/project/output/report_20240601_143022.csv
```

---

## 📝 Logging

All events are logged to `logs/app.log` with timestamps and log levels:

```
2024-06-01 14:30:20 | INFO     | Logger initialised. Log file: logs/app.log
2024-06-01 14:30:22 | INFO     | File selected: sales_data.csv
2024-06-01 14:30:22 | INFO     | CSV loaded: 200 rows × 6 columns.
2024-06-01 14:30:22 | INFO     | Total missing values: 27 across 6 columns.
2024-06-01 14:30:22 | INFO     | Duplicate rows found: 1
2024-06-01 14:30:22 | INFO     | Validation completed successfully.
2024-06-01 14:30:22 | INFO     | Reports saved → output/report_20240601_143022.txt
```

---

## 🤝 Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for new functionality.
4. Open a pull request.

---

## GUI After running
<img width="1538" height="1002" alt="GUI" src="https://github.com/user-attachments/assets/4ff35bd3-5d2b-478e-a67a-8da0c8c6537f" />

