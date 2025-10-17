from flask import Flask, render_template, jsonify
import requests
import os

app = Flask(__name__)

# Environment variables
UBIBOT_ACCOUNT_KEY = os.getenv('UBIBOT_ACCOUNT_KEY', 'your_key_here')

@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/api/latest')
def get_latest():
    """Fetch latest data from all UbiBot channels"""
    result = {'gs1_sensor': None, 'smart_plug': None}
    
    try:
        # Debug log
        print(f"[DEBUG] Account Key exists: {bool(UBIBOT_ACCOUNT_KEY)}")
        print(f"[DEBUG] Account Key length: {len(UBIBOT_ACCOUNT_KEY)}")
        
        # Call UbiBot Get Channels API
        url = 'https://webapi.ubibot.com/channels'
        params = {'account_key': UBIBOT_ACCOUNT_KEY}
        
        print(f"[DEBUG] Calling: {url}")
        response = requests.get(url, params=params, timeout=10)
        
        print(f"[DEBUG] Status Code: {response.status_code}")
        
        if response.status_code != 200:
            error_msg = f"UbiBot API Error: {response.status_code} - {response.text[:200]}"
            print(f"[ERROR] {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        data = response.json()
        print(f"[DEBUG] Response keys: {list(data.keys())}")
        
        if 'channels' not in data:
            print(f"[ERROR] No 'channels' in response")
            return jsonify({'error': 'No channels found'}), 500
        
        channels = data['channels']
        print(f"[DEBUG] Found {len(channels)} channels")
        
        for channel in channels:
            device_name = channel.get('name', '')
            device_name_lower = device_name.lower()
            last_values = channel.get('last_values', {})
            
            print(f"[DEBUG] Processing device: '{device_name}'")
            
            # Check for GS1 - exact match with your device name
            if 'gs1' in device_name_lower:
                print(f"[DEBUG] ✅ Matched GS1 Sensor")
                result['gs1_sensor'] = {
                    'temperature': last_values.get('field1'),
                    'humidity': last_values.get('field2'),
                    'soil_temperature': last_values.get('field3'),
                    'soil_humidity': last_values.get('field4'),
                    'soil_ec': last_values.get('field5'),
                    'soil_ph': last_values.get('field6')
                }
                print(f"[DEBUG] GS1 Data: {result['gs1_sensor']}")
            
            # Check for Smart Plug - exact match with your device name
            if 'smart plug' in device_name_lower or 'plug' in device_name_lower:
                print(f"[DEBUG] ✅ Matched Smart Plug")
                result['smart_plug'] = {
                    'switch_status': last_values.get('field1', 0),
                    'socket_voltage': last_values.get('field2'),
                    'socket_current': last_values.get('field3'),
                    'socket_power': last_values.get('field4'),
                    'cumulative_electricity': last_values.get('field5'),
                    'carbon_dioxide': last_values.get('field6')
                }
                print(f"[DEBUG] Plug Data: {result['smart_plug']}")
        
        print(f"[DEBUG] Final result - GS1: {result['gs1_sensor'] is not None}, Plug: {result['smart_plug'] is not None}")
        return jsonify(result)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"[ERROR] Exception: {e}")
        print(f"[ERROR] Traceback: {error_detail}")
        return jsonify({'error': str(e), 'detail': error_detail}), 500

@app.route('/api/history')
def get_history():
    """Fetch historical data"""
    result = {'gs1_sensor': [], 'smart_plug': []}
    
    try:
        # Get all channels
        channels_url = 'https://webapi.ubibot.com/channels'
        channels_params = {'account_key': UBIBOT_ACCOUNT_KEY}
        channels_res = requests.get(channels_url, params=channels_params, timeout=10)
        
        if channels_res.status_code != 200:
            return jsonify(result)
        
        channels_data = channels_res.json()
        
        if 'channels' in channels_data:
            for channel in channels_data['channels']:
                channel_id = channel.get('channel_id')
                device_name = channel.get('name', '').lower()
                
                # Get historical data
                history_url = f'https://webapi.ubibot.com/channels/{channel_id}/data'
                history_params = {
                    'account_key': UBIBOT_ACCOUNT_KEY,
                    'results': 100
                }
                history_res = requests.get(history_url, params=history_params, timeout=10)
                
                if history_res.status_code == 200:
                    history_data = history_res.json()
                    
                    if 'feeds' in history_data:
                        # GS1
                        if 'gs1' in device_name:
                            for feed in history_data['feeds'][:100]:
                                result['gs1_sensor'].append({
                                    'timestamp': feed.get('created_at'),
                                    'temperature': feed.get('field1'),
                                    'humidity': feed.get('field2'),
                                    'soil_temperature': feed.get('field3'),
                                    'soil_humidity': feed.get('field4')
                                })
                        
                        # Smart Plug
                        if 'plug' in device_name:
                            for feed in history_data['feeds'][:100]:
                                result['smart_plug'].append({
                                    'timestamp': feed.get('created_at'),
                                    'socket_power': feed.get('field4'),
                                    'socket_voltage': feed.get('field2'),
                                    'socket_current': feed.get('field3')
                                })
        
        return jsonify(result)
    
    except Exception as e:
        print(f"[ERROR] History error: {e}")
        return jsonify(result)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
    
