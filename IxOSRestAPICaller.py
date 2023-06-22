import json
import math
from datetime import datetime, timezone

def get_chassis_os(session):
    """Method to get Chassis Type based on IP from Chassis DB"""
    try:
        port_list = session.get_ports().data
        #linkState field is only in Linux Based Chassis
        if 'linkState' in  port_list[0]:
            return "Linux"
        return "Windows"
    except Exception:
        return "NA"

def convert_size(size_bytes):
    """Method to convert chassis size"""
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])

def get_perf_metrics(session, chassisIp):
    """Method to get Performance Metrics from Ixia Chassis"""
    chassis_perf_dict = {}
    # Exception Handling for Windows Chassis
    perf = {}
    try:
        perf = session.get_perfcounters().data[0]
    except Exception:
        pass
    
    mem_bytes = int(perf.get("memoryInUseBytes", "0"))
    mem_bytes_total = int(perf.get("memoryTotalBytes", "0"))
    cpu_pert_usage = perf.get("cpuUsagePercent", "0")
    if not mem_bytes_total:
        mem_util = 0
    else:
        mem_util = (mem_bytes/mem_bytes_total)*100
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    chassis_perf_dict.update({"chassisIp": chassisIp,
                              "mem_utilization": mem_util, 
                              "cpu_utilization": cpu_pert_usage,
                              "lastUpdatedAt_UTC": last_update_at})
    
    return chassis_perf_dict
    
def get_chassis_information(session):
    """ Fetch chassis information from RestPy
    We also get the perf counters in the same call
    """
    temp_dict = {}
    chassis_filter_dict = {}
    no_serial_string = ""
    mem_bytes = "NA"
    mem_bytes_total = "NA"
    cpu_pert_usage =  "NA"
    os = get_chassis_os(session)
    
    chassisInfo = session.get_chassis()
    try:
        # Exception Handling for Windows Chassis
        perf = session.get_perfcounters().data[0]
        mem_bytes = convert_size(perf["memoryInUseBytes"])
        mem_bytes_total = convert_size(perf["memoryTotalBytes"])
        cpu_pert_usage = perf["cpuUsagePercent"]
    except Exception:
       pass
        
    
    chassis_data = json.loads(json.dumps(chassisInfo.data[0]))
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    
    if chassis_data["type"] == "Ixia_Virtual_Test_Appliance":
        no_serial_string = "IxiaVM"
    
    chassis_filter_dict.update({ "chassisIp": chassis_data.get("managementIp"),
                                 "chassisSerial#": chassis_data.get("serialNumber", no_serial_string),
                                 "controllerSerial#": chassis_data.get("controllerSerialNumber", "NA"),
                                 "chassisType": chassis_data["type"].replace(" ", "_"),
                                 "physicalCards#": str(chassis_data.get("numberOfPhysicalCards", "NA")),
                                 "chassisStatus": chassis_data.get('state'),
                                 "lastUpdatedAt_UTC": last_update_at,
                                 "mem_bytes": mem_bytes, 
                                 "mem_bytes_total": mem_bytes_total, 
                                 "cpu_pert_usage": cpu_pert_usage,
                                 "os": os
                                })
    
    # List of Application on Ix CHhssis
    list_of_ixos_protocols = chassis_data["ixosApplications"]    
    for item in list_of_ixos_protocols:
        if item["name"] != "IxOS REST" or item["name"] != "LicenseServerPlus":
           temp_dict.update({item["name"]: item["version"]})
        
    chassis_filter_dict.update(temp_dict)
    return chassis_filter_dict
    
def get_chassis_cards_information(session, ip, type_of_chassis):
    """Method to get chassis card information from Ixia Chassis using RestPy"""
    card_list= session.get_cards().data
    final_card_details_list= []
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    # Cards on Chassis
    sorted_cards = sorted(card_list, key=lambda d: d['cardNumber'])
    
    
    for sc  in sorted_cards:
        final_card_details_list.append({"chassisIp": ip, 
                                        "chassisType": type_of_chassis,
                                        "cardNumber":sc.get("cardNumber"), 
                                        "serialNumber": sc.get("serialNumber"),
                                        "cardType": sc.get("type"),
                                        "cardState": sc.get("state"), 
                                        "numberOfPorts":sc.get("numberOfPorts", "No data"),
                                        "lastUpdatedAt_UTC": last_update_at
                                        })
    return final_card_details_list
    
def get_chassis_ports_information(session, chassisIp, chassisType):
    """Method to get chassis port information from Ixia Chassis using RestPy"""
    port_data_list = []
    used_port_details = []
    total_ports = 0
    used_ports = 0
    
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    port_list = session.get_ports().data
    
    keys_to_keep = ['owner', 'transceiverModel', 'transceiverManufacturer', 'cardNumber', 'portNumber', 'phyMode', 'linkState', 'speed', 'type', 'transmitState']

    if port_list:
        a = list(port_list[0].keys())
    else:
        a = []
    keys_to_remove = [x for x in a if x not in keys_to_keep]
    # Removing the extra keys from port details json response
    for port_data in port_list:
        if not port_data.get("owner"):
            port_data["owner"] = "Free"
            
        for k in keys_to_remove:
            port_data.pop(k)
    
    for port in port_list:
        port_data_list.append(port)
    
    # Lets get used ports, free ports and total ports
    if port_data_list:
        used_port_details = [item for item in port_data_list if item.get("owner")]
        total_ports = len(port_list)
        used_ports = len(used_port_details)
        
    
    
    for port_data_list_item in port_data_list:
        port_data_list_item.update({
                                "lastUpdatedAt_UTC": last_update_at,
                                "totalPorts": total_ports,
                                "ownedPorts": used_ports, 
                                "freePorts": (total_ports-used_ports),
                                "chassisIp": chassisIp,
                                "typeOfChassis": chassisType })
    return port_data_list

        
def get_license_activation(session, ip, type_chassis):
    """Method to get license information from Ixia Chassis using RestPy"""
    host_id = session.get_license_server_host_id()
    license_info = session.get_license_activation().json()
    last_update_at = datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")
    license_info_list= []
    for item in license_info:
        license_info_list.append({
                "chassisIp": ip,
                "typeOfChassis": type_chassis,
                "hostId": host_id,
                "partNumber": item["partNumber"],
                "activationCode": item["activationCode"], 
                "quantity": item["quantity"], 
                "description": item["description"].replace(",","_"),
                "maintenanceDate": item["maintenanceDate"], 
                "expiryDate": item["expiryDate"],
                "isExpired": str(item.get("isExpired", "NA")),
                "lastUpdatedAt_UTC": last_update_at})
    return license_info_list


def get_sensor_information(session, chassis, type_chassis):
    """Method to get sensor information from Ixia Chassis using RestPy"""
    sensor_list = session.get_sensors().json()
    keys_to_remove = ["criticalValue", "maxValue", 'parentId', 'id','adapterName','minValue','sensorSetName', 'cpuName']
    for record in sensor_list:
        for item in keys_to_remove:
            record.pop(item, "NA")
        record.update({"chassisIp":chassis, "typeOfChassis": type_chassis, "lastUpdatedAt_UTC": datetime.now(timezone.utc).strftime("%m/%d/%Y, %H:%M:%S")})
    return sensor_list