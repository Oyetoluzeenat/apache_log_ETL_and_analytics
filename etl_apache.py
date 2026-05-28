import os
import glob
import json
import argparse
import logging
from parser import transform_batch
from database import init_db, load_data_to_db
from summarizer import generate_summaries

# Global log formatting
logging.basicConfig(level=logging.INFO, format="%(filename)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TMP_DIR = ".tmp"
EXTRACT_CACHE = os.path.join(TMP_DIR, "extracted_lines.json")
TRANSFORM_CACHE = os.path.join(TMP_DIR, "transformed_payload.json")

def ensure_tmp_dir():
    os.makedirs(TMP_DIR, exist_ok=True)

# ─── SUBCOMMAND ACTIONS ───────────────────────────────────────────

def handle_extract(args):
    """Command: extract --input <dir>"""
    logger.info(f"CLI Triggered: EXTRACT stage scanning path '{args.input}'")
    ensure_tmp_dir()
    
    if not os.path.exists(args.input):
        logger.error(f"Extract target directory '{args.input}' does not exist.")
        return

    search_pattern = os.path.join(args.input, "*.log")
    log_files = glob.glob(search_pattern)
    
    if not log_files:
        logger.warning(f"No '.log' files discovered inside '{args.input}'")
        return

    extracted_lines = []
    for file_path in log_files:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.strip():
                    extracted_lines.append(line.strip())
                    
    # Cache to disk for downstream CLI steps
    with open(EXTRACT_CACHE, "w", encoding="utf-8") as f:
        json.dump(extracted_lines, f)
        
    logger.info(f"Extract Complete: Cached {len(extracted_lines)} raw string lines to staging area.")


def handle_transform(args):
    """Command: transform"""
    logger.info("CLI Triggered: TRANSFORM stage processing staging lines...")
    
    if not os.path.exists(EXTRACT_CACHE):
        logger.error("Transform Failure: Staging file missing. You must run the 'extract' command first.")
        return

    with open(EXTRACT_CACHE, "r", encoding="utf-8") as f:
        raw_lines = json.load(f)

    # Call your parser logic batch transformation
    valid_records, malformed_records = transform_batch(raw_lines)
    
    # Cache payload for the Load layer
    payload = {
        "valid": valid_records,
        "malformed": malformed_records
    }
    with open(TRANSFORM_CACHE, "w", encoding="utf-8") as f:
        json.dump(payload, f)
        
    logger.info(f"Transform Complete: {len(valid_records)} valid logs structured. {len(malformed_records)} lines tagged malformed.")


def handle_load(args):
    """Command: load --db <path>"""
    logger.info(f"CLI Triggered: LOAD stage writing to destination database '{args.db}'")
    
    if not os.path.exists(TRANSFORM_CACHE):
        logger.error("Load Failure: Transformed payload cache missing. You must run 'transform' first.")
        return

    with open(TRANSFORM_CACHE, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Initialize targeted DB path and run insertion rules
    db_dir = os.path.dirname(args.db)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    init_db(args.db)
    load_data_to_db(payload["valid"], payload["malformed"], db_path=args.db)
    
    # Save the current operational DB path for the summary tool fallback
    with open(os.path.join(TMP_DIR, "current_db.txt"), "w") as f:
        f.write(args.db)


def handle_summary(args):
    """Command: summary --output-format <json|csv>"""
    logger.info(f"CLI Triggered: SUMMARY generation running format output spec -> {args.output_format}")
    
    # Find which database path was written to last
    db_path = "logs.db"
    db_tracking_file = os.path.join(TMP_DIR, "current_db.txt")
    if os.path.exists(db_tracking_file):
        with open(db_tracking_file, "r") as f:
            db_path = f.read().strip()

    # Pass configuration straight to your summarizer engine
    # (Your summarizer automatically exports both JSON and CSV files by default)
    generate_summaries(db_path=db_path, output_dir="reports")
    logger.info(f"Summary reports generated successfully from '{db_path}'. Check your 'reports/' directory.")

# ─── CORE PARSER ORCHESTRATION ────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Logforge Apache Pipeline Command Line Engine Tool",
        epilog="Example: python etl_apache.py extract --input data/logs/"
    )
    subparsers = parser.add_subparsers(title="Available Pipeline Commands", dest="command", required=True)

    # 1. Extract Command Setup
    p_extract = subparsers.add_parser("extract", help="Scan a directory and pull raw string entries.")
    p_extract.add_argument("--input", required=True, help="Target path pointing to source folder location.")
    p_extract.set_defaults(func=handle_extract)

    # 2. Transform Command Setup
    p_transform = subparsers.add_parser("transform", help="Apply regex patterns and run metadata schema sorting.")
    p_transform.set_defaults(func=handle_transform)

    # 3. Load Command Setup
    p_load = subparsers.add_parser("load", help="Establish transactions to import arrays into tables.")
    p_load.add_argument("--db", default="logs.db", help="Target filename location path for local SQLite storage.")
    p_load.set_defaults(func=handle_load)

    # 4. Summary Command Setup
    p_summary = subparsers.add_parser("summary", help="Aggregate metrics into static file sheets.")
    p_summary.add_argument("--output-format", choices=["json", "csv"], default="json", help="Core structure extension layout format choice.")
    p_summary.set_defaults(func=handle_summary)

    # Parse and direct arguments to respective execution functions
    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()