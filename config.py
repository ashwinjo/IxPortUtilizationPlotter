"""
Configuration for IxOS Port Utilization Poller

This module supports both direct configuration and environment variables.
Environment variables take precedence if set (useful for Docker deployment).
"""

import os
import json
import requests
import dotenv

dotenv.load_dotenv()

# =============================================================================
# CHASSIS CONFIGURATION
# =============================================================================

_CREDENTIALS_URL = os.getenv(
    'CREDENTIALS_URL',
    'http://host.docker.internal:3001/api/config/credentials'
)

def _fetch_chassis_from_api():
    """Try to fetch chassis credentials from IxiaInventoryExplorer API.
    Returns list of {ip, username, password} dicts, or None on failure."""
    try:
        resp = requests.get(_CREDENTIALS_URL, timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('success') and data.get('credentials'):
                print(f"✓ Loaded {data['count']} chassis from {_CREDENTIALS_URL}")
                return data['credentials']
    except Exception:
        pass
    return None


# Priority 1: IxiaInventoryExplorer API
_api_chassis = _fetch_chassis_from_api()
if _api_chassis:
    CHASSIS_LIST = _api_chassis

# Priority 2: CHASSIS_LIST environment variable
elif os.getenv('CHASSIS_LIST', ''):
    _chassis_env = os.getenv('CHASSIS_LIST', '')
    try:
        CHASSIS_LIST = json.loads(_chassis_env)
        print(f"✓ Loaded {len(CHASSIS_LIST)} chassis from CHASSIS_LIST env var")
    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Invalid CHASSIS_LIST JSON in environment variable: {e}")
        CHASSIS_LIST = []

# Priority 3: No chassis configured
else:
    print(f"⚠️  API unreachable and CHASSIS_LIST not set — no chassis will be polled.")
    print(f"    Set CHASSIS_LIST env var or run the credentials service at {_CREDENTIALS_URL}")
    CHASSIS_LIST = []

def get_chassis_list():
    """Fetch chassis list from credentials service each call.
    Falls back to CHASSIS_LIST (env var or hardcoded) if service unreachable."""
    result = _fetch_chassis_from_api()
    return result if result else CHASSIS_LIST


# =============================================================================
# POLLING CONFIGURATION
# =============================================================================

# Polling interval in seconds (how often to query chassis)
POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '10'))
POLLING_INTERVAL_PERF_METRICS = int(os.getenv('POLLING_INTERVAL_PERF_METRICS', '60'))

# =============================================================================
# INFLUXDB CONFIGURATION
# =============================================================================

# InfluxDB URL (use 'influxdb' hostname in Docker, 'localhost' outside Docker)
INFLUXDB_URL = os.getenv(
    'INFLUXDB_URL',
    'http://localhost:8086'
)

# InfluxDB API Token (required for authentication)
INFLUXDB_TOKEN = os.getenv(
    'INFLUXDB_TOKEN',
    'eegHpR9kkgxg5KG7rklj2zQI86-5z7yNETx0P0qQpSnw1owDxSL5IF-uQruOP-J8M_xmrhT3KWECh-QGbsdyYA=='
)

# InfluxDB Organization (optional, defaults in influxDBclient.py)
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG', 'keysight')

# InfluxDB Bucket (optional, defaults in influxDBclient.py)
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET', 'portBlockedMetrics')

# =============================================================================
# BLOCKED PORTS API CONFIGURATION
# =============================================================================

# URL for the blocked ports API (IxPortUtilizationAuditor or similar)
# Returns ports actively locked in IxNetwork sessions
BLOCKED_PORTS_URL = os.getenv(
    'BLOCKED_PORTS_URL',
    'http://localhost:8890/api/v1/ports/blocked'
)

# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

def validate_config():
    """Validate configuration and print warnings if needed"""
    issues = []
    
    if not CHASSIS_LIST:
        issues.append("⚠️  CHASSIS_LIST is empty! No chassis will be polled.")
    
    if not INFLUXDB_TOKEN or INFLUXDB_TOKEN == 'your-super-secret-token-change-me':
        issues.append("⚠️  INFLUXDB_TOKEN not properly configured!")
    
    if POLLING_INTERVAL < 5:
        issues.append(f"⚠️  POLLING_INTERVAL ({POLLING_INTERVAL}s) is very low. Recommended: 10s or higher.")
    
    return issues

# =============================================================================
# CONFIGURATION INFO
# =============================================================================

def print_config():
    """Print current configuration (for debugging)"""
    print("=" * 80)
    print("CONFIGURATION")
    print("=" * 80)
    print(f"Chassis Count: {len(CHASSIS_LIST)}")
    if CHASSIS_LIST:
        print("Chassis IPs:")
        for chassis in CHASSIS_LIST:
            print(f"  - {chassis.get('ip', 'N/A')}")
    print(f"Polling Interval: {POLLING_INTERVAL} seconds for InfluxDB Polling")
    print(f"Polling Interval: {POLLING_INTERVAL_PERF_METRICS} seconds for Performance Metrics Polling")
    print(f"InfluxDB URL: {INFLUXDB_URL}")
    print(f"InfluxDB Org: {INFLUXDB_ORG}")
    print(f"InfluxDB Bucket: {INFLUXDB_BUCKET}")
    print(f"InfluxDB Token: {'*' * 20}...{INFLUXDB_TOKEN[-10:] if len(INFLUXDB_TOKEN) > 10 else '***'}")
    print("=" * 80)
    
    # Print any configuration warnings
    issues = validate_config()
    if issues:
        print("\n⚠️  CONFIGURATION WARNINGS:")
        for issue in issues:
            print(f"   {issue}")
        print()

if __name__ == "__main__":
    print_config()
