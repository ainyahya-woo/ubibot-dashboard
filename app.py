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
        # Call UbiBot Get Channels API - get ALL devices at once!
        url = 'https://webapi.ubibot.com/channels'
        params = {'account_key': UBIBOT_ACCOUNT_KEY}
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'channels' in data:
                for channel in data['channels']:
                    device_name = channel.get('name', '').lower()
                    last_values = channel.get('last_values', {})
                    
                    # Identify GS1 sensor (check name contains 'gs1' or 'agricultural')
                    if 'gs1' in device_name or 'agricultural' in device_name or 'sensor' in device_name:
                        result['gs1_sensor'] = {
                            'temperature': last_values.get('field1'),
                            'humidity': last_values.get('field2'),
                            'soil_temperature': last_values.get('field3'),
                            'soil_humidity': last_values.get('field4'),
                            'soil_ec': last_values.get('field5'),
                            'soil_ph': last_values.get('field6')
                        }
                    
                    # Identify Smart Plug (check name contains 'plug' or 'socket')
                    elif 'plug' in device_name or 'socket' in device_name or 'sp1' in device_name:
                        result['smart_plug'] = {
                            'switch_status': last_values.get('field1', 0),
                            'socket_voltage': last_values.get('field2'),
                            'socket_current': last_values.get('field3'),
                            'socket_power': last_values.get('field4'),
                            'cumulative_electricity': last_values.get('field5'),
                            'carbon_dioxide': last_values.get('field6')
                        }
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history')
def get_history():
    """Fetch historical data"""
    result = {'gs1_sensor': [], 'smart_plug': []}
    
    try:
        # Get all channels first to identify channel IDs
        channels_url = 'https://webapi.ubibot.com/channels'
        channels_params = {'account_key': UBIBOT_ACCOUNT_KEY}
        channels_res = requests.get(channels_url, params=channels_params, timeout=10)
        
        if channels_res.status_code == 200:
            channels_data = channels_res.json()
            
            if 'channels' in channels_data:
                for channel in channels_data['channels']:
                    channel_id = channel.get('channel_id')
                    device_name = channel.get('name', '').lower()
                    
                    # Get historical data for each channel
                    history_url = f'https://webapi.ubibot.com/channels/{channel_id}/data'
                    history_params = {
                        'account_key': UBIBOT_ACCOUNT_KEY,
                        'results': 100
                    }
                    history_res = requests.get(history_url, params=history_params, timeout=10)
                    
                    if history_res.status_code == 200:
                        history_data = history_res.json()
                        
                        if 'feeds' in history_data:
                            # Check if GS1 or Smart Plug
                            if 'gs1' in device_name or 'agricultural' in device_name or 'sensor' in device_name:
                                for feed in history_data['feeds'][:100]:
                                    result['gs1_sensor'].append({
                                        'timestamp': feed.get('created_at'),
                                        'temperature': feed.get('field1'),
                                        'humidity': feed.get('field2'),
                                        'soil_temperature': feed.get('field3'),
                                        'soil_humidity': feed.get('field4')
                                    })
                            
                            elif 'plug' in device_name or 'socket' in device_name or 'sp1' in device_name:
                                for feed in history_data['feeds'][:100]:
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
