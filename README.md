# py-central-monitor

python webapp for central monitoring from different sources

## env

* flask
* linux
* api
* pip install zabbix-utils

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
Go to Administration > User groups > Create user group.

Group name: API_Automation_Group.

Host permissions tab: Add the specific Host Groups your script needs to manage.

Permission: Select Read-write (since you mentioned "updating stuff").

Inside your User Group settings, look for the Frontend access dropdown.

Set this to Disabled.

2. Create the User Role
Go to Administration > User roles > Create user role.

Name: API_Limited_Write_Role.

User type: Admin (required if you are updating host/item configurations).

API access: Checked.

API methods: Specify problem.*, event.*, and host.* (or just the ones you specifically need).

3. Create the User
Go to Administration > Users > Create user.

Username: api_script_user.

Groups: Select your API_Automation_Group.

User role tab: Select your API_Limited_Write_Role.

## run script

```bash 
(venv python3 get_problems.py)

```

result

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

## flask app








