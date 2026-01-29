import json
import os
import ssl
import urllib.request
import time

def zabbix_rpc(url, method, params, auth_token=None):
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
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d > 0: parts.append(str(d) + "d")
    if h > 0: parts.append(str(h) + "h")
    if m > 0: parts.append(str(m) + "m")
    
    if parts:
        return " ".join(parts)
    else:
        return "0m"

def get_zabbix_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, 'config.json')
    history_file = os.path.join(base_dir, 'last_problems.json')
    
    if not os.path.exists(config_file):
        error_output = "Error: " + config_file + " not found."
        print(error_output)
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    z_vm_name = config.get("zabbix_vm_name", "Unknown-VM")
    history = {}
    
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            file_content = f.read()
            if file_content:
                history = json.loads(file_content)

    # 1. Login
    login = zabbix_rpc(config['zabbix_url'], "user.login", 
                       {"username": config['zabbix_user'], "password": config['zabbix_pass']})
    
    if "result" not in login:
        error_msg = str(login.get("error", "Unknown Error"))
        login_error = "Login failed: " + error_msg
        print(login_error)
        return

    auth_token = login["result"]

    # 2. Fetch Data
    params = {
        "output": ["triggerid", "description", "priority", "opdata", "lastchange"],
        "selectHosts": ["name"],
        "selectLastEvent": ["acknowledged", "opdata"], 
        "expandDescription": True,
        "only_true": True,
        "monitored": True
    }
    
    rpc_response = zabbix_rpc(config['zabbix_url'], "trigger.get", params, auth_token)
    
    if "result" not in rpc_response:
        fetch_error = "Failed to fetch triggers."
        print(fetch_error)
        return

    triggers = rpc_response["result"]
    current_time = time.time()
    current_state = {}
    changes_detected = False

    # 3. Process Triggers
    for t in triggers:
        tid = str(t['triggerid'])
        
        if t.get("hosts"):
            hostname = t["hosts"][0]["name"]
        else:
            hostname = "Unknown"
        
        raw_desc = t['description']
        if ":" in raw_desc:
            parts = raw_desc.split(":", 1)
            category = parts[0].strip()
            problem_detail = parts[1].strip()
        else:
            category = "General"
            problem_detail = raw_desc.strip()
        
        op_data = "No data"
        event_data = t.get("lastEvent", {})
        event_opdata = event_data.get("opdata")
        trigger_opdata = t.get("opdata")

        if event_opdata and "{ITEM.LASTVALUE" not in event_opdata:
            op_data = event_opdata
        elif trigger_opdata and "{ITEM.LASTVALUE" not in trigger_opdata:
            op_data = trigger_opdata
        
        duration_str = format_duration(current_time - int(t['lastchange']))
        
        if event_data.get("acknowledged") == "1":
            ack_status = "Acknowledged"
        else:
            ack_status = "Unacknowledged"

        # Construct the core semicolon string using concatenation
        formatted_string = tid + "; " + z_vm_name + "; " + hostname + "; " + category + "; " + problem_detail + "; " + op_data + "; " + duration_str + "; " + ack_status
        
        current_state[tid] = {
            "display": formatted_string,
            "opdata": op_data,
            "action": ack_status
        }

        # Compare with history
        if tid not in history:
            output_msg = "NEW PROBLEM; " + formatted_string
            print(output_msg)
            changes_detected = True
        elif history[tid]['opdata'] != op_data or history[tid]['action'] != ack_status:
            output_msg = "DATA UPDATE; " + formatted_string
            print(output_msg)
            changes_detected = True

    # 4. Handle Resolutions
    resolved_ids = set(history.keys()) - set(current_state.keys())
    for rid in resolved_ids:
        # String concatenation for resolved messages
        resolved_msg = "RESOLVED; " + str(history[rid]['display'])
        print(resolved_msg)
        changes_detected = True

    # 5. Save state
    if changes_detected:
        with open(history_file, 'w') as f:
            json.dump(current_state, f, indent=4)
    else:
        no_change_msg = "No changes since last run."
        print(no_change_msg)

    # 6. Logout
    zabbix_rpc(config['zabbix_url'], "user.logout", [], auth_token)

if __name__ == "__main__":
    get_zabbix_data()