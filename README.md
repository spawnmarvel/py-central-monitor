# py-central-monitor

python webapp for central monitoring from different sources

## env

* linux
* zabbix 7.0.22 / 7 LTS
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
PROBLEM; 23875; vmzabbix02; Zabbix server; Cert; SSL certificate is invalid; No data; 198d 7h 1m; Unacknowledged; High
PROBLEM; 24126; vmzabbix02; vmchaos09; Linux; Zabbix agent is not available; No data; 15m; Unacknowledged; Average
PROBLEM; 24039; vmzabbix02; docker03getmirrortest; Linux; Zabbix agent is not available; No data; 14m; Unacknowledged; Average
PROBLEM; 24062; vmzabbix02; dmzdocker03; Linux; Zabbix agent is not available; No data; 14m; Unacknowledged; Average
PROBLEM; 23795; vmzabbix02; Zabbix server; MySQL; Buffer pool utilization is too low; No data; 12m; Unacknowledged; Warning
PROBLEM; 23435; vmzabbix02; Zabbix server; Interface eth0; Ethernet has changed to lower speed than it was before; No data; 6m; Unacknowledged; Info
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
        "display": "23875; vmzabbix02; Zabbix server; Cert; SSL certificate is invalid; No data; 198d 7h 1m; Unacknowledged; High",
        "opdata": "No data",
        "action": "Unacknowledged"
    },
    "24126": {
        "display": "24126; vmzabbix02; vmchaos09; Linux; Zabbix agent is not available; No data; 15m; Unacknowledged; Average",
        "opdata": "No data",
        "action": "Unacknowledged"
    }
   
}
```

Information:

- Secured Credentials: Moved secrets to config.json with a tracked .example template.

- Environment Isolation: Standardized on a Python venv for clean dependency management.

- Git Hardening: Implemented .gitignore to prevent credential leaks and ignore local state files.

- Stateful Intelligence: Built a "brain" via last_problems.json to track active alerts.

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
    severity_level INT, -- New: Allows sorting (0=Info, 5=Disaster)
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX (hostname),   -- Optimization: Faster searching by host
    INDEX (category)    -- Optimization: Faster filtering by category
);


```

Why this structure?

- trigger_id as BIGINT: Correct. Zabbix 7.0 IDs are large.
- operational_data as TEXT: Correct. Sometimes Zabbix 7.0 packs extra metadata into this field.
- utf8mb4_bin: Matches your database collation, ensuring that special characters in Zabbix item names (like Greek letters or symbols) don't break the insert.
- last_updated: This helps you see exactly when the script last synced that specific alert to the central database.

## example insert into

```sql
USE central_monitor;

INSERT INTO zabbix_live_problems 
    (trigger_id, source_vm, hostname, category, problem_detail, operational_data, duration, ack_status, severity, severity_level) 
VALUES 
    (23875, 'vmzabbix02', 'Zabbix server', 'Cert', 'SSL certificate is invalid', 'No data', '198d 7h 13m', 'Unacknowledged', 'High', 4),
    (24126, 'vmzabbix02', 'vmchaos09', 'Linux', 'Zabbix agent is not available', 'No data', '27m', 'Unacknowledged', 'Average', 3),
    (24039, 'vmzabbix02', 'docker03getmirrortest', 'Linux', 'Zabbix agent is not available', 'No data', '27m', 'Unacknowledged', 'Average', 3),
    (24062, 'vmzabbix02', 'dmzdocker03', 'Linux', 'Zabbix agent is not available', 'No data', '27m', 'Unacknowledged', 'Average', 3),
    (23795, 'vmzabbix02', 'Zabbix server', 'MySQL', 'Buffer pool utilization is too low', 'No data', '24m', 'Unacknowledged', 'Warning', 2),
    (23435, 'vmzabbix02', 'Zabbix server', 'Interface eth0', 'Ethernet has changed to lower speed than it was before', 'No data', '18m', 'Unacknowledged', 'Info', 1)
AS new_data -- This creates an alias for the incoming data
ON DUPLICATE KEY UPDATE 
    duration = new_data.duration,
    operational_data = new_data.operational_data,
    ack_status = new_data.ack_status,
    last_updated = CURRENT_TIMESTAMP;
```

result on select

```sql
select * from zabbix_live_problems;

-- or
SELECT trigger_id, hostname, severity, duration, operational_data 
FROM zabbix_live_problems 
ORDER BY severity_level DESC;
```

row


## flask app central monitor view








