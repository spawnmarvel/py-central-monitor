import json
import os
# import urllib3
from zabbix_utils import ZabbixAPI

# Disable SSL warnings
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_zabbix_data():
    config_file = 'config.json'
    if not os.path.exists(config_file):
        print("Error: " + config_file + " not found.")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    api = ZabbixAPI(url=config['zabbix_url'], validate_certs=False)

    try:
        api.login(user=config['zabbix_user'], password=config['zabbix_pass'])
        print("Connected to Zabbix API")
        print("-------------------------------------------------------")

        # We add expandDescription to fill in macros
        # We add selectLastEvent to get the Operational Data (opdata)
        triggers = api.trigger.get(
            output=["triggerid", "description", "priority", "opdata"],
            selectHosts=["name"],
            expandDescription=True,
            only_true=True,
            monitored=True,
            selectLastEvent=["eventid", "opdata"],
            sortfield="priority",
            sortorder="DESC"
        )

        if not triggers:
            print("No active problems found.")
            return

        severity_labels = ["Not classified", "Info", "Warning", "Average", "High", "Disaster"]

        for t in triggers:
            # 1. Get Hostname
            hostname = "Unknown Host"
            if "hosts" in t and len(t["hosts"]) > 0:
                hostname = t["hosts"][0]["name"]

            # 2. Get Severity Name
            sev_index = int(t['priority'])
            if sev_index < len(severity_labels):
                sev_name = severity_labels[sev_index]
            else:
                sev_name = str(t['priority'])

            # 3. Get Operational Data
            # This is the "live value" seen in the Zabbix dashboard
            op_data = "No data"
            if "opdata" in t and t["opdata"] != "":
                op_data = t["opdata"]
            elif "lastEvent" in t and t["lastEvent"] is not None:
                # Sometimes opdata is nested in the last event
                op_data = t["lastEvent"].get("opdata", "No data")

            # 4. Print using + concatenation
            print("[" + hostname + "] " + sev_name + ": " + t['description'])
            print("  > Operational Data: " + op_data)
            print("  > Trigger ID: " + str(t['triggerid']))
            print("-" * 30)

    except Exception as e:
        print("An error occurred: " + str(e))

    finally:
        api.logout()

if __name__ == "__main__":
    get_zabbix_data()