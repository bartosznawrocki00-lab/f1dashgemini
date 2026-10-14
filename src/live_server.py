from flask import Flask, jsonify
from flask_cors import CORS
import random
from datetime import datetime

app = Flask(__name__)
# CORS pozwala Twojej stronie (na GitHubie lub otwartej lokalnie) bezpiecznie pytać ten serwer o dane
CORS(app) 

@app.route('/api/live')
def live_data():
    """
    Ten endpoint symuluje "pikanie" telemetrii na żywo.
    Za każdym razem gdy strona o to zapyta, wygeneruje minimalnie inne czasy.
    W przyszłości ten fragment zastąpimy nasłuchem prawdziwej telemetrii FastF1!
    """
    
    # Generujemy losowe milisekundy dla uwiarygodnienia akcji
    ms_ver = random.randint(100, 999)
    ms_nor = random.randint(100, 999)
    
    data = [
        {"pos": 1, "number": 1, "driver": "VER", "team": "Red Bull Racing", "gap": "Leader", "lap": f"1:30.{ms_ver}", "tire": "Soft", "tireColor": "bg-red-600 text-white", "status": "track"},
        {"pos": 2, "number": 4, "driver": "NOR", "team": "McLaren", "gap": "+0.215", "lap": f"1:30.{ms_nor}", "tire": "Medium", "tireColor": "bg-yellow-400 text-black", "status": "track"},
        {"pos": 3, "number": 16, "driver": "LEC", "team": "Ferrari", "gap": "+0.512", "lap": f"1:30.{random.randint(100, 999)}", "tire": "Soft", "tireColor": "bg-red-600 text-white", "status": "track"},
        {"pos": 4, "number": 44, "driver": "HAM", "team": "Mercedes", "gap": "+0.840", "lap": f"1:31.{random.randint(100, 999)}", "tire": "Hard", "tireColor": "bg-white text-black", "status": "track"},
        {"pos": 5, "number": 81, "driver": "PIA", "team": "McLaren", "gap": "+1.102", "lap": "IN PIT", "tire": "Medium", "tireColor": "bg-yellow-400 text-black", "status": "pit"},
        {"pos": 6, "number": 14, "driver": "ALO", "team": "Aston Martin", "gap": "+1.450", "lap": f"1:31.{random.randint(100, 999)}", "tire": "Soft", "tireColor": "bg-red-600 text-white", "status": "track"},
        {"pos": 7, "number": 55, "driver": "SAI", "team": "Ferrari", "gap": "+1.600", "lap": f"1:31.{random.randint(100, 999)}", "tire": "Hard", "tireColor": "bg-white text-black", "status": "track"},
        {"pos": 8, "number": 63, "driver": "RUS", "team": "Mercedes", "gap": "+1.950", "lap": f"1:32.{random.randint(100, 999)}", "tire": "Inters", "tireColor": "bg-green-500 text-white", "status": "track"}
    ]
    return jsonify(data)

if __name__ == '__main__':
    print("🚀 Serwer Live Timingu F1 uruchomiony! Nasłuch na porcie 5000...")
    # debug=True sprawia, że serwer sam się zresetuje, gdy zrobisz zmiany w kodzie
    app.run(debug=True, port=5000)
