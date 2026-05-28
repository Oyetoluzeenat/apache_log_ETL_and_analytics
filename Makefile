SHELL := powershell.exe

# Define the Python interpreter path inside your virtual environment
PYTHON = .venv/Scripts/python.exe

# The default action when you just type 'make' on its own
.DEFAULT_GOAL := help

.PHONY: help extract transform load summary pipeline clean setup

help:
	@echo "=========================================================="
	@echo "             LOGFORGE APACHE PIPELINE CONTROL             "
	@echo "=========================================================="
	@echo "Available shortcuts:"
	@echo "  make extract    - Scan directory and extract raw logs"
	@echo "  make transform  - Apply regex structure and validation"
	@echo "  make load       - Store results into SQLite DB"
	@echo "  make summary    - Compute metrics (Top IPs, Endpoints, etc.)"
	@echo "  make pipeline   - Run all 4 ETL stages sequentially"
	@echo "  make clean      - Delete temporary staging caches and reports"
	@echo "  make setup      - Install virtual environment requirements"
	@echo "=========================================================="

# Individual Pipeline Stages
extract:
	$(PYTHON) etl_apache.py extract --input data/logs/

transform:
	$(PYTHON) etl_apache.py transform

load:
	$(PYTHON) etl_apache.py load --db db/logs.db

summary:
	$(PYTHON) etl_apache.py summary --output-format json

# ─── SEQUENTIAL PIPELINE CHAINING ─────────────────────────────────
# This rule links all steps together. Running 'make pipeline' checks 
# and runs each stage in chronological data order automatically.
pipeline: extract transform load summary
	@echo "ETL Pipeline completed successfully! Check the 'reports/' directory."

# Administrative Shortcuts
# Administrative Shortcuts (Windows Native PowerShell compatible)
clean:
	powershell -Command "if (Test-Path .tmp) { Remove-Item -Recurse -Force .tmp }"
	powershell -Command "if (Test-Path db/logs.db) { Remove-Item -Force db/logs.db }"
	powershell -Command "if (Test-Path reports) { Remove-Item -Recurse -Force reports }"
	@echo "Project workspace cleaned. Caches, local database, and reports removed."

setup:
	$(PYTHON) -m pip install --upgrade pip
	@echo "Setup complete. Workspace initialized."