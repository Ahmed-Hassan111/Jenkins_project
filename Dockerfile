# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Data Quality & ETL Validator
#
# Supports two run modes:
#   1. GUI mode (default): requires a running X11 server / VNC / X forwarding.
#   2. Headless/CLI mode:  runs validation without a display (useful in CI).
# ─────────────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── System dependencies ───────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        # Tkinter runtime
        python3-tk \
        tk-dev \
        # X11 client libraries needed by CustomTkinter
        libx11-6 \
        libxext6 \
        libxrender1 \
        libxtst6 \
        libxi6 \
        # Clean up
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY . .

# ── Persistent volumes ────────────────────────────────────────────────────────
# Mount host directories to preserve reports and logs across container runs.
VOLUME ["/app/output", "/app/logs"]

# ── Environment ───────────────────────────────────────────────────────────────
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # DISPLAY must be set at runtime for GUI mode, e.g. -e DISPLAY=:0
    DISPLAY=${DISPLAY}

# ── Default command ───────────────────────────────────────────────────────────
CMD ["python", "app.py"]
