import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import time
import random
from config import INFLUXDB_TOKEN, INFLUXDB_URL

# InfluxDB Configuration

bucket = "ixosChassisStatistics"
org = "keysight"
token = INFLUXDB_TOKEN
# Store the URL of your InfluxDB instance
url=INFLUXDB_URL


client = influxdb_client.InfluxDBClient(
   url=url,
   token=token,
   org=org
)


def write_data_to_influxdb(port_list_details):
    """Write data to InfluxDB portUtilization measurement"""

    write_api = client.write_api(write_options=SYNCHRONOUS)
    for port_detail in port_list_details:
        try:
            # Convert values to ensure consistent types
            # Tags must be strings - cardNumber and portNumber are explicitly strings
            chassis_tag = str(port_detail["chassisIp"])
            card_tag = str(port_detail["cardNumber"])  # Explicitly string
            port_tag = str(port_detail["fullyQualifiedPortName"])  # Explicitly string
            
            # Convert transmitState boolean to string to avoid type conflicts
            transmit_state = port_detail["transmitState"]
            if isinstance(transmit_state, bool):
                transmit_state_str = "active" if transmit_state else "idle"
            else:
                transmit_state_str = str(transmit_state)
            
            # Ensure numeric fields are integers
            total_ports = int(port_detail["totalPorts"]) if port_detail["totalPorts"] != "NA" else 0
            owned_ports = int(port_detail["ownedPorts"]) if port_detail["ownedPorts"] != "NA" else 0
            free_ports = int(port_detail["freePorts"]) if port_detail["freePorts"] != "NA" else 0
            
            p = influxdb_client.Point("portUtilization")\
                .tag("chassis", chassis_tag)\
                .tag("card", card_tag)\
                .tag("port", port_tag)\
                .field("cardNumber", card_tag)\
                .field("portNumber", port_tag)\
                .field("owner", str(port_detail["owner"]))\
                .field("linkState", str(port_detail["linkState"]))\
                .field("transmitState", transmit_state_str)\
                .field("totalPorts", total_ports)\
                .field("ownedPorts", owned_ports)\
                .field("freePorts", free_ports)
            
            # Actually write the point to InfluxDB
            write_api.write(bucket=bucket, org=org, record=p)
            print(f"✓ Written: {chassis_tag}/{card_tag}/{port_tag} -> Owner={port_detail['owner']}, LinkState={port_detail['linkState']}, TransmitState={transmit_state_str}")
        except Exception as e:
            print(f"✗ Error writing data for {port_detail.get('chassisIp', 'unknown')}/{port_detail.get('cardNumber', 'unknown')}/{port_detail.get('portNumber', 'unknown')}: {e}")



def query_data():
    query_api = client.query_api()
    query = f'''
    from(bucket: "{bucket}")
        |> range(start: -1h)
        |> filter(fn: (r) => r["_measurement"] == "portUtilization")
        |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
    '''
    
    result = query_api.query(org=org, query=query)
    
    # Process and display results in row format
    print(f"\n{'='*120}")
    print(f"MEASUREMENT: portUtilization")
    print(f"{'='*120}")
    
    # Print header
    if result and result[0].records:
        first_record = result[0].records[0]
        print(f"\n{'Time':<30} {'Chassis':<18} {'Card':<6} {'Port':<6} {'Owner':<15} {'LinkState':<10} {'TransmitState':<12} {'Total':<6} {'Owned':<6} {'Free':<6}")
        print("-" * 120)
    
    # Print each row
    for table in result:
        for record in table.records:
            time_str = str(record.get_time())[:19]  # Truncate microseconds
            chassis = record.values.get("chassis", "N/A")
            card = record.values.get("card", "N/A")
            port = record.values.get("port", "N/A")
            owner = record.values.get("owner", "N/A")
            link_state = record.values.get("linkState", "N/A")
            transmit_state = record.values.get("transmitState", "N/A")
            total_ports = record.values.get("totalPorts", "N/A")
            owned_ports = record.values.get("ownedPorts", "N/A")
            free_ports = record.values.get("freePorts", "N/A")
            
            print(f"{time_str:<30} {chassis:<18} {card:<6} {port:<6} {owner:<15} {link_state:<10} {transmit_state:<12} {total_ports:<6} {owned_ports:<6} {free_ports:<6}")
    
    print(f"{'='*120}\n")
    
    return result

def delete_measurement_data():
    """Delete all data from portUtilization measurement"""
    delete_api = client.delete_api()
    
    start = "1970-01-01T00:00:00Z"  # Beginning of time
    stop = "2099-12-31T23:59:59Z"   # Far future
    
    delete_api.delete(
        start=start,
        stop=stop,
        predicate='_measurement="portUtilization"',
        bucket=bucket,
        org=org
    )
    print("All data from 'portUtilization' measurement deleted successfully!")



if __name__ == "__main__":
    # Uncomment the functions you want to run:
    #delete_measurement_data()  # Run first to clear old data
    #write_data()               # Then write new data with Power Rangers owners
    
    # Test the connection first
    #test_write_and_query()
    pass
    
    # Or just query existing data
    query_data()               # Query and display the data