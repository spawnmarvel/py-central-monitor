import json
import os
import sys
from zabbix_utils import ZabbixAPI

# Get the directory where the script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.json')

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: {CONFIG_PATH} not found.")
        sys.exit(1)
    
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def main():
    config = load_config()
    api = ZabbixAPI(url=config['zabbix_url'])

    try:
        api.login(user=config['zabbix_user'], password=config['zabbix_pass'])
        # Get only the most important problem details
        problems = api.problem.get(
            output=["name", "severity"],
            recent=True
        )
        
        for p in problems:
            print(f"Alert: {p['name']} (Severity: {p['severity']})")
            
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        api.logout()

if __name__ == "__main__":
    main()