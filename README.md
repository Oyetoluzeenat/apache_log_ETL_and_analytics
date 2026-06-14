# Logforge Apache: Production Log Processing & Analytics Pipeline

## The Architectural Narrative (Overview)
In any enterprise cloud environment, web servers generate billions of log lines daily. Hidden within these walls of text are critical business insights (such as platform usage trends) and structural anomalies (such as malicious vulnerability scans or system failures). 

As a Data Engineer, the challenge isn't just reading this data—it's building a resilient, decoupled data processing system that handles it at scale. If an unexpected binary payload, a truncated string, or a corrupted timestamp hits a fragile pipeline, the entire ingestion loop crashes, leading to severe data loss and visibility blind spots.

**Logforge Apache** was engineered to solve this problem. It shifts log processing away from brittle, monolithic scripts toward an isolated, decoupled, and idempotent **Extract-Transform-Load (ETL)** command-line application. By introducing a staging area cache, strict regex boundaries, an automated validation gate, and a Dead-Letter Queue (DLQ), Logforge processes valid traffic with sub-linear efficiency while cleanly containing malformed entries for developer debugging—ensuring zero data loss.

---

## Project Goal
The primary objective of this project is to construct a production-ready, command-line driven ETL data pipeline that securely parses Apache Combined Log files, enforces database integrity, and exports business intelligence metrics.

The pipeline is explicitly engineered to achieve:
1. **Fault Tolerance:** Isolate structural formatting anomalies without terminating the processing workflow.
2. **Idempotence:** Ensure that identical multi-run executions do not create duplicate data rows or inflate reports.
3. **High Performance:** Minimize database query execution times from $O(N)$ sequential scans down to $O(\log N)$ sub-linear lookups using composite indexes.

---

## Project Architecture
Logforge abandons linear script execution in favor of a **Decoupled State CLI Architecture**. Each phase stores its state inside an internal staging directory (`.tmp/`), allowing stages to be tested and run completely independently.

<image src="images/apache_log_forge.png" alt="apache_log_forge"/>


### Technical Component Breakdown:
**etl_apache.py:** The central CLI controller driven by argparse. It routes subcommands (extract, transform, load, summary) to their respective modules.

**parser.py:** The structural transformation layer. Uses a pre-compiled regular expression with named capture groups and strict character-class exclusions to avoid catastrophic backtracking. Includes calendar-parsing verification and range validations (100 to 599) for HTTP status codes.

**database.py:** The load and transaction management engine. It initializes the SQLite schema, maps structured keys to tables, applies a UNIQUE constraint over a compound business key (IP + Timestamp + Resource Path) to enforce idempotence, and sets up explicit indexes for performance optimization.

**summarizer.py:** The aggregation utility. It runs complex SQL queries over the analytical database tables to export CSV metrics and a single consolidated JSON run-summary payload.

## Source Dataset
The pipeline is designed around the standard Apache Combined Log Format. Each log entry is structured as a single space-delimited string layout wrapped in contextual string delimiters:

**Sample Input Record:**

83.149.9.216 - - [17/May/2015:10:05:03 +0000] "GET /presentations/logstash-monitorama-2013/images/kibana-search.png HTTP/1.1" 200 203023 "[http://semicomplete.com/presentations/logstash-monitorama-2013/](http://semicomplete.com/presentations/logstash-monitorama-2013/)" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.77 Safari/537.36"
The transformation module parses this record into 9 distinct database schema tokens:

**IP Address:** Client identification network indicator (83.149.9.216).

**Timestamp:** Verified request window date and time (17/May/2015:10:05:03 +0000).

**HTTP Method:** Transaction method protocol verb (GET).

**Resource Path:** Targeted file system endpoint url (/presentations/.../kibana-search.png).

**Protocol:** Communication standard version type (HTTP/1.1).

**Status Code:** Process response integer (200).

**Bytes Sent:** Target delivery byte payload volume size (203023).

**Referrer:** Upstream routing link origin pointer (http://semicomplete.com/...).

User-Agent: Client software application metadata footprint configuration.

### How to Reproduce & Run
1. Project Workspace Directory Layout
Ensure your workspace directory matches this layout structure before executing commands:

log_forge_apache/
├── data/
│   └── logs/
│       └── apache_logs.log   <-- Place your source log files here
├── database.py
├── etl_apache.py
├── parser.py
├── summarizer.py
└── Makefile
2. Environment Setup
Activate your project's Python virtual environment (.venv):

PowerShell
# Windows PowerShell
.venv\Scripts\Activate.ps1
3. Execution Options
Option A: End-to-End Execution (Recommended)
To run all 4 pipeline steps sequentially (Extract, Transform, Load, and Summary Generation) with a single command, use:

PowerShell
make pipeline
Option B: Step-by-Step CLI Execution
If you prefer to execute or debug individual pipeline segments independently, use the following step-by-step commands:

PowerShell
### Step 1: Scan and cache the raw log text streams to the staging area
make extract

### Step 2: Extract text data into structured JSON objects via regex validation
make transform

### Step 3: Stream and batch-load records directly into the SQLite tables
make load

### Step 4: Compute analytics queries and write out summary reports
make summary

### Administrative Operations
To wipe out temporary runtime caching metadata folders, remove the generated reports, and clear the operational database to run a completely fresh test run, execute:

PowerShell
make clean

### Reviewing Output Artifacts
After running the pipeline, check the reports/ directory for your final metrics:

top_endpoints.csv — The 10 most frequently accessed system paths.

top_ips.csv — The 10 most active client network addresses.

status_distribution.csv — A comprehensive breakdown of HTTP server responses.

pipeline_summary.json — A complete nested metrics summary object ready for dashboard integration.