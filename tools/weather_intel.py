#!/usr/bin/env python3
"""
Claw Weather Intelligence
Advanced weather monitoring and alerts
"""

import subprocess
import json
import os
from datetime import datetime

LOCATION = "Holyrood,Newfoundland"
LOG_FILE = "/config/clawd/memory/weather_log.jsonl"

def get_weather_data():
    """Fetch weather data from wttr.in"""
    try:
        # Get structured data
        result = subprocess.run(
            ["curl", "-s", f"wttr.in/{LOCATION}?format=j1"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except:
        return None

def get_simple_weather():
    """Get simple weather string"""
    try:
        result = subprocess.run(
            ["curl", "-s", f"wttr.in/{LOCATION}?format=%C:+%t"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except:
        return None

def analyze_weather(weather_data):
    """Analyze weather conditions"""
    if not weather_data:
        return None
    
    try:
        current = weather_data.get('current_condition', [{}])[0]
        
        temp = current.get('temp_C', '?')
        feels_like = current.get('FeelsLikeC', '?')
        condition = current.get('weatherDesc', [{}])[0].get('value', 'Unknown')
        wind_speed = current.get('windspeedKmph', '?')
        humidity = current.get('humidity', '?')
        visibility = current.get('visibility', '?')
        
        analysis = {
            'temperature': temp,
            'feels_like': feels_like,
            'condition': condition,
            'wind_speed': wind_speed,
            'humidity': humidity,
            'visibility': visibility,
            'is_severe': False,
            'alerts': []
        }
        
        # Check for severe conditions
        if int(temp) < -10:
            analysis['is_severe'] = True
            analysis['alerts'].append(f"Extreme cold: {temp}°C")
        
        if int(temp) > 30:
            analysis['is_severe'] = True
            analysis['alerts'].append(f"Extreme heat: {temp}°C")
        
        if int(wind_speed) > 50:
            analysis['is_severe'] = True
            analysis['alerts'].append(f"High winds: {wind_speed} km/h")
        
        if int(visibility) < 2:
            analysis['is_severe'] = True
            analysis['alerts'].append(f"Low visibility: {visibility} km")
        
        return analysis
        
    except Exception as e:
        return {'error': str(e)}

def log_weather(analysis):
    """Log weather data"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'location': LOCATION,
        'analysis': analysis
    }
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def generate_weather_summary(analysis):
    """Generate human-readable summary"""
    if not analysis:
        return "Unable to fetch weather data"
    
    if 'error' in analysis:
        return f"Error: {analysis['error']}"
    
    summary = f"🌤️ Weather in Holyrood:\n"
    summary += f"   Condition: {analysis['condition']}\n"
    summary += f"   Temperature: {analysis['temperature']}°C (feels like {analysis['feels_like']}°C)\n"
    summary += f"   Wind: {analysis['wind_speed']} km/h\n"
    summary += f"   Humidity: {analysis['humidity']}%\n"
    
    if analysis['alerts']:
        summary += f"\n⚠️ Alerts:\n"
        for alert in analysis['alerts']:
            summary += f"   • {alert}\n"
    
    return summary

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        # Quick simple output
        weather = get_simple_weather()
        if weather:
            print(f"🌤️ {weather}")
        else:
            print("❌ Unable to fetch weather")
        return
    
    print("🦅 Weather Intelligence")
    print("=" * 40)
    
    # Fetch data
    weather_data = get_weather_data()
    
    if not weather_data:
        print("❌ Failed to fetch weather data")
        return
    
    # Analyze
    analysis = analyze_weather(weather_data)
    
    # Log
    log_weather(analysis)
    
    # Display
    print(generate_weather_summary(analysis))
    
    # Return code for scripting
    if analysis and analysis.get('is_severe'):
        print("\n🚨 SEVERE WEATHER DETECTED")
        return 1
    
    print("\n✅ Weather check complete")
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
