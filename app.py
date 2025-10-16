from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

# ⬇️ TUKAR NI NANTI! ⬇️
UBIBOT_ACCOUNT_KEY = os.getenv('UBIBOT_ACCOUNT_KEY', 'your_key_here')
CHANNEL_ID_GS1 = os.getenv('CHANNEL_ID_GS1', 'your_gs1_id')
CHANNEL_ID_PLUG = os.getenv('CHANNEL_ID_PLUG', 'your_plug_id')

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/latest')
def get_latest():
    """Fetch latest data from UbiBot API"""
    result = {'gs1_sensor': None, 'smart_plug': None}
    
    try:
        # Get GS1 data
        gs1_url = f'https://api.ubibot.io/v1.0/channels/{CHANNEL_ID_GS1}'
        gs1_res = requests.get(gs1_url, params={'account_key': UBIBOT_ACCOUNT_KEY}, timeout=10)
        
        if gs1_res.status_code == 200:
            data = gs1_res.json()
            if 'channel' in data and 'last_values' in data['channel']:
                vals = data['channel']['last_values']
                result['gs1_sensor'] = {
                    'temperature': vals.get('field1'),
                    'humidity': vals.get('field2'),
                    'soil_temperature': vals.get('field3'),
                    'soil_humidity': vals.get('field4'),
                    'soil_ec': vals.get('field5'),
                    'soil_ph': vals.get('field6')
                }
        
        # Get Smart Plug data
        plug_url = f'https://api.ubibot.io/v1.0/channels/{CHANNEL_ID_PLUG}'
        plug_res = requests.get(plug_url, params={'account_key': UBIBOT_ACCOUNT_KEY}, timeout=10)
        
        if plug_res.status_code == 200:
            data = plug_res.json()
            if 'channel' in data and 'last_values' in data['channel']:
                vals = data['channel']['last_values']
                result['smart_plug'] = {
                    'switch_status': vals.get('field1', 0),
                    'socket_voltage': vals.get('field2'),
                    'socket_current': vals.get('field3'),
                    'socket_power': vals.get('field4'),
                    'cumulative_electricity': vals.get('field5'),
                    'carbon_dioxide': vals.get('field6')
                }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    """Fetch last 24 hours data"""
    result = {'gs1_sensor': [], 'smart_plug': []}
    
    try:
        # Get GS1 history
        gs1_url = f'https://api.ubibot.io/v1.0/channels/{CHANNEL_ID_GS1}/data'
        gs1_res = requests.get(gs1_url, params={'account_key': UBIBOT_ACCOUNT_KEY, 'results': 100}, timeout=10)
        
        if gs1_res.status_code == 200:
            data = gs1_res.json()
            if 'feeds' in data:
                for feed in data['feeds'][:100]:
                    result['gs1_sensor'].append({
                        'timestamp': feed.get('created_at'),
                        'temperature': feed.get('field1'),
                        'humidity': feed.get('field2'),
                        'soil_temperature': feed.get('field3'),
                        'soil_humidity': feed.get('field4')
                    })
        
        # Get Smart Plug history
        plug_url = f'https://api.ubibot.io/v1.0/channels/{CHANNEL_ID_PLUG}/data'
        plug_res = requests.get(plug_url, params={'account_key': UBIBOT_ACCOUNT_KEY, 'results': 100}, timeout=10)
        
        if plug_res.status_code == 200:
            data = plug_res.json()
            if 'feeds' in data:
                for feed in data['feeds'][:100]:
                    result['smart_plug'].append({
                        'timestamp': feed.get('created_at'),
                        'socket_power': feed.get('field4'),
                        'socket_voltage': feed.get('field2'),
                        'socket_current': feed.get('field3')
                    })
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

4. **Scroll bawah**, commit message: `Create app.py`

5. Click **"Commit changes"** (button hijau)

---

### **FILE 2: requirements.txt**

1. **Balik ke main page** repo (click `ubibot-dashboard` atas)

2. Click **"Add file"** → **"Create new file"**

3. **Name your file**: Type `requirements.txt`

4. **Paste ni:**
```
Flask==3.0.0
requests==2.31.0
gunicorn==21.2.0
