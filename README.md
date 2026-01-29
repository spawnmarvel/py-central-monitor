# py-central-monitor

python webapp for central monitoring from different sources

## env

* linux
* zabbix api
* cron job or az functions

```bash
python3 --version
Python 3.11.2

pip --version
pip 23.0.1 from /usr/lib/python3/dist-packages/pip (python 3.11)
``` 

However, since you are inside a Git repo, you must make sure the venv folder is ignored, or you'll accidentally try to push thousands of library files to your repository.

```bash
mkdir py-central-monitor
# or
git clone # the repos url

cd py-central-monitor

# In your terminal, inside your project folder:
# Create the virtual environment folder (commonly named 'venv')
python3 -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# dependencies
pip install zabbix-utils

# libs
pip freeze > requirements.txt

# deactivate
deactivate

```

You definitely don't want Git tracking the venv folder. Add this line to your .gitignore:

```log
# Ignore python virtual environments
venv/
.env
config.json
``` 

example structure

```text
py-central-monitor/
├── .git/                      # Git metadata
├── venv/                      # Python virtual environment (IGNORED)
├── .gitignore                 # Files to exclude from Git
├── config.json                # Real credentials (IGNORED)
├── config.json.example        # Template with dummy data (TRACKED)
├── last_problems.json         # The local state "brain" (IGNORED)
└── pcm_agent_collector.py     # Your main logic (TRACKED)
```

## config

user and passbased:

```json
{
    "zabbix_url": "https://your-zabbix-server/zabbix",
    "zabbix_vm_name": "monitored host name",
    "zabbix_user": "Admin",
    "zabbix_pass": "your_password"
}
```
tokenbased:

## zabbix integration

1. Create the User Group

- Go to Administration > User groups > Create user group.
- Group name: API_Automation_Group.
- Host permissions tab: Add the specific Host Groups your script needs to manage.
- Permission: Select Read-write (since you mentioned "updating stuff").
- Inside your User Group settings, look for the Frontend access dropdown.
- Set this to Disabled.

2. Create the User Role

- Go to Administration > User roles > Create user role.
- Name: API_Limited_Write_Role.
- User type: Admin (required if you are updating host/item configurations).
- API access: Checked.
- API methods: (kept default )Specify problem.*, event.*, and host.* (or just the ones you specifically need).

3. Create the User

- Go to Administration > Users > Create user.
- Username: api_script_user.
- Groups: Select your API_Automation_Group.
- User role tab: Select your API_Limited_Write_Role.

## pcm-agent-collector (telegraf??)

The agent can be deployed to any linux server and can send data to a mysql database that acts as a central monitor for many agents

Here the data is collected from a zabbix server.

The data can the be:

- stored local/ file / db
- sent to remote server and stored local/ file / db / rabbitmq

In this example the data is collect from a remote zabbix server (it could be localhost also, on the zabbix server) and sent to a remote mysql.


```bash 
(venv python3 pcm_agent_collector.py.py)

```

Example result:

```text
NEW PROBLEM; 24075; vmzabbix02; dmzdocker03; Interface eth0; Ethernet has changed to lower speed than it was before; No data; 4m; Unacknowledged
NEW PROBLEM; 24105; vmzabbix02; docker03getmirrortest; Interface eth0; Ethernet has changed to lower speed than it was before; No data; 4m; Unacknowledged
NEW PROBLEM; 23875; vmzabbix02; Zabbix server; Cert; SSL certificate is invalid; No data; 197d 11h 7m; Unacknowledged
NEW PROBLEM; 24126; vmzabbix02; vmoffline01; Linux; Zabbix agent is not available; No data; 15d 21h 31m; Unacknowledged
NEW PROBLEM; 24039; vmzabbix02; docker03getmirrortest; Linux; Zabbix agent is not available; No data; 9d 23h 39m; Unacknowledged
NEW PROBLEM; 24062; vmzabbix02; dmzdocker03; Linux; Zabbix agent is not available; No data; 9d 23h 38m; Unacknowledged
NEW PROBLEM; 23795; vmzabbix02; Zabbix server; MySQL; Buffer pool utilization is too low; No data; 22h 12m; Unacknowledged
```

second run

```bash
python3 pcm_agent_collector.py 
# No changes since last run.
``` 

example last_problems.json

```json
{
    "23875": {
        "source_vm": "vmzabbix02",
        "hostname": "Zabbix server",
        "full_display": "vmzabbix02; Zabbix server; Cert; SSL certificate is invalid; No data; 197d 10h 57m; Unacknowledged",
        "opdata": "No data",
        "duration": "197d 10h 57m",
        "action": "Unacknowledged"
    },
    "24075": {
        "source_vm": "vmzabbix02",
        "hostname": "dmzdocker03",
        "full_display": "vmzabbix02; dmzdocker03; Interface eth0; Ethernet has changed to lower speed than it was before; Current reported speed: {ITEM.LASTVALUE1}; 48d 20h 31m; Unacknowledged",
        "opdata": "Current reported speed: {ITEM.LASTVALUE1}",
        "duration": "48d 20h 31m",
        "action": "Unacknowledged"
    }
   
}
```

Information:

- Secured Credentials: Moved secrets to config.json with a tracked .example template.

- Environment Isolation: Standardized on a Python venv for clean dependency management.

- Git Hardening: Implemented .gitignore to prevent credential leaks and ignore local state files.

- Stateful Intelligence: Built a "brain" via last_problems.json to track active alerts and only perform database writes when data actually changes.

- Delimited Data Engine: Created a semicolon-delimited output format tailored for the central_monitor database schema.


## central monitor database

The agents can be deployed to any linux server and can send data to a mysql database that acts as a central monitor for many agents.

The data in the database can then be shipped of or use replication on mysql , https://dev.mysql.com/doc/refman/8.4/en/replication.html

Replication enables data from one MySQL database server (known as a source) to be copied to one or more MySQL database servers (known as replicas). - 

Replication is asynchronous by default; replicas do not need to be connected permanently to receive updates from a source. Depending on the configuration, you can replicate all databases, selected databases, or even selected tables within a database
create the database

```sql

CREATE DATABASE central_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;

CREATE USER 'pcm-agent'@'%' IDENTIFIED BY 'password';

GRANT ALL PRIVILEGES ON central_monitor.* TO 'pcm-agent'@'%';

FLUSH PRIVILEGES;


USE central_monitor;

CREATE TABLE IF NOT EXISTS zabbix_live_problems (
    trigger_id BIGINT PRIMARY KEY,
    source_vm VARCHAR(50),
    hostname VARCHAR(255),
    category VARCHAR(100),
    problem_detail TEXT,
    operational_data TEXT,
    duration VARCHAR(50),
    ack_status VARCHAR(50),
    severity VARCHAR(20),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

```

Why this structure?
- trigger_id as PRIMARY KEY: This is the most important part. Since Zabbix gives every alert a unique ID, we use it to prevent duplicates. If the script finds a change, it will REPLACE or UPDATE the row with that ID rather than creating a new one.

- utf8mb4_bin: Matches your database collation, ensuring that special characters in Zabbix item names (like Greek letters or symbols) don't break the insert.

- last_updated: This helps you see exactly when the script last synced that specific alert to the central database.

## example insert into

```sql
INSERT INTO zabbix_live_problems 
    (trigger_id, source_vm, hostname, category, problem_detail, operational_data, duration, ack_status, severity) 
VALUES 
    (23875, 'vmzabbix02', 'Zabbix server', 'Cert', 'SSL certificate is invalid', 'No data', '197d 14h 14m', 'Unacknowledged', 'Average')
ON DUPLICATE KEY UPDATE 
    operational_data = VALUES(operational_data),
    duration = VALUES(duration),
    ack_status = VALUES(ack_status),
    last_updated = CURRENT_TIMESTAMP;
```

result on select

```text
select * from zabbix_live_problems;
+------------+------------+---------------+----------+----------------------------+------------------+--------------+----------------+----------+---------------------+
| trigger_id | source_vm  | hostname      | category | problem_detail             | operational_data | duration     | ack_status     | severity | last_updated        |
+------------+------------+---------------+----------+----------------------------+------------------+--------------+----------------+----------+---------------------+
|      23875 | vmzabbix02 | Zabbix server | Cert     | SSL certificate is invalid | No data          | 197d 14h 14m | Unacknowledged | Average  | 2026-01-29 22:00:31 |
+------------+------------+---------------+----------+----------------------------+------------------+--------------+----------------+----------+---------------------+
1 row in set (0.012 sec)
```

To insert your data into the MySQL table, you should use the ON DUPLICATE KEY UPDATE syntax. This is the most efficient method because it allows the script to update the duration or acknowledgment status of an existing alert without creating a duplicate row for the same trigger_id.

## flask app central monitor view








