from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import threading
import fastf1
import pandas as pd

app = Flask(__name__)
CORS(app)

RACE_YEAR = 2024
RACE_ID = 1  # Bahrajn
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
        print("✅ Dane wczytane! Pełny wyścig gotowy.")
    except Exception as e:
        print("❌ Błąd:", e)
    finally:
        is_loading = False

threading.Thread(target=load_fastf1_data).start()

# Funkcja pomocnicza: ładne formatowanie straty do lidera
def format_timedelta(td):
    if pd.isnull(td): return ""
    total_seconds = td.total_seconds()
    if total_seconds < 0: return ""
    m = int(total_seconds // 60)
    s = int(total_seconds % 60)
    ms = int((total_seconds - (m * 60) - s) * 1000)
    if m > 0: return f"+{m}:{s:02d}.{ms:03d}"
    else: return f"+{s}.{ms:03d}"

# Funkcja pomocnicza: czas pojedynczego okrążenia
def format_laptime(td):
    if pd.isnull(td): return "Brak"
    total_seconds = td.total_seconds()
    m = int(total_seconds // 60)
    s = int(total_seconds % 60)
    ms = int((total_seconds - (m * 60) - s) * 1000)
    return f"{m}:{s:02d}.{ms:03d}"

@app.route('/api/live')
def live_data():
    if is_loading or race_laps is None or race_laps.empty:
        return jsonify({"status": "loading", "max_lap": 0, "current_lap": 0, "data": []})
        
    max_lap = int(race_laps['LapNumber'].max())
    req_lap = request.args.get('lap', default=1, type=int)
    
    if req_lap > max_lap: req_lap = max_lap
    if req_lap < 1: req_lap = 1
        
    laps_up_to_now = race_laps[race_laps['LapNumber'] <= req_lap]
    
    # Krok 1: Znajdź OSTATNIE zaliczone okrążenie dla każdego kierowcy w tym momencie wyścigu
    idx = laps_up_to_now.groupby('Driver')['LapNumber'].idxmax()
    latest_laps = laps_up_to_now.loc[idx]
    
    # Krok 2: Prawdziwe sortowanie F1 (najpierw liczba okrążeń, potem łączny czas)
    latest_laps = latest_laps.sort_values(by=['LapNumber', 'Time'], ascending=[False, True])
    
    # Krok 3: Namierzamy lidera, aby od niego obliczać różnice!
    leader = latest_laps.iloc[0]
    leader_lap_num = leader['LapNumber']
    leader_time = leader['Time']
    
    formatted_data = []
    pos = 1
    
    for index, row in latest_laps.iterrows():
        driver = str(row['Driver'])
        compound = str(row['Compound'])
        
        tire_color = "bg-neutral-600 text-white"
        if compound == 'SOFT': tire_color = "bg-red-600 text-white"
        elif compound == 'MEDIUM': tire_color = "bg-yellow-400 text-black"
        elif compound == 'HARD': tire_color = "bg-white text-black"
        elif compound == 'INTERMEDIATE': tire_color = "bg-green-500 text-white"
        elif compound == 'WET': tire_color = "bg-blue-500 text-white"
        
        lap_str = format_laptime(row['LapTime'])
        
        # Sprawdzamy maksymalne kółko kierowcy w CAŁYM wyścigu, żeby wykryć wycofanie (DNF)
        driver_max_lap = race_laps[race_laps['Driver'] == driver]['LapNumber'].max()
        
        status = "track"
        gap = ""
        
        # Logika zjazdów do boksu
        if not pd.isnull(row['PitInTime']):
            status = "pit"
            
        # Logika strat i wycofań (DNF)
        if pos == 1:
            gap = "Leader"
        else:
            if driver_max_lap == row['LapNumber'] and req_lap > row['LapNumber'] + 1:
                # Jeśli wyścig odjechał, a on został w miejscu - DNF
                gap = "DNF"
                status = "out"
                lap_str = "OUT"
            elif row['LapNumber'] < leader_lap_num:
                # Zdublowany
                laps_behind = int(leader_lap_num - row['LapNumber'])
                gap = f"+{laps_behind} LAP"
            else:
                # Zwykła strata na torze (sekundy)
                time_diff = row['Time'] - leader_time
                gap = format_timedelta(time_diff)

        formatted_data.append({
            "pos": pos,
            "number": str(row['DriverNumber']),
            "driver": driver,
            "team": str(row['Team']),
            "gap": gap, 
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
