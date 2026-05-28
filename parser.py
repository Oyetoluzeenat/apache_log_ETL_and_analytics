import re
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Comprehensive Regex for Apache Combined Log format matching all 9 required fields
APACHE_REGEX = re.compile(
    r'^(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'              # 1. IP Address
    r'\s+-\s+-\s+\['                                            # Skip identity fields
    r'(?P<timestamp>[^\]]+)\]'                                  # 2. Timestamp
    r'\s+"(?P<method>[A-Z]+)'                                   # 3. HTTP Method
    r'\s+(?P<resource_path>[^\s"]+)'                            # 4. Resource Path
    r'\s+(?P<protocol>HTTP/\d\.\d)"'                            # 5. Protocol
    r'\s+(?P<status_code>\d{3})'                                # 6. Status Code
    r'\s+(?P<bytes_sent>\d+|-)'                                 # 7. Bytes Sent
    r'\s+"(?P<referrer>[^"]*)"'                                 # 8. Referrer
    r'\s+"(?P<user_agent>[^"]*)"'                               # 9. User-Agent
)

# Set of processed record hashes to enforce deduplication in memory
_processed_hashes = set()

def validate_data(timestamp_str, status_code_str):
    """Validates the timestamp format and HTTP status code correctness."""
    # 1. Validate Timestamp format (e.g., 17/May/2015:10:05:03 +0000)
    try:
        # Strip timezone offset for simplified core validation check
        core_time = timestamp_str.split(' ')[0]
        datetime.strptime(core_time, "%d/%b/%Y:%H:%M:%S")
    except ValueError:
        logger.error(f"Validation Failed: Invalid timestamp structure '{timestamp_str}'")
        return False

    # 2. Validate HTTP Status Code (Must be a 3-digit number between 100 and 599)
    if not status_code_str.isdigit() or not (100 <= int(status_code_str) <= 599):
        logger.error(f"Validation Failed: Invalid status code '{status_code_str}'")
        return False

    return True

def generate_dedup_hash(ip, timestamp, endpoint):
    """Creates a unique MD5 hash signature for deduplication based on IP + timestamp + endpoint."""
    unique_string = f"{ip}|{timestamp}|{endpoint}"
    return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

def parse_log_line(raw_line):
    """
    TRANSFORM STAGE:
    Extracts 9 fields via Regex, validates data formats, and filters out duplicates.
    """
    match = APACHE_REGEX.match(raw_line)
    if not match:
        return None

    fields = match.groupdict()

    # --- VALIDATION LAYER ---
    if not validate_data(fields['timestamp'], fields['status_code']):
        return None  # Drop record if validation fails

    # --- DEDUPLICATION LAYER ---
    # Assignment rule: Deduplicate using hash of IP + timestamp + endpoint (resource_path)
    record_hash = generate_dedup_hash(fields['ip'], fields['timestamp'], fields['resource_path'])
    
    if record_hash in _processed_hashes:
        logger.debug(f"Duplicate record dropped: {fields['ip']} at {fields['timestamp']}")
        return None # Skip duplicate log entry
        
    _processed_hashes.add(record_hash)

    # Clean up data types
    fields['status_code'] = int(fields['status_code'])
    fields['bytes_sent'] = 0 if fields['bytes_sent'] == '-' else int(fields['bytes_sent'])
    
    return fields

def transform_batch(raw_lines):
    """Processes an array of raw strings and returns valid dicts and malformed lines."""
    valid_records = []
    malformed_records = []
    
    for line in raw_lines:
        clean_line = line.strip()
        if not clean_line:
            continue
        
        record = parse_log_line(clean_line)
        if record:
            valid_records.append(record)
        else:
            malformed_records.append((clean_line, "Regex match failed or validation anomaly"))
            
    return valid_records, malformed_records