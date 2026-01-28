import json
from zabbix_utils import ZabbixAPI

def get_zabbix_problems():
    # 1. Load configuration from JSON
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json file not found.")
        return

    # 2. Initialize API using dictionary keys
    api = ZabbixAPI(url=config['zabbix_url'])

    try:
        # 3. Authenticate
        api.login(user=config['zabbix_user'], password=config['zabbix_pass'])
        print(f"Connected to: {config['zabbix_url']}\n")

        # 4. Fetch Problems
        # We only request the fields we actually need to save memory
        problems = api.problem.get(
            output=["eventid", "name", "severity", "clock"],
            sortfield="eventid",
            sortorder="DESC"
        )

        if not problems:
            print("No active problems found. Everything is green!")
            return

        print(f"{'ID':<10} | {'Severity':<10} | {'Problem Name'}")
        print("-" * 60)

        for p in problems:
            print(f"{p['eventid']:<10} | {p['severity']:<10} | {p['name']}")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # 5. Always close the session
        if 'api' in locals():
            api.logout()

if __name__ == "__main__":
    get_zabbix_problems()