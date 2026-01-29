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
├── .git/               # Git metadata
├── venv/               # Virtual environment (IGNORED)
├── .gitignore          # Should contain "venv/" and "config.json"
├── config.json         # Your local secrets (IGNORED)
├── config.json.example # Template for others (TRACKED)
└── get_problems.py     # Your script (TRACKED)
```

## config

user and passbased:

```json
{
    "zabbix_url": "https://your-zabbix-server/zabbix",
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
Connected to Zabbix API
-------------------------------------------------------
[Zabbix server] High: Cert: SSL certificate is invalid
  > Operational Data: No data
  > Trigger ID: 23875
------------------------------
[vmoffline01] Average: Linux: Zabbix agent is not available
  > Operational Data: No data
  > Trigger ID: 24126
------------------------------
[docker03getmirrortest] Average: Linux: Zabbix agent is not available
  > Operational Data: No data
  > Trigger ID: 24039
------------------------------
[dmzdocker03] Average: Linux: Zabbix agent is not available
  > Operational Data: No data
  > Trigger ID: 24062
------------------------------
[Zabbix server] Warning: MySQL: Buffer pool utilization is too low
  > Operational Data: No data
  > Trigger ID: 23795
------------------------------
[dmzdocker03] Info: Interface eth0: Ethernet has changed to lower speed than it was before
  > Operational Data: Current reported speed: {ITEM.LASTVALUE1}
  > Trigger ID: 24075
------------------------------
[docker03getmirrortest] Info: Interface eth0: Ethernet has changed to lower speed than it was before
  > Operational Data: Current reported speed: {ITEM.LASTVALUE1}
  > Trigger ID: 24105
------------------------------
```

- Secured your credentials using a config.json file.

- Isolated your environment using a Python venv.

- Hardened your Git workflow by untracking sensitive files.

- Mastered the Zabbix API connection while handling SSL certificate issues.

- Extracted live problem data, including hostnames, severity levels, and operational data.


## central monitor database

The agents can be deployed to any linux server and can send data to a mysql database that acts as a central monitor for many agents.

The data in the database can then be shipped of or use replication on mysql , https://dev.mysql.com/doc/refman/8.4/en/replication.html

Replication enables data from one MySQL database server (known as a source) to be copied to one or more MySQL database servers (known as replicas). - 

Replication is asynchronous by default; replicas do not need to be connected permanently to receive updates from a source. Depending on the configuration, you can replicate all databases, selected databases, or even selected tables within a database
create the database

```sql

create database central_monitor character set utf8mb4 collate utf8mb4_bin;

create user pcm-agent@'%' identified by 'password';

grant all privileges on central_monitor.* to pcm-agent@'%';

-- create table
-- agent_name,zabbx_name, monitored_host, level, message,                               , host_data                 trigger_id 
-- agent name,            dmzdocker03     Average: Linux: Zabbix agent is not available, Operational Data: No data, Trigger ID: 24062

```

## flask app central monitor view








