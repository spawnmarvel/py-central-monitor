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
    
    # Login
    login = zabbix_rpc(config['zabbix_url'], "user.login", 
                       {"username": config['zabbix_user'], "password": config['zabbix_pass']})
    if "result" not in login:
        print("Login failed")
        return
    auth_token = login["result"]

    # Get Problems
    prob_params = {"output": "extend", "recent": False, "sortfield": ["eventid"], "sortorder": "DESC"}
    problems = zabbix_rpc(config['zabbix_url'], "problem.get", prob_params, auth_token).get("result", [])
    
    trigger_ids = list(set([p["objectid"] for p in problems]))
    trigger_params = {
        "triggerids": trigger_ids, "output": ["description", "priority"],
        "selectHosts": ["name"], "selectFunctions": ["itemid"], "expandDescription": True
    }
    triggers = zabbix_rpc(config['zabbix_url'], "trigger.get", trigger_params, auth_token).get("result", [])
    trigger_map = {t["triggerid"]: t for t in triggers}

    current_state = {}
    severity_labels = ["Not classified", "Info", "Warning", "Average", "High", "Disaster"]

    for p in problems:
        tid = p['objectid']
        if tid not in trigger_map: continue
        t = trigger_map[tid]
        
        # Operational Data Logic
        op_data = p.get("opdata", "").strip()
        if not op_data or "{ITEM.LASTVALUE" in op_data:
            if t.get("functions"):
                item_id = t["functions"][0]["itemid"]
                item = zabbix_rpc(config['zabbix_url'], "item.get", {"itemids": item_id, "output": ["lastvalue", "units"]}, auth_token)
                if item.get("result"):
                    res = item["result"][0]
                    op_data = f"{res['lastvalue']} {res['units']}".strip()
        if not op_data: op_data = "No data"

        # Parsing
        raw_desc = t['description']
        cat, det = (raw_desc.split(":", 1) if ":" in raw_desc else ("General", raw_desc))
        dur = format_duration(time.time() - int(p['clock']))
        ack = "Acknowledged" if p.get("acknowledged") == "1" else "Unacknowledged"
        sev = severity_labels[int(p['severity'])]
        host = t["hosts"][0]["name"] if t.get("hosts") else "Unknown"

        display_str = f"{tid}; {z_vm_name}; {host}; {cat.strip()}; {det.strip()}; {op_data}; {dur}; {ack}; {sev}"
        current_state[tid] = {"display": display_str}

    with open(history_file, 'w') as f:
        json.dump(current_state, f, indent=4)
    zabbix_rpc(config['zabbix_url'], "user.logout", [], auth_token)
    print(f"Sync complete. {len(current_state)} problems found.")

if __name__ == "__main__":
    get_zabbix_data()