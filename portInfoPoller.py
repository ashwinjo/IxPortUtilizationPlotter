import time
import config
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from RestApi.IxOSRestInterface import IxRestSession
from influxDBclient import write_data_to_influxdb
from config import POLLING_INTERVAL

load_dotenv()

def get_chassis_ports_information(session, chassisIp, chassisType):
    """Method to get chassis port information from Ixia Chassis using RestPy"""
    port_data_list = [] # Final port information list
    used_port_details = []
    total_ports = 0
    used_ports = 0
    
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    port_list = session.get_ports().data
    
    keys_to_keep = ['owner', 
                    'cardNumber', 
                    'portNumber',
                    'fullyQualifiedPortName', 
                    'linkState', 
                    'transmitState']

    a = []
    if port_list:
        a = list(port_list[0].keys())
        
    # Removing the extra keys from port details json response
    keys_to_remove = [x for x in a if x not in keys_to_keep]

    # Setting up Owner
    for port_data in port_list:
        if not port_data.get("owner"):
            port_data["owner"] = "Free"
            
        for k in keys_to_remove:
            port_data.pop(k, None)  # Use None as default to avoid KeyError if key doesn't exist
    
    # Creating the final port information list
    for port in port_list:
        port_data_list.append(port)
    
    # Lets get used ports, free ports and total ports
    if port_data_list:
        used_port_details = [item for item in port_data_list if item.get("owner")]
        total_ports = len(port_list)
        used_ports = len(used_port_details)
        
    
    # Updating the final port information list with total ports, used ports and free ports
    for port_data_list_item in port_data_list:
        port_data_list_item.update({
                                "lastUpdatedAt_UTC": last_update_at,
                                "totalPorts": total_ports,
                                "ownedPorts": used_ports, 
                                "freePorts": (total_ports-used_ports),
                                "chassisIp": chassisIp,
                                "typeOfChassis": chassisType })
    return port_data_list # Final port information list


def poll_single_chassis(chassis):
    """Poll a single chassis and return its port data
    
    Args:
        chassis: Dictionary with 'ip', 'username', 'password'
    
    Returns:
        List of port details for this chassis
    """
    try:
        session = IxRestSession(
            chassis["ip"], 
            chassis["username"], 
            chassis["password"], 
            verbose=False)
        
        port_list_details = get_chassis_ports_information(
            session, 
            chassis["ip"], 
            "NA")
        
        print(f"✓ Successfully polled {chassis['ip']} - {len(port_list_details)} ports")
        return port_list_details
        
    except Exception as e:
        print(f"✗ Error polling {chassis['ip']}: {e}")
        # Return error placeholder data
        return [{
            'owner': 'NA',
            'transceiverModel': 'NA',
            'transceiverManufacturer': 'NA',
            'portNumber': 'NA',
            'portName': 'NA',
            'fullyQualifiedPortName': 'NA',
            'linkState': 'NA',
            'cardNumber': 'NA',
            'lastUpdatedAt_UTC': 'NA',
            'totalPorts': 'NA',
            'ownedPorts': 'NA',
            'freePorts': 'NA',
            'chassisIp': chassis["ip"],
            'typeOfChassis': 'NA',
            'transmitState': 'NA'
        }]


def get_chassis_port_data():
    """Poll all chassis in parallel to get synchronized timestamps
    
    Returns:
        Combined list of port details from all chassis
    """
    all_port_details = []
    
    if not config.CHASSIS_LIST:
        return all_port_details
    
    # Use ThreadPoolExecutor to poll all chassis simultaneously
    # max_workers=None will use (number of processors) * 5 threads
    # For 10 chassis, you can also set max_workers=10 explicitly
    with ThreadPoolExecutor(max_workers=len(config.CHASSIS_LIST)) as executor:
        # Submit all chassis polling tasks
        future_to_chassis = {
            executor.submit(poll_single_chassis, chassis): chassis 
            for chassis in config.CHASSIS_LIST
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_chassis):
            chassis = future_to_chassis[future]
            try:
                port_details = future.result()
                all_port_details.extend(port_details)
            except Exception as e:
                print(f"✗ Unexpected error for {chassis['ip']}: {e}")

    return all_port_details


if __name__ == '__main__':
    # OPTIONAL: Uncomment below to delete all historical data on startup (use with caution!)
    # print("Deleting all data from InfluxDB measurement...")
    # delete_measurement_data()
    
    # Start parallel chassis poller
    print(f"Starting parallel chassis poller for {len(config.CHASSIS_LIST)} chassis...")
    print(f"Polling interval: {config.POLLING_INTERVAL} seconds")
    print(f"Chassis IPs: {[c['ip'] for c in config.CHASSIS_LIST]}")
    print("-" * 80)
    
    poll_count = 0
    while True:
        poll_count += 1
        start_time = time.time()
        
        print(f"\n[Poll #{poll_count}] Starting parallel poll at {datetime.now().strftime('%H:%M:%S')}")
        
        # Poll all chassis in parallel
        port_list_details = get_chassis_port_data()
        
        poll_duration = time.time() - start_time
        print(f"[Poll #{poll_count}] Collected {len(port_list_details)} total ports in {poll_duration:.2f}s")
        
        # Write all data to InfluxDB (synchronized timestamps)
        if port_list_details:
            write_data_to_influxdb(port_list_details)
            print(f"[Poll #{poll_count}] Written to InfluxDB")
        else:
            print(f"[Poll #{poll_count}] ⚠ No data collected")
        
        # Wait for next polling interval
        time.sleep(POLLING_INTERVAL)
        print("-" * 80)
