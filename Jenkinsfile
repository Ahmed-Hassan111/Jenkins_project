// ─────────────────────────────────────────────────────────────────────────────
// Jenkinsfile — Data Quality & ETL Validator CI/CD Pipeline
// ─────────────────────────────────────────────────────────────────────────────

pipeline {

     agent any

    environment {
        // Virtual-environment directory (kept inside the workspace)
        VENV_DIR  = "${WORKSPACE}/.venv"
        // Output and log directories
        OUTPUT_DIR = "${WORKSPACE}/output"
        LOG_DIR    = "${WORKSPACE}/logs"
    }

    options {
        // Keep the last 10 builds to limit disk usage
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // Abort if the pipeline takes longer than 30 minutes
        timeout(time: 30, unit: 'MINUTES')
        // Print timestamps in the console log
        timestamps()
    }

    stages {

        // ── Stage 1: Checkout ────────────────────────────────────────────────
        stage('Checkout') {
            steps {
                echo '📥 Checking out source code …'
                checkout scm
                sh 'git log --oneline -5 || true'   // show recent commits
            }
        }

        // ── Stage 2: Install Dependencies ───────────────────────────────────
        stage('Install Dependencies') {
            steps {
                echo '📦 Creating virtual environment and installing dependencies …'
                sh """
                    python3 -m venv ${VENV_DIR}
                    ${VENV_DIR}/bin/pip install --upgrade pip
                    ${VENV_DIR}/bin/pip install -r requirements.txt
                """
            }
        }

        // ── Stage 3: Code Quality Check ──────────────────────────────────────
        stage('Code Quality') {
            steps {
                echo '🔍 Running flake8 lint checks …'
                sh """
                    ${VENV_DIR}/bin/flake8 src/ app.py \
                        --max-line-length=100 \
                        --exclude=__pycache__ \
                        --statistics \
                        || true     # don't fail the build on lint warnings
                """
            }
        }

        // ── Stage 4: Run Tests ───────────────────────────────────────────────
        stage('Run Tests') {
            steps {
                echo '🧪 Running pytest suite …'
                sh """
                    mkdir -p ${OUTPUT_DIR} ${LOG_DIR}
                    PYTHONPATH=${WORKSPACE} \
                    ${VENV_DIR}/bin/pytest tests/ \
                        -v \
                        --tb=short \
                        --junitxml=test-results.xml \
                        --cov=src \
                        --cov-report=xml:coverage.xml \
                        --cov-report=term-missing
                """
            }
            post {
                always {
                    // Publish JUnit test results in Jenkins UI
                    junit 'test-results.xml'
                    // Publish coverage (requires Cobertura plugin)
                    cobertura coberturaReportFile: 'coverage.xml', onlyStable: false
                }
            }
        }

        // ── Stage 5: Run Application Validation (headless) ──────────────────
        stage('Run Application Validation') {
            steps {
                echo '⚡ Running headless CSV validation on sample data …'
                sh """
                    mkdir -p ${OUTPUT_DIR} ${LOG_DIR}
                    # Generate a sample CSV if none exists
                    if [ ! -f sample_data.csv ]; then
                        python3 -c "
import csv, random, math
rows = [['id','name','age','salary','department','score']]
depts = ['Engineering','Marketing','HR','Finance','Operations']
names = ['Alice','Bob','Carol','Dave','Eve','Frank','Grace','Hank']
for i in range(1, 201):
    rows.append([
        i,
        random.choice(names) if i % 7 != 0 else '',   # introduce missing
        random.randint(22, 60) if i % 11 != 0 else '', # introduce missing
        round(random.uniform(40000, 120000), 2),
        random.choice(depts),
        round(random.uniform(0, 100), 1),
    ])
# Add a duplicate
rows.append(rows[1])
with open('sample_data.csv', 'w', newline='') as f:
    csv.writer(f).writerows(rows)
print('sample_data.csv created')
"
                    fi

                    # Run the validator programmatically (no GUI needed)
                    PYTHONPATH=${WORKSPACE} python3 - <<'EOF'
import os, sys
sys.path.insert(0, '.')
from src.validator import DataValidator
from src.report_generator import ReportGenerator

result = DataValidator('sample_data.csv').validate()
print(f"Rows: {result.total_rows}, Cols: {result.total_columns}")
print(f"Missing: {result.total_missing}, Duplicates: {result.duplicate_rows}")

gen = ReportGenerator('${OUTPUT_DIR}')
txt, csv_ = gen.generate(result)
print(f"TXT report: {txt}")
print(f"CSV report: {csv_}")

if not result.success:
    sys.exit(1)
print("Validation PASSED")
EOF
                """
            }
        }

        // ── Stage 6: Archive Reports ─────────────────────────────────────────
        stage('Archive Reports') {
            steps {
                echo '📁 Archiving reports and logs …'
                archiveArtifacts artifacts: 'output/**/*', allowEmptyArchive: true
                archiveArtifacts artifacts: 'logs/**/*',   allowEmptyArchive: true
                archiveArtifacts artifacts: 'test-results.xml, coverage.xml',
                                 allowEmptyArchive: true
            }
        }
    }

    // ── Post-build actions ───────────────────────────────────────────────────
    post {
        success {
            echo '✅ Pipeline completed successfully.'
        }
        failure {
            echo '❌ Pipeline FAILED — check console output for details.'
        }
        always {
            // Clean up the virtual environment to save disk space
            sh "rm -rf ${VENV_DIR} || true"
        }
    }
}
