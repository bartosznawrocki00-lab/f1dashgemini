from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import threading
import fastf1
import pandas as pd

app = Flask(__name__)
CORS(app)

RACE_YEAR = 2024
RACE_ID = 1  # GP Bahrajnu
SESSION_TYPE = 'R'

race_laps = None
is_loading = True

def load_fastf1_data():
    global race_laps, is_loading
    try:
        print("🚀 Pobieranie telemetrii FastF1...")
        cache_dir = '/tmp/fastf1_cache'
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
        session = fastf1.get_session(RACE_YEAR, RACE_ID, SESSION_TYPE)
        session.load(telemetry=False, weather=False, messages=False)
        race_laps = session.laps
        print("✅ Dane wczytane!")
    except Exception as e:
        print("❌ Błąd:", e)
    finally:
        is_loading = False

threading.Thread(target=load_fastf1_data).start()

@app.route('/api/live')
def live_data():
    # Zwracamy obiekt ze statusem, aby strona wiedziała, czy serwer się jeszcze ładuje
    if is_loading or race_laps is None or race_laps.empty:
        return jsonify({"status": "loading", "max_lap": 0, "current_lap": 0, "data": []})
        
    max_lap = int(race_laps['LapNumber'].max())
    # Pobieramy numer okrążenia z zapytania URL (np. /api/live?lap=15). Domyślnie 1.
    req_lap = request.args.get('lap', default=1, type=int)
    
    # Zabezpieczenia zakresu
    if req_lap > max_lap: req_lap = max_lap
    if req_lap < 1: req_lap = 1
        
    laps_up_to_now = race_laps[race_laps['LapNumber'] <= req_lap]
    latest_laps = laps_up_to_now.groupby('Driver').last().reset_index()
    latest_laps = latest_laps.sort_values(by='Time')
    
    formatted_data = []
    pos = 1
    
    for index, row in latest_laps.iterrows():
        compound = str(row['Compound'])
        tire_color = "bg-neutral-600 text-white"
        if compound == 'SOFT': tire_color = "bg-red-600 text-white"
        elif compound == 'MEDIUM': tire_color = "bg-yellow-400 text-black"
        elif compound == 'HARD': tire_color = "bg-white text-black"
        elif compound == 'INTERMEDIATE': tire_color = "bg-green-500 text-white"
        elif compound == 'WET': tire_color = "bg-blue-500 text-white"
        
        lap_time = row['LapTime']
        if pd.isnull(lap_time):
            lap_str = "OUT"
        else:
            total_seconds = lap_time.total_seconds()
            m = int(total_seconds // 60)
            s = int(total_seconds % 60)
            ms = int((total_seconds - (m * 60) - s) * 1000)
            lap_str = f"{m}:{s:02d}.{ms:03d}"
            
        status = "pit" if not pd.isnull(row['PitInTime']) else "track"

        formatted_data.append({
            "pos": pos,
            "number": str(row['DriverNumber']),
            "driver": str(row['Driver']),
            "team": str(row['Team']),
            "gap": f"Okrążenie {int(row['LapNumber'])}", 
            "lap": lap_str,
            "tire": compound if compound != 'nan' else "?",
            "tireColor": tire_color,
            "status": status
        })
        pos += 1
        
    return jsonify({
        "status": "ready", 
        "max_lap": max_lap, 
        "current_lap": req_lap, 
        "data": formatted_data
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
