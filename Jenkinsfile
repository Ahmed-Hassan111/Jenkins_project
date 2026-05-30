// ─────────────────────────────────────────────────────────────────────────────
// Jenkinsfile — Data Quality & ETL Validator
// Compatible with plain Jenkins (no Docker plugin required).
//
// KEY FIXES vs previous version:
//   1. Uses requirements-ci.txt (no customtkinter — GUI not needed in CI).
//   2. pandas pinned to 2.2.3 which ships pre-built wheels for Python 3.13.
//   3. numpy range constraint avoids source-build fallback on any Python.
// ─────────────────────────────────────────────────────────────────────────────

pipeline {

    agent any

    environment {
        OUTPUT_DIR = "${WORKSPACE}/output"
        LOG_DIR    = "${WORKSPACE}/logs"
        VENV_DIR   = "${WORKSPACE}/.venv"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }

    stages {

        // ── Stage 1: Checkout ────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code …'
                checkout scm
                sh 'git log --oneline -5 || true'
            }
        }

        // ── Stage 2: Install Dependencies ────────────────────────────────────
        stage('Install Dependencies') {
            steps {
                echo '📦 Installing CI dependencies (no GUI packages) …'
                sh '''
                    # ── Install Python if missing (Debian/Ubuntu agent) ──────
                    if ! command -v python3 > /dev/null 2>&1; then
                        echo "Python3 not found — installing …"
                        apt-get update -qq
                        apt-get install -y -qq python3 python3-pip python3-venv
                    fi

                    echo "✅ Python: $(python3 --version)"

                    # ── Create isolated virtual environment ──────────────────
                    python3 -m venv ${VENV_DIR}
                    ${VENV_DIR}/bin/pip install --upgrade pip --quiet

                    # ── Install CI-only deps (no customtkinter) ──────────────
                    # requirements-ci.txt uses pandas==2.2.3 which has
                    # pre-built wheels for Python 3.11 / 3.12 / 3.13.
                    # pandas==2.2.2 did NOT have a py3.13 wheel and failed
                    # to compile from source.
                    ${VENV_DIR}/bin/pip install -r requirements-ci.txt --quiet

                    echo "✅ All CI dependencies installed."
                    ${VENV_DIR}/bin/pip list
                '''
            }
        }

        // ── Stage 3: Code Quality ─────────────────────────────────────────────
        stage('Code Quality') {
            steps {
                echo '🔍 Running flake8 lint checks …'
                sh '''
                    ${VENV_DIR}/bin/flake8 src/ app.py \
                        --max-line-length=100 \
                        --exclude=__pycache__ \
                        --statistics \
                        || true
                '''
            }
        }

        // ── Stage 4: Run Tests ────────────────────────────────────────────────
        stage('Run Tests') {
            steps {
                echo '🧪 Running pytest suite …'
                sh '''
                    mkdir -p ${OUTPUT_DIR} ${LOG_DIR}
                    PYTHONPATH=${WORKSPACE} \
                    ${VENV_DIR}/bin/pytest tests/ \
                        -v \
                        --tb=short \
                        --junitxml=test-results.xml \
                        --cov=src \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                }
            }
        }

        // ── Stage 5: Run Application Validation (headless) ───────────────────
        stage('Run Application Validation') {
            steps {
                echo '⚡ Running headless CSV validation …'
                sh '''
                    mkdir -p ${OUTPUT_DIR} ${LOG_DIR}

                    # Generate a sample CSV with intentional quality issues
                    ${VENV_DIR}/bin/python3 -c "
import csv, random
rows = [['id','name','age','salary','department','score']]
depts = ['Engineering','Marketing','HR','Finance','Operations']
names = ['Alice','Bob','Carol','Dave','Eve','Frank','Grace','Hank']
for i in range(1, 201):
    rows.append([
        i,
        random.choice(names) if i % 7  != 0 else '',
        random.randint(22, 60)          if i % 11 != 0 else '',
        round(random.uniform(40000, 120000), 2),
        random.choice(depts),
        round(random.uniform(0, 100), 1),
    ])
rows.append(rows[1])   # intentional duplicate
with open('sample_data.csv', 'w', newline='') as f:
    csv.writer(f).writerows(rows)
print('sample_data.csv created')
"

                    # Run the validator without any GUI / DISPLAY
                    PYTHONPATH=${WORKSPACE} \
                    ${VENV_DIR}/bin/python3 -c "
import sys, os
sys.path.insert(0, '.')
from src.validator import DataValidator
from src.report_generator import ReportGenerator

result = DataValidator('sample_data.csv').validate()
print(f'  Rows      : {result.total_rows}')
print(f'  Columns   : {result.total_columns}')
print(f'  Missing   : {result.total_missing}')
print(f'  Duplicates: {result.duplicate_rows}')

gen = ReportGenerator(os.environ['OUTPUT_DIR'])
txt, csv_ = gen.generate(result)
print(f'  TXT report: {txt}')
print(f'  CSV report: {csv_}')

if not result.success:
    sys.exit(1)
print('Validation PASSED')
"
                '''
            }
        }

        // ── Stage 6: Archive Reports ──────────────────────────────────────────
        stage('Archive Reports') {
            steps {
                echo '📁 Archiving reports and logs …'
                archiveArtifacts artifacts: 'output/**/*',      allowEmptyArchive: true
                archiveArtifacts artifacts: 'logs/**/*',        allowEmptyArchive: true
                archiveArtifacts artifacts: 'test-results.xml', allowEmptyArchive: true
                archiveArtifacts artifacts: 'coverage.xml',     allowEmptyArchive: true
            }
        }
    }

    post {
        success {
            echo '✅ Pipeline completed successfully.'
        }
        failure {
            echo '❌ Pipeline FAILED — check the console output above.'
        }
        always {
            sh 'rm -f sample_data.csv    || true'
            sh 'rm -rf ${VENV_DIR}       || true'
        }
    }
}