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
    headers = {'Content-Type': 'application/json-rpc', 'User-Agent': 'Zabbix-to-JSON'}
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, context=context) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def format_duration(seconds):
    # Converts seconds into a readable string like 1d 4h 20m
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d > 0: parts.append(f"{d}d")
    if h > 0: parts.append(f"{h}h")
    if m > 0: parts.append(f"{m}m")
    return " ".join(parts) if parts else "0m"

def get_zabbix_data():
    config_file = 'config.json'
    history_file = 'last_problems.json'
    
    if not os.path.exists(config_file): return

    with open(config_file, 'r') as f:
        config = json.load(f)

    z_vm_name = config.get("zabbix_vm_name", "Unknown-VM")
    history = {}
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            history = {}

    try:
        login = zabbix_rpc(config['zabbix_url'], "user.login", 
                           {"username": config['zabbix_user'], "password": config['zabbix_pass']})
        if "result" not in login: return
        auth_token = login["result"]

        # Added 'lastchange' for duration and 'value' for state
        params = {
            "output": ["triggerid", "description", "priority", "opdata", "lastchange", "value"],
            "selectHosts": ["name"],
            "selectLastEvent": ["eventid", "acknowledged"],
            "expandDescription": True,
            "only_true": True,
            "monitored": True
        }
        result = zabbix_rpc(config['zabbix_url'], "trigger.get", params, auth_token)
        triggers = result.get("result", [])

        current_time = time.time()
        severity_labels = ["Not classified", "Info", "Warning", "Average", "High", "Disaster"]
        current_state = {}
        changes_detected = False

        for t in triggers:
            tid = t['triggerid']
            hostname = t["hosts"][0]["name"] if t.get("hosts") else "Unknown"
            
            # Category and Detail split
            raw_desc = t['description']
            category, problem_detail = (raw_desc.split(":", 1) if ":" in raw_desc else ("General", raw_desc))
            category, problem_detail = category.strip(), problem_detail.strip()

            # Calculate Duration
            duration_secs = current_time - int(t['lastchange'])
            duration_str = format_duration(duration_secs)

            # Action / Acknowledgment status
            ack_status = "Unacknowledged"
            if t.get("lastEvent") and t["lastEvent"].get("acknowledged") == "1":
                ack_status = "Acknowledged"

            op_data = t.get("opdata", "No data")
            if not op_data or op_data == "": op_data = "No data"

            # FINAL FORMAT: Type; VM; Host; Category; Detail; OpData; Duration; Action
            formatted_string = f"{z_vm_name}; {hostname}; {category}; {problem_detail}; {op_data}; {duration_str}; {ack_status}"
            
            current_state[tid] = {
                "source_vm": z_vm_name,
                "hostname": hostname,
                "full_display": formatted_string,
                "opdata": op_data,
                "duration": duration_str,
                "action": ack_status
            }

            if tid not in history:
                print(f"NEW PROBLEM; {formatted_string}")
                changes_detected = True
            elif history[tid]['opdata'] != op_data or history[tid]['action'] != ack_status:
                # We also trigger an update if someone acknowledges the alert in Zabbix
                print(f"DATA UPDATE; {formatted_string}")
                changes_detected = True

        resolved_ids = set(history.keys()) - set(current_state.keys())
        for r_id in resolved_ids:
            print(f"RESOLVED; {history[r_id]['full_display']}")
            changes_detected = True

        if changes_detected:
            with open(history_file, 'w') as f:
                json.dump(current_state, f, indent=4)
        else:
            print("No changes since last run.")

        zabbix_rpc(config['zabbix_url'], "user.logout", [], auth_token)

    except Exception as e:
        print(f"Script Error: {e}")

if __name__ == "__main__":
    get_zabbix_data()