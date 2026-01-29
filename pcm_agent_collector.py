import json
import os
import ssl
import urllib.request
import time

def zabbix_rpc(url, method, params, auth_token=None):
    if not url.endswith('/api_jsonrpc.php'):
        url = url.rstrip('/') + '/api_jsonrpc.php'
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if auth_token: payload["auth"] = auth_token
    
    data = json.dumps(payload).encode("utf-8")
    context = ssl._create_unverified_context()
    headers = {'Content-Type': 'application/json-rpc', 'User-Agent': 'PCM-Agent'}
    
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, context=context) as response:
        return json.loads(response.read().decode("utf-8"))

def format_duration(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    parts = []
    if d > 0: parts.append(f"{d}d")
    if h > 0: parts.append(f"{h}h")
    if m > 0: parts.append(f"{m}m")
    return " ".join(parts) if parts else "0m"

def get_zabbix_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file = os.path.join(base_dir, 'config.json')
    history_file = os.path.join(base_dir, 'last_problems.json')
    
    if not os.path.exists(config_file):
        print(f"Error: {config_file} not found.")
        return

    with open(config_file, 'r') as f:
        config = json.load(f)

    z_vm_name = config.get("zabbix_vm_name", "Unknown-VM")
    history = {}
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            try: history = json.load(f)
            except: history = {}

    try:
        # 1. Login
        login = zabbix_rpc(config['zabbix_url'], "user.login", 
                           {"username": config['zabbix_user'], "password": config['zabbix_pass']})
        if "result" not in login:
            print("Login failed. Check config.json")
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
        result = zabbix_rpc(config['zabbix_url'], "trigger.get", params, auth_token)
        triggers = result.get("result", [])

        current_time = time.time()
        current_state = {}
        changes_detected = False

        for t in triggers:
            tid = t['triggerid']
            hostname = t["hosts"][0]["name"] if t.get("hosts") else "Unknown"
            
            # Clean Description
            raw_desc = t['description']
            category, problem_detail = (raw_desc.split(":", 1) if ":" in raw_desc else ("General", raw_desc))
            
            # Resolve Operational Data (Macros)
            # Strategy: Prefer lastEvent opdata which Zabbix resolves into actual values
            op_data = "No data"
            event_opdata = t.get("lastEvent", {}).get("opdata")
            trigger_opdata = t.get("opdata")

            if event_opdata and "{ITEM.LASTVALUE" not in event_opdata:
                op_data = event_opdata
            elif trigger_opdata and "{ITEM.LASTVALUE" not in trigger_opdata:
                op_data = trigger_opdata
            
            duration_str = format_duration(current_time - int(t['lastchange']))
            ack_status = "Acknowledged" if t.get("lastEvent", {}).get("acknowledged") == "1" else "Unacknowledged"

            # NEW FORMAT: Type; TriggerID; VM; Host; Category; Detail; OpData; Duration; Action
            formatted_string = f"{tid}; {z_vm_name}; {hostname}; {category.strip()}; {problem_detail.strip()}; {op_data}; {duration_str}; {ack_status}"
            
            current_state[tid] = {
                "display": formatted_string,
                "opdata": op_data,
                "action": ack_status
            }

            if tid not in history:
                print(f"NEW PROBLEM; {formatted_string}")
                changes_detected = True
            elif history[tid]['opdata'] != op_data or history[tid]['action'] != ack_status:
                print(f"DATA UPDATE; {formatted_string}")
                changes_detected = True

        # 3. Handle Resolutions
        resolved_ids = set(history.keys()) - set(current_state.keys())
        for rid in resolved_ids:
            print(f"RESOLVED; {history[rid]['display']}")
            changes_detected = True

        # 4. Save state if changes occurred
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