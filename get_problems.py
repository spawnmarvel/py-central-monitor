import json
import os
import ssl
import urllib.request
import urllib.error

def zabbix_rpc(url, method, params, auth_token=None):
    """Helper to handle JSON-RPC requests via urllib"""
    
    # Ensure URL points exactly to the API endpoint
    if not url.endswith('/api_jsonrpc.php'):
        url = url.rstrip('/') + '/api_jsonrpc.php'

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    if auth_token:
        payload["auth"] = auth_token

    try:
        data = json.dumps(payload).encode("utf-8")
        
        # Create SSL context to ignore self-signed certificate errors
        context = ssl._create_unverified_context()
        
        # Define headers to ensure the server accepts the JSON request
        headers = {
            'Content-Type': 'application/json-rpc',
            'User-Agent': 'Zabbix-Python-Urllib-Client'
        }
        
        req = urllib.request.Request(url, data=data, headers=headers)
        
        with urllib.request.urlopen(req, context=context) as response:
            res_body = response.read().decode("utf-8")
            if not res_body:
                return {"error": "Empty response from server"}
            return json.loads(res_body)
            
    except urllib.error.HTTPError as e:
        return {"error": "HTTP Error " + str(e.code) + ": " + e.reason}
    except Exception as e:
        return {"error": str(e)}

def get_zabbix_data():
    # 1. Load Configuration
    config_file = 'config.json'
    if not os.path.exists(config_file):
        print("Error: " + config_file + " not found.")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    url = config['zabbix_url']

    # 2. Login to get Auth Token
    login_params = {
        "username": config['zabbix_user'],
        "password": config['zabbix_pass']
    }
    
    print("Connecting to: " + url)
    login_result = zabbix_rpc(url, "user.login", login_params)

    if "error" in login_result:
        print("Login Failed, is zabbix running: " + str(login_result["error"]))
        return

    auth_token = login_result["result"]
    print("Login Successful.")
    print("-" * 50)

    # 3. Fetch Triggers (Problems)
    trigger_params = {
        "output": ["triggerid", "description", "priority", "opdata"],
        "selectHosts": ["name"],
        "expandDescription": True,
        "only_true": True,
        "monitored": True,
        "selectLastEvent": ["eventid", "opdata"],
        "sortfield": "priority",
        "sortorder": "DESC"
    }

    result = zabbix_rpc(url, "trigger.get", trigger_params, auth_token)

    if "error" in result:
        print("API Error: " + str(result["error"]))
        return

    triggers = result.get("result", [])

    if not triggers:
        print("No active problems found.")
    else:
        severity_labels = ["Not classified", "Info", "Warning", "Average", "High", "Disaster"]

        for t in triggers:
            # Get Hostname
            hostname = "Unknown Host"
            if "hosts" in t and len(t["hosts"]) > 0:
                hostname = t["hosts"][0]["name"]

            # Get Severity
            sev_idx = int(t['priority'])
            sev_name = severity_labels[sev_idx] if sev_idx < len(severity_labels) else str(sev_idx)

            # Get Operational Data (Check both trigger and last event levels)
            op_data = t.get("opdata", "")
            if op_data == "" and "lastEvent" in t and t["lastEvent"]:
                op_data = t["lastEvent"].get("opdata", "No data")
            if op_data == "":
                op_data = "No data"

            # Output with + concatenation
            print("[" + hostname + "] " + sev_name + ": " + t['description'])
            print("  > Value: " + op_data)
            print("  > ID: " + str(t['triggerid']))
            print("-" * 30)

    # 4. Logout
    zabbix_rpc(url, "user.logout", [], auth_token)
    print("Session closed.")

if __name__ == "__main__":
    get_zabbix_data()