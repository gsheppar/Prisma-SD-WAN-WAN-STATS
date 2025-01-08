#!/usr/bin/env python3
import argparse
from prisma_sase import API, jd, jd_detailed, jdout
import prismasase_settings
import sys
import logging
import logging.handlers as handlers
import os
import datetime
import os
from datetime import datetime, timedelta
import time
import pytz
import csv
from csv import DictReader

# Global Vars
TIME_BETWEEN_API_UPDATES = 60       # seconds
REFRESH_LOGIN_TOKEN_INTERVAL = 7    # hours
SCRIPT_NAME = 'CloudGenix: Example script: WAN Interface Script'
SCRIPT_VERSION = "v1"

####################################################################
# Read cloudgenix_settings file for auth token or username/password
####################################################################

sys.path.append(os.getcwd())

def run_reports(cgx, start_date_iso, end_date_iso):
    print("Starting the interface stats script")    
    print("Start time: " + start_date_iso)
    print("End time: " + end_date_iso)
    
    data_set_list = []
    
    nework_id2n = {}
    for network in cgx.get.wannetworks().cgx_content['items']:
        nework_id2n[network["id"]] = network["name"]  
    
    element_data = cgx.get.elements().cgx_content["items"]
    
    for site in cgx.get.sites().cgx_content["items"]:
        if site["element_cluster_role"] == "SPOKE":
            print("Checking site " + site["name"])
            site_id = site["id"]
            ha_element_id = None
            status = cgx.get.spokeclusters(site_id=site_id).cgx_content["items"]
            if status:    
                spokecluster_id = status[0]["id"]
                for ion in cgx.get.spokeclusters_status(site_id=site_id, spokecluster_id=spokecluster_id).cgx_content["cluster_members"]:
                    if ion["status"] == "active":
                        ha_element_id = ion["element_id"]                   
            for element in element_data:
                if element["site_id"] == site_id and ha_element_id == None or ha_element_id == element["id"]:
                    element_id = element["id"]
                    site_name = site["name"]
                    element_name = element["name"]
                    try:
                        for interface in cgx.get.interfaces(site_id=site_id, element_id=element_id).cgx_content['items']:
                            if interface["type"] != "bypasspair":
                                if interface["site_wan_interface_ids"]:
                                    print("Checking metrics for interface:  " + interface["name"])
                                    circuit_name = None
                                    bw_up = None
                                    bw_down = None            
                                    for wan in cgx.get.waninterfaces(site_id=site_id).cgx_content['items']:
                                        if wan["id"] == interface["site_wan_interface_ids"][0]:
                                            if wan["name"] == None:
                                                circuit_name = nework_id2n[wan["network_id"]]
                                            else:
                                                circuit_name = wan["name"]
                                            bw_down = wan["link_bw_down"]
                                            bw_up = wan["link_bw_up"]
                                                               
                        
                                    interface_id = interface["id"]
                        
                                    data_set_egress = []
                                    data_set_ingress = []
                                
                                    data = {"start_time":start_date_iso,"end_time":end_date_iso,"interval":"1min","metrics":[{"name":"InterfaceBandwidthUsage","statistics":["average"],"unit":"Mbps"}],"view":{"individual":"direction"},"filter":{"site":[site_id],"element":[element_id],"interface":[interface_id]}}
                    
                                    resp = cgx.post.monitor_sys_metrics(data)                                
                                    data_info = resp.cgx_content["metrics"][0]["series"]
                                
                                    for item in data_info:
                                        if isinstance(item["view"], dict):
                                            if item["view"]["direction"] == "Ingress":
                                                for value in item["data"][0]["datapoints"]:
                                                    data_set_ingress.append(value["value"])
                                            elif item["view"]["direction"] == "Egress":
                                                for value in item["data"][0]["datapoints"]:
                                                    data_set_egress.append(value["value"])
                                                
                                
                                    data_set = {}
                                    data_set["Site_Name"] = site_name
                                    data_set["Circuit_Name"] = circuit_name
                                    data_set["UP_BW"] = bw_up
                                    data_set["DOWN_BW"] = bw_down
                                    data_set["DOWN_MIN"] = 0
                                    data_set["DOWN_MAX"] = 0
                                    data_set["DOWN_AVG"] = 0
                                    data_set["DOWN_ABOVE_70"] = 0 
                                    data_set["UP_MIN"] = 0
                                    data_set["UP_MAX"] = 0
                                    data_set["UP_AVG"] = 0
                                    data_set["UP_ABOVE_70"] = 0
                                
                                    if data_set_ingress:
                                        data_set["DOWN_MIN"] = round(min(data_set_ingress), 2)
                                        data_set["DOWN_MAX"] = round(max(data_set_ingress), 2)
                                        data_set["DOWN_AVG"] = round(sum(data_set_ingress) / len(data_set_ingress), 2)
                                
                                        check_overage = int(bw_down) * .70
                                        overage_minutes = 0
                                        for item in data_set_ingress:
                                            if int(item) >= check_overage:
                                                overage_minutes += 1
                                        data_set["DOWN_ABOVE_70"] = overage_minutes
                                
                                    if data_set_egress:
                                        data_set["UP_MIN"] = round(min(data_set_egress), 2)
                                        data_set["UP_MAX"] = round(max(data_set_egress), 2)
                                        data_set["UP_AVG"] = round(sum(data_set_egress) / len(data_set_egress), 2)
                                
                                        check_overage = int(bw_up) * .70
                                        overage_minutes = 0
                                        for item in data_set_egress:
                                            if int(item) >= check_overage:
                                                overage_minutes += 1
                                        data_set["UP_ABOVE_70"] = overage_minutes
                                
                                    data_set_list.append(data_set)
                    except:
                        print("Unable to get wan stats for " + site_name)                                                     
                                    
    
    csv_columns = []        
    for key in (data_set_list)[0]:
        csv_columns.append(key)
    
    csv_file = "circuit_report.csv"
    with open(csv_file, 'w', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()
        for data in data_set_list:
            try:
                writer.writerow(data)
            except:
                print("Failed to write data for row")
        print("Saved " + csv_file + " file")
    
    return

                                          
def go():
    ############################################################################
    # Begin Script, parse arguments.
    ############################################################################

    # Parse arguments
    parser = argparse.ArgumentParser(description="{0}.".format(SCRIPT_NAME))

    # Allow Controller modification and debug level sets.
    controller_group = parser.add_argument_group('API', 'These options change how this program connects to the API.')
    controller_group.add_argument("--controller", "-C",
                                  help="Controller URI, ex. "
                                       "Alpha: https://api-alpha.elcapitan.cloudgenix.com"
                                       "C-Prod: https://api.elcapitan.cloudgenix.com",
                                  default=None)
    controller_group.add_argument("--insecure", "-I", help="Disable SSL certificate and hostname verification",
                                  dest='verify', action='store_false', default=True)
    config_group = parser.add_argument_group('Config', 'Details for the ION devices you wish to update')
    config_group.add_argument("--date", "-D", help="Provide a date such as 2025-01-01", default=None)
    
    args = vars(parser.parse_args())
                             
    ############################################################################
    # Instantiate API
    ############################################################################
    cgx_session = API()

    
    ##
    # ##########################################################################
    # Draw Interactive login banner, run interactive login including args above.
    ############################################################################
    print("{0} {1} ({2})\n".format(SCRIPT_NAME, SCRIPT_VERSION, cgx_session.controller))

    # check for token
    from prismasase_settings import PRISMASASE_CLIENT_ID, PRISMASASE_CLIENT_SECRET, PRISMASASE_TSG_ID
    try:
        from prismasase_settings import PRISMASASE_CLIENT_ID, PRISMASASE_CLIENT_SECRET, PRISMASASE_TSG_ID
    except ImportError:
        print("error")

        # will get caught below
        PRISMASASE_CLIENT_ID = None
        PRISMASASE_CLIENT_SECRET = None
        PRISMASASE_TSG_ID = None
        
    
    cgx_session.interactive.login_secret(client_id=PRISMASASE_CLIENT_ID, 
                                     client_secret=PRISMASASE_CLIENT_SECRET, 
                                     tsg_id=PRISMASASE_TSG_ID)

        

    ############################################################################
    # End Login handling, begin script..
    ############################################################################

    # get time now.
    curtime_str = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')
    print("Starting Bandwidth Interface Script")

    # create file-system friendly tenant str.
    tenant_str = "".join(x for x in cgx_session.tenant_name if x.isalnum()).lower()
    cgx = cgx_session
    
    input_date = args["date"]
    
    # Define the PST timezone
    pst = pytz.timezone("US/Pacific")
    
    # Convert input string to a PST-aware datetime object
    base_datetime = pst.localize(datetime.strptime(input_date, "%Y-%m-%d"))
    
    # Set the end date to 8:00 AM PST on the provided day
    end_datetime = base_datetime.replace(hour=8, minute=0, second=0)
    end_date_iso = end_datetime.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Set the start date to 5:00 PM PST the previous day
    start_datetime = base_datetime - timedelta(days=1)
    start_datetime = start_datetime.replace(hour=17, minute=0, second=0)
    start_date_iso = start_datetime.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    run_reports(cgx, start_date_iso, end_date_iso)
    
    # end of script, run logout to clear session.
    cgx_session.get.logout()

if __name__ == "__main__":
    go()