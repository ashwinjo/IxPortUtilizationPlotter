import time
import config
import logging
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

from RestApi.IxOSRestInterface import IxRestSession
from influxDBclient import write_data_to_influxdb
from config import POLLING_INTERVAL

load_dotenv()


def fetch_blocked_ports():
    """Fetch blocked ports from the blocked-ports API once per poll cycle.

    Returns:
        set of (chassis_ip, "card.port") tuples, e.g. {("10.36.236.121", "4.7")}
        Returns empty set if API is unreachable (fallback: owned ports -> Utilized).
    """
    try:
        url = config.BLOCKED_PORTS_URL
        if "?" in url:
            url += "&refresh=true"
        else:
            url += "?refresh=true"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            blocked = set()
            for entry in data.get("ports", []):
                blocked.add((entry["chassis"], entry["port"]))
            print(f"✓ Blocked ports fetched: {len(blocked)} ports")
            return blocked
    except Exception as e:
        print(f"⚠ Blocked ports API unreachable ({e}), defaulting owned ports to 'Utilized'")
    return set()


def get_chassis_ports_information(session, chassisIp, chassisType, blocked_ports=None):
    if blocked_ports is None:
        blocked_ports = set()
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

    # Setting up Owner, portStatus, and blocked
    for port_data in port_list:
        raw_owner = port_data.get("owner", "")
        if not raw_owner:
            port_data["owner"] = "Free"
            port_data["portStatus"] = "Free"
            port_data["blocked"] = False
        else:
            port_key = f"{port_data['cardNumber']}.{port_data['portNumber']}"
            if (chassisIp, port_key) in blocked_ports:
                port_data["portStatus"] = "Blocked"
                port_data["blocked"] = True
            else:
                port_data["portStatus"] = "Utilized"
                port_data["blocked"] = False

        for k in keys_to_remove:
            port_data.pop(k, None)  # Use None as default to avoid KeyError if key doesn't exist
    
    # Creating the final port information list
    for port in port_list:
        port_data_list.append(port)
    
    # Lets get used ports, free ports and total ports
    if port_data_list:
        used_port_details = [item for item in port_data_list if item.get("owner") != "Free"]
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


def poll_single_chassis(chassis, blocked_ports=None):
    """Poll a single chassis and return its port data

    Args:
        chassis: Dictionary with 'ip', 'username', 'password'
        blocked_ports: set of (chassis_ip, "card.port") tuples from fetch_blocked_ports()

    Returns:
        List of port details for this chassis
    """
    if blocked_ports is None:
        blocked_ports = set()
    try:
        session = IxRestSession(
            chassis["ip"],
            chassis["username"],
            chassis["password"],
            verbose=False)

        port_list_details = get_chassis_ports_information(
            session,
            chassis["ip"],
            "NA",
            blocked_ports)
        
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
            'transmitState': 'NA',
            'blocked': False
        }]


def get_chassis_port_data():
    """Poll all chassis in parallel to get synchronized timestamps
    
    Returns:
        Combined list of port details from all chassis
    """
    all_port_details = []
    
    chassis_list = config.get_chassis_list()
    if not chassis_list:
        return all_port_details

    # Fetch blocked ports ONCE for the entire poll cycle
    blocked_ports = fetch_blocked_ports()

    # Use ThreadPoolExecutor to poll all chassis simultaneously
    with ThreadPoolExecutor(max_workers=len(chassis_list)) as executor:
        # Submit all chassis polling tasks
        future_to_chassis = {
            executor.submit(poll_single_chassis, chassis, blocked_ports): chassis
            for chassis in chassis_list
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

    import os
    dry_run = os.getenv('DRY_RUN', '').lower() in ('1', 'true', 'yes')

    # Start parallel chassis poller
    print(f"Starting parallel chassis poller (credentials service: {config._CREDENTIALS_URL})")
    print(f"Polling interval: {config.POLLING_INTERVAL} seconds")
    if dry_run:
        print("DRY RUN -- InfluxDB writes skipped")
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
            if dry_run:
                for port_detail in port_list_details:
                    chassis_tag = str(port_detail["chassisIp"])
                    card_tag = str(port_detail["cardNumber"])
                    if port_detail.get("fullyQualifiedPortName", "N/A") == "N/A":
                        port_tag = str(port_detail["portNumber"])
                    else:
                        port_tag = str(port_detail["fullyQualifiedPortName"])
                    transmit_state = port_detail["transmitState"]
                    if isinstance(transmit_state, bool):
                        transmit_state_str = "active" if transmit_state else "idle"
                    else:
                        transmit_state_str = str(transmit_state)
                    print(f"[DRY RUN] ✓ Would write: {chassis_tag}/{card_tag}/{port_tag} -> Owner={port_detail['owner']}, LinkState={port_detail['linkState']}, TransmitState={transmit_state_str}, Blocked={port_detail.get('blocked', False)}, portStatus={port_detail.get('portStatus', 'Utilized')}")
            else:
                write_data_to_influxdb(port_list_details)
                print(f"[Poll #{poll_count}] Written to InfluxDB")
        else:
            print(f"[Poll #{poll_count}] No data collected")

        # Wait for next polling interval
        time.sleep(POLLING_INTERVAL)
        print("-" * 80)
