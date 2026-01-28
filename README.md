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


```

You definitely don't want Git tracking the venv folder. Add this line to your .gitignore:

```log
# Ignore python virtual environments
venv/
.env
config.json
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


