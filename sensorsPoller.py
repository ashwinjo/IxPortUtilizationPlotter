import time
import config
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from prometheus_client import start_http_server, Gauge

from RestApi.IxOSRestInterface import IxRestSession
from config import CHASSIS_LIST, POLLING_INTERVAL

load_dotenv()

# ==============================================================================
# PROMETHEUS METRIC DEFINITIONS
# ==============================================================================

# Temperature sensor metric (in Celsius)
sensor_temperature_celsius = Gauge(
    'ixos_sensor_temperature_celsius',
    'Temperature sensor reading in Celsius',
    ['chassis', 'sensor_name', 'sensor_type']
)

# Current/Amperage sensor metric (in Amperes)
sensor_current_amperes = Gauge(
    'ixos_sensor_current_amperes',
    'Current sensor reading in Amperes',
    ['chassis', 'sensor_name', 'sensor_type']
)

# Fan speed metric (as ratio 0-1, where 1 = 100%)
sensor_fan_speed_ratio = Gauge(
    'ixos_sensor_fan_speed_ratio',
    'Fan speed as ratio (0-1 where 1 = 100%)',
    ['chassis', 'sensor_name', 'sensor_type']
)


def get_sensor_information(session, chassis, type_chassis):
    """Method to get sensor information from Ixia Chassis using RestPy"""
    sensor_list = session.get_sensors().json()
    keys_to_remove = ["criticalValue", "maxValue", 'parentId', 'id','adapterName','minValue','sensorSetName', 'cpuName']
    for record in sensor_list:
        for item in keys_to_remove:
            record.pop(item, "NA")
        record.update({"chassisIp":chassis, "typeOfChassis": type_chassis, "lastUpdatedAt_UTC": datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")})
    return sensor_list


def update_prometheus_metrics(sensor_list):
    """Update Prometheus metrics from sensor data"""
    for sensor in sensor_list:
        chassis = sensor['chassisIp']
        sensor_name = sensor['name']
        sensor_type = sensor['type']
        unit = sensor['unit']
        value = sensor['value']
        
        # Route to appropriate metric based on unit type
        if unit == 'CELSIUS':
            sensor_temperature_celsius.labels(
                chassis=chassis,
                sensor_name=sensor_name,
                sensor_type=sensor_type
            ).set(value)
            
        elif unit == 'AMPERAGE':
            sensor_current_amperes.labels(
                chassis=chassis,
                sensor_name=sensor_name,
                sensor_type=sensor_type
            ).set(value)
            
        elif unit == 'PERCENTAGE':
            # Convert percentage (0-100) to ratio (0-1) for Prometheus best practice
            sensor_fan_speed_ratio.labels(
                chassis=chassis,
                sensor_name=sensor_name,
                sensor_type=sensor_type
            ).set(value / 100.0)


def poll_single_chassis(chassis):
    """
    Poll a single chassis for sensor information.
    
    Args:
        chassis (dict): Dictionary containing chassis ip, username, and password
        
    Returns:
        list: List of sensor dictionaries
    """
    try:
        session = IxRestSession(chassis['ip'], chassis['username'], chassis['password'])
        sensor_data = get_sensor_information(session, chassis['ip'], 'NA')
        return sensor_data
    except Exception as e:
        print(f"❌ Error polling chassis {chassis['ip']}: {e}")
        return []


def get_all_chassis_sensors():
    """
    Get sensor data from all chassis in parallel using ThreadPoolExecutor.
    This ensures all chassis are polled at approximately the same time.
    """
    if not CHASSIS_LIST:
        print("⚠️  No chassis configured in CHASSIS_LIST")
        return []
    
    all_sensors = []
    
    # Use ThreadPoolExecutor to poll all chassis in parallel
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
                sensor_data = future.result()
                if sensor_data:
                    all_sensors.extend(sensor_data)
                    
                    # Count sensor types for this chassis
                    cpu_temps = sum(1 for s in sensor_data if s['type'] == 'CPU' and s['unit'] == 'CELSIUS')
                    currents = sum(1 for s in sensor_data if s['unit'] == 'AMPERAGE')
                    fans = sum(1 for s in sensor_data if s['unit'] == 'PERCENTAGE')
                    
                    print(f"✓ {chassis['ip']}: {cpu_temps} temp sensors, {currents} current sensors, {fans} fan sensors")
            except Exception as e:
                print(f"❌ Exception processing chassis {chassis['ip']}: {e}")
    
    return all_sensors


# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

def main():
    """
    Main function to start the HTTP server and begin monitoring loop.
    """
    # Start the HTTP server to expose metrics on port 9002
    start_http_server(9002)
    
    print("=" * 70)
    print("Chassis Sensor Monitoring Service Started")
    print("=" * 70)
    print(f"Metrics endpoint: http://localhost:9002/metrics")
    print(f"Number of chassis: {len(CHASSIS_LIST)}")
    print(f"Monitoring interval: {POLLING_INTERVAL} seconds")
    print(f"Polling mode: Parallel (ThreadPoolExecutor)")
    print("=" * 70)
    print("\nPress Ctrl+C to stop.\n")
    
    # Main monitoring loop
    poll_count = 0
    while True:
        poll_count += 1
        print(f"\n[Poll #{poll_count}] Starting parallel chassis polling at {datetime.now().strftime('%H:%M:%S')}...")
        start_time = time.time()
        
        # Get sensor data from all chassis
        all_sensors = get_all_chassis_sensors()
        
        if all_sensors:
            # Update Prometheus metrics
            update_prometheus_metrics(all_sensors)
            print(f"✓ Updated Prometheus metrics: {len(all_sensors)} total sensors")
        
        elapsed_time = time.time() - start_time
        print(f"[Poll #{poll_count}] Completed in {elapsed_time:.2f} seconds")
        print(f"Next poll in {POLLING_INTERVAL} seconds...\n")
        
        time.sleep(POLLING_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSensor monitoring stopped by user (Ctrl+C). Exiting...")
