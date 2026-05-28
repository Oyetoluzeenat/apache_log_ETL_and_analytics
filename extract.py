import os
import glob
import logging

# ─── ADD THIS MASTER SWITCH LINE RIGHT HERE ───────────────────────
logging.basicConfig(level=logging.INFO, format="%(filename)s [%(levelname)s] %(message)s")

logger = logging.getLogger(__name__)

logs_dir = 'data/logs'

def extract_log_files(logs_dir):
    """
    EXTRACT Stage:
    Scans the target directory, discovers all files matching the 
    strict '*.log' specification, and returns a list of file paths.
    """
    logger.info(f"Starting Extract stage directory scan: '{logs_dir}'")
    
    # 1. Validation: Ensure target path exists on the system
    if not os.path.exists(logs_dir):
        logger.error(f"Extract failure: Target directory '{logs_dir}' does not exist.")
        raise FileNotFoundError(f"Directory not found: {logs_dir}")
        
    # 2. Pattern Matching: Filter explicitly for files ending in .log
    search_pattern = os.path.join(logs_dir, "*.log")
    log_files = glob.glob(search_pattern)
    
    # 3. Status Evaluation
    if not log_files:
        logger.warning(f"Extract alert: No matching '*.log' files found in '{logs_dir}'.")
        return []
        
    logger.info(f"Extract success: Discovered {len(log_files)} file stream target(s).")

    return log_files

# Run the extracted file paths to get file list
discovered_files = extract_log_files(logs_dir)

# Loop through the discovered files
for file_path in discovered_files:
    logger.info(f"Opening file stream for extraction: {file_path}")

    # Open safely using a context manager with error="ignore" for dirty bytes
    with open(file_path, 'r', encoding="utf-8",errors='ignore') as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            clean_line = raw_line.strip()
            if clean_line:  # Only process non-empty lines
                logger.debug(f"Extracted line {line_number} from {file_path}: {clean_line[:50]}..." )
        
        logger.info(f"Completed extraction from file: {file_path}")

