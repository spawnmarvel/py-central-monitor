import json
import os
import ssl
import urllib.request
import time

def zabbix_rpc(url, method, params, auth_token=None):
    """Standard Zabbix API Request Handler"""
    if not url.endswith('/api_jsonrpc.php'):
        url = url.rstrip('/') + '/api_jsonrpc.php'

    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if auth_token:
        payload["auth"] = auth_token
    
    data = json.dumps(payload).encode("utf-8")
    context = ssl._create_unverified_context()
    headers = {'Content-Type': 'application/json-rpc', 'User-Agent': 'PCM-Agent'}
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def format_duration(seconds):
    """Converts unix timestamp difference into readable d/h/m format"""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d > 0: parts.append(str(d) + "d")
    if h > 0: parts.append(str(h) + "h")
    if m > 0: parts.append(str(m) + "m")
    return " ".join(parts) if parts else "0m"

def get_zabbix_data():
    # 1. Setup paths and load local configuration
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, 'config.json')
    history_file = os.path.join(base_dir, 'last_problems.json')
    
    if not os.path.exists(config_file):
        print("Error: " + config_file + " not found.")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    z_vm_name = config.get("zabbix_vm_name", "Unknown-VM")
    
    # 2. Load the previous snapshot to detect resolved problems
    history = {}
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            try: history = json.load(f)
            except: history = {}

    # 3. Authenticate with Zabbix API
    login = zabbix_rpc(config['zabbix_url'], "user.login", 
                       {"username": config['zabbix_user'], "password": config['zabbix_pass']})
    
    if "result" not in login:
        print("Login failed: " + str(login.get("error", "Unknown Error")))
        return
    auth_token = login["result"]

    # 4. Request Active Problems
    # In Zabbix 7.0, we select 'lastEvent' to try and get expanded opdata macros
    params = {
        "output": ["triggerid", "description", "priority", "opdata", "lastchange"],
        "selectHosts": ["name"],
        "selectLastEvent": "extend", 
        "expandDescription": True,
        "only_true": True,
        "monitored": True
    }
    
    rpc_response = zabbix_rpc(config['zabbix_url'], "trigger.get", params, auth_token)
    triggers = rpc_response.get("result", [])
    
    current_time = time.time()
    current_state = {}
    severity_labels = ["Not classified", "Info", "Warning", "Average", "High", "Disaster"]

    # 5. Process currently active triggers
    for t in triggers:
        tid = str(t['triggerid'])
        hostname = t["hosts"][0]["name"] if t.get("hosts") else "Unknown"
        
        # Split Category (e.g., 'Cert') from Problem Detail
        raw_desc = t['description']
        if ":" in raw_desc:
            parts = raw_desc.split(":", 1)
            category = parts[0].strip()
            detail = parts[1].strip()
        else:
            category = "General"
            detail = raw_desc.strip()
        
        # Operational Data Search (Macro Expansion)
        op_data = "No data"
        last_event = t.get("lastEvent")
        
        # Look in the Event metadata first (Zabbix 7.0 default)
        if isinstance(last_event, dict) and last_event.get("opdata"):
            val = str(last_event["opdata"]).strip()
            if val and "{ITEM.LASTVALUE" not in val:
                op_data = val
        
        # Fallback to Trigger opdata field
        if op_data == "No data" and t.get("opdata"):
            val = str(t["opdata"]).strip()
            if val and "{ITEM.LASTVALUE" not in val:
                op_data = val
        
        duration_str = format_duration(current_time - int(t['lastchange']))
        
        # Determine if the alert has been acknowledged in the UI
        ack_status = "Unacknowledged"
        if isinstance(last_event, dict) and last_event.get("acknowledged") == "1":
            ack_status = "Acknowledged"

        severity = severity_labels[int(t['priority'])]

        # Construct semicolon string for console output
        formatted_string = tid + "; " + z_vm_name + "; " + hostname + "; " + category + "; " + detail + "; " + op_data + "; " + duration_str + "; " + ack_status + "; " + severity
        
        current_state[tid] = {"display": formatted_string}

        print("PROBLEM; " + formatted_string)

    # 6. Compare new data with history to find resolved alerts
    for old_tid in history:
        if old_tid not in current_state:
            # If it was in our JSON but is no longer in Zabbix, it is RESOLVED
            print("RESOLVED; " + str(history[old_tid]['display']))

    # 7. Save the current snapshot back to JSON for the next run
    with open(history_file, 'w') as f:
        json.dump(current_state, f, indent=4)

    # 8. Close the API session
    zabbix_rpc(config['zabbix_url'], "user.logout", [], auth_token)

if __name__ == "__main__":
    get_zabbix_data()