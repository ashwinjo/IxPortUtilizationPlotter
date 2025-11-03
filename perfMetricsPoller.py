import time
import json
# Load .env file if it exists
from dotenv import load_dotenv
 
from concurrent.futures import ThreadPoolExecutor, as_completed
from IxOSRestAPICaller import get_perf_metrics
from prometheus_client import start_http_server, Gauge
from RestApi.IxOSRestInterface import IxRestSession
from config import CHASSIS_LIST, POLLING_INTERVAL_PERF_METRICS

load_dotenv()
# ==============================================================================
# METRIC DEFINITIONS
# ==============================================================================

memory_utilization = Gauge(
    'memory_utilization',
    'Memory utilization of the chassis',
    ['chassis']
)


cpu_utilization = Gauge(
    'cpu_utilization',
    'CPU utilization of the chassis',
    ['chassis']
)


def poll_single_chassis(chassis):
    """
    Poll a single chassis for metrics.
    
    Args:
        chassis (dict): Dictionary containing chassis ip, username, and password
        
    Returns:
        dict: Chassis metrics including IP, memory utilization, and CPU utilization
    """
    try:
        session = IxRestSession(chassis['ip'], chassis['username'], chassis['password'])
        chassis_metrics = get_perf_metrics(session, chassis['ip'])
        return chassis_metrics
    except Exception as e:
        print(f"❌ Error polling chassis {chassis['ip']}: {e}")
        return None


def get_chassis_metrics():
    """
    Get chassis metrics from all chassis in parallel using ThreadPoolExecutor.
    This ensures all chassis are polled at approximately the same time.
    """
    if not CHASSIS_LIST:
        print("⚠️  No chassis configured in CHASSIS_LIST")
        return
    
    # Use ThreadPoolExecutor to poll all chassis in parallel
    # max_workers=None means it will default to min(32, num_chassis + 4)
    with ThreadPoolExecutor(max_workers=len(CHASSIS_LIST)) as executor:
        # Submit all polling tasks
        future_to_chassis = {
            executor.submit(poll_single_chassis, chassis): chassis 
            for chassis in CHASSIS_LIST
        }
        
        # Process results as they complete
        for future in as_completed(future_to_chassis):
            chassis = future_to_chassis[future]
            try:
                chassis_metrics = future.result()
                if chassis_metrics:
                    print(f"✓ {chassis_metrics['chassisIp']}: "
                          f"CPU={chassis_metrics['cpu_utilization']}%, "
                          f"MEM={chassis_metrics['mem_utilization']:.2f}%")
                    
                    # Update Prometheus metrics
                    memory_utilization.labels(chassis_metrics['chassisIp']).set(
                        chassis_metrics['mem_utilization']
                    )
                    cpu_utilization.labels(chassis_metrics['chassisIp']).set(
                        chassis_metrics['cpu_utilization']
                    )
            except Exception as e:
                print(f"❌ Exception processing chassis {chassis['ip']}: {e}")

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

def main():
    """
    Main function to start the HTTP server and begin monitoring loop.
    """
    # Start the HTTP server to expose metrics on port 9001
    start_http_server(9001)
    
    print("=" * 70)
    print("Chassis Performance Monitoring Service Started")
    print("=" * 70)
    print(f"Metrics endpoint: http://localhost:9001/metrics")
    print(f"Number of chassis: {len(CHASSIS_LIST)}")
    print(f"Polling mode: Parallel (ThreadPoolExecutor)")
    print(f"Monitoring interval: 110 seconds")
    print("=" * 70)
    print("\nPress Ctrl+C to stop.\n")
    
    # Main monitoring loop - runs every 110 seconds
    poll_count = 0
    while True:
        poll_count += 1
        print(f"\n[Poll #{poll_count}] Starting parallel chassis polling...")
        start_time = time.time()
        
        get_chassis_metrics()
        
        elapsed_time = time.time() - start_time
        print(f"[Poll #{poll_count}] Completed in {elapsed_time:.2f} seconds")
        print(f"Next poll in 110 seconds...\n")
        
        time.sleep(POLLING_INTERVAL_PERF_METRICS)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nLoop stopped by user (Ctrl+C). Exiting.")