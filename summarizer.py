import sqlite3
import csv
import json
import os
import logging

logger = logging.getLogger(__name__)

def run_analytical_aggregations(db_path="logs.db"):
    """Queries the database and returns data structures for the required metrics."""
    conn = sqlite3.connect(db_path)
    # Allows fetching rows as dictionaries instead of tuples
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    metrics = {}
    
    # Query 1: Top 10 Endpoints (Resource Paths)
    cursor.execute("""
        SELECT resource_path, COUNT(*) as request_count
        FROM logs
        GROUP BY resource_path
        ORDER BY request_count DESC
        LIMIT 10
    """)
    metrics['top_endpoints'] = [dict(row) for row in cursor.fetchall()]
    
    # Query 2: Status Code Distribution
    cursor.execute("""
        SELECT status_code, COUNT(*) as occurrences
        FROM logs
        GROUP BY status_code
        ORDER BY occurrences DESC
    """)
    metrics['status_distribution'] = [dict(row) for row in cursor.fetchall()]
    
    # Query 3: Top Client IPs (Volume Drivers)
    cursor.execute("""
        SELECT ip, COUNT(*) as hit_count
        FROM logs
        GROUP BY ip
        ORDER BY hit_count DESC
        LIMIT 10
    """)
    metrics['top_ips'] = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return metrics

def export_to_csv(metrics, output_dir="reports"):
    """Generates explicit individual CSV spreadsheets for each analytical field."""
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Export Endpoints CSV
    endpoints_file = os.path.join(output_dir, "top_endpoints.csv")
    with open(endpoints_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Resource Path", "Request Count"])
        for row in metrics['top_endpoints']:
            writer.writerow([row['resource_path'], row['request_count']])
            
    # 2. Export Status Codes CSV
    status_file = os.path.join(output_dir, "status_distribution.csv")
    with open(status_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Status Code", "Occurrences"])
        for row in metrics['status_distribution']:
            writer.writerow([row['status_code'], row['occurrences']])
            
    # 3. Export IPs CSV
    ips_file = os.path.join(output_dir, "top_ips.csv")
    with open(ips_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Client IP", "Hit Count"])
        for row in metrics['top_ips']:
            writer.writerow([row['ip'], row['hit_count']])
            
    logger.info(f"CSV Summaries exported cleanly to folder: '{output_dir}/'")

def export_to_json(metrics, output_dir="reports"):
    """Generates a combined JSON payload representing the entire operational run summary."""
    os.makedirs(output_dir, exist_ok=True)
    json_file = os.path.join(output_dir, "pipeline_summary.json")
    
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4)
        
    logger.info(f"JSON Operational Run Summary saved to: '{json_file}'")

def generate_summaries(db_path="logs.db", output_dir="reports"):
    """Orchestrates the extraction and file writing process for business reporting."""
    logger.info("Starting Reporting Stage Analytical Calculations...")
    if not os.path.exists(db_path):
        logger.error(f"Reporting Failure: Source database '{db_path}' not found. Cannot calculate metrics.")
        return
        
    metrics = run_analytical_aggregations(db_path)
    export_to_csv(metrics, output_dir)
    export_to_json(metrics, output_dir)
    logger.info("Reporting & Summaries Stage Complete.")