from flask import Flask, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app) 

@app.route('/api/live')
def live_data():
    try:
        # 1. Pobieramy w ułamku sekundy prawdziwe dane z ostatniego wyścigu F1
        url = "https://api.jolpi.ca/ergast/f1/current/last/results.json"
        response = requests.get(url, timeout=5)
        raw_data = response.json()
        
        # 2. Wyciągamy mięso, czyli samą tabelę wyników
        results = raw_data['MRData']['RaceTable']['Races'][0]['Results']
        
        formatted_data = []
        # 3. Analizujemy pierwszą dziesiątkę (możesz usunąć [:10], żeby pobrać wszystkich)
        for item in results[:10]: 
            # Logika straty do lidera (Gap)
            status = item['status']
            gap = item.get('Time', {}).get('time', status)
            if item['position'] == "1":
                gap = "Leader"
                
            # Historyczne API nie przechowuje niestety opon, 
            # więc na czas testu symulujemy, że parzyści mają Soft, a nieparzyści Medium
            is_even = int(item['position']) % 2 == 0
            
            # 4. Tłumaczymy dane na format JSON dla Twojego Alpine.js
            formatted_data.append({
                "pos": item['position'],
                "number": item['number'],
                "driver": item['Driver'].get('code', item['Driver']['familyName'][:3].upper()),
                "team": item['Constructor']['name'],
                "gap": gap,
                "lap": item.get('FastestLap', {}).get('Time', {}).get('time', 'Brak czasu'),
                "tire": "Soft" if is_even else "Medium",
                "tireColor": "bg-red-600 text-white" if is_even else "bg-yellow-400 text-black",
                "status": "pit" if status != "Finished" and "+1" not in status else "track"
            })
            
        # Zwracamy czystą tablicę do Twojej strony
        return jsonify(formatted_data)
        
    except Exception as e:
        print("Błąd pobierania z API:", e)
        # W razie awarii API, wysyłamy pustą listę żeby nie zepsuć strony
        return jsonify([])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
