import time
import config
import logging

from datetime import datetime
import mysql.connector

import IxOSRestAPICaller as ixOSRestCaller
from RestApi.IxOSRestInterface import IxRestSession


def write_data_to_database(records=None, date_string=None):

    # Connect to MySQL
    cnx = mysql.connector.connect(
        host=config.MYSQL_ENDPOINT,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASS,
        database=config.MYSQL_DB
    )

    # Create a cursor object to execute queries
    cur = cnx.cursor()

    # Insert a record into the database
    for rcd in records[0]:
        ts = 0
        if rcd.get('transmitState','NA'):
            ts = 1
        query = f"""INSERT INTO chassis_port_details (chassisIp,    
                                                      typeOfChassis,
                                                      cardNumber,
                                                      portNumber,
                                                      linkState,
                                                      phyMode,
                                                      transceiverModel,
                                                      transceiverManufacturer,
                                                      owner, 
                                                      speed, 
                                                      type, 
                                                      totalPorts,
                                                      ownedPorts,
                                                      freePorts, 
                                                      transmitState, 
                                                      lastUpdatedAt_UTC) VALUES 
                        ('{rcd["chassisIp"]}', '{rcd["typeOfChassis"]}', '{rcd["cardNumber"]}','{rcd["portNumber"]}','{rcd.get("linkState", "NA")}',
                        '{rcd.get("phyMode","NA")}','{rcd.get("transceiverModel", "NA")}', '{rcd.get("transceiverManufacturer", "NA")}','{rcd["owner"]}',
                        '{rcd.get("speed", "NA")}','{rcd.get("type", "NA")}','{rcd["totalPorts"]}','{rcd["ownedPorts"]}', '{rcd["freePorts"]}','{ts}', 
                        '{date_string}')"""
        
        cur.execute(query)
        
    cnx.commit()

    # Close the cursor and connection
    cur.close()
    cnx.close()


def get_chassis_port_data(date_string):
    """This is a call to RestAPI to get chassis card port summary data
    """
    port_list_details = []
    if config.CHASSIS_LIST:
        for chassis in config.CHASSIS_LIST:
            try:
                session = IxRestSession(
                    chassis["ip"], chassis["username"], chassis["password"], verbose=False)
                out = ixOSRestCaller.get_chassis_ports_information(session, chassis["ip"], "NA")
                port_list_details.append(out)
            except Exception:
                a = [{
                    'owner': 'NA',
                    'transceiverModel': 'NA',
                    'transceiverManufacturer': 'NA',
                    'portNumber': 'NA',
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
                port_list_details.append(a)
        write_data_to_database(records=port_list_details, date_string=date_string)


if __name__ == '__main__':
    while True:
        current_datetime=datetime.utcnow()
        date_string = current_datetime.strftime('%Y-%m-%d %H:%M:%S')
        logging.basicConfig(level=logging.INFO)
        logging.info(date_string)
        get_chassis_port_data(date_string)
        time.sleep(config.POLLING_INTERVAL)
