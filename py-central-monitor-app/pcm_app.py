import json
import os
from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.normpath(os.path.join(BASE_DIR, '..', 'py-central-monitor-agent', 'last_problems.json'))

def get_severity_weight(columns):
    """Assigns a numerical weight for sorting. Disaster is most critical."""
    # We look at the 9th column (index 8) which contains the severity name
    if len(columns) < 9: return 99
    
    s = columns[8].lower()
    if "disaster" in s: return 0  # Highest priority
    if "high" in s: return 1
    if "average" in s: return 2
    if "warning" in s: return 3
    if "info" in s: return 4
    return 5

@app.route('/')
def index():
    alerts_to_show = []
    error_message = None
    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    if not os.path.exists(FILE_PATH):
        error_message = f"FILE NOT FOUND at {FILE_PATH}"
    else:
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            for key in raw_data:
                display_str = raw_data[key].get("display", "")
                if "not classified" in display_str.lower():
                    continue
                
                columns = [c.strip() for c in display_str.split(';')]
                # Ensure the column count is safe for sorting
                if len(columns) > 8:
                    alerts_to_show.append(columns)

            alerts_to_show.sort(key=get_severity_weight)

        except Exception as e:
            error_message = f"SYSTEM ERROR: {str(e)}"

    return render_template('index.html', alerts=alerts_to_show, error=error_message, update_time=now)

# --- THIS IS THE CRITICAL BLOCK ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)