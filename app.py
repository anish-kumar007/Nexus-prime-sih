from flask import Flask, jsonify, request
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect("smriti.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def home():
    return "Hello, Nexus Prime!"

@app.route('/api/set_stage', methods=['POST'])
def set_stage():
    data = request.get_json() or {}
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Users (id, name, stage) VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET stage = excluded.stage
    ''', (data['user_id'], data.get('name', 'Patient'), data['stage']))
    conn.commit(); conn.close()
    return jsonify({"status": "success", "stage": data['stage']})

@app.route('/api/save_score', methods=['POST'])
def save_score():
    data = request.get_json() or {}
    for field in ('user_id', 'game_type', 'score'):
        if field not in data:
            return jsonify({"status":"error", "message":f"Missing field: {field}"}), 400

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO GameSessions (user_id, game_type, score, difficulty)
        VALUES (?, ?, ?, ?)
    ''', (int(data['user_id']), data['game_type'], int(data['score']), data.get('difficulty', 'Easy')))
    conn.commit(); conn.close()
    return jsonify({"status":"success", "message":"Score saved to database"})

@app.route('/api/progress/<int:user_id>')
def get_progress(user_id):
    conn = get_db_connection()

    rows = conn.execute('''
        SELECT game_type, score, difficulty, timestamp
        FROM GameSessions
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user_id,)).fetchall()

    total_games = conn.execute('''
        SELECT COUNT(*) AS count FROM GameSessions WHERE user_id = ?
    ''', (user_id,)).fetchone()['count']

    word_picture = conn.execute('''
        SELECT MAX(score) AS best, COUNT(*) AS count
        FROM GameSessions
        WHERE user_id = ? AND game_type = 'word_picture_match'
    ''', (user_id,)).fetchone()

    conn.close()

    return jsonify({
        "user_id": user_id,
        "total_games": total_games,
        "word_picture_best": word_picture['best'] or 0,
        "word_picture_games": word_picture['count'] or 0,
        "history": [dict(row) for row in rows]
    })

@app.route('/api/update_location', methods=['POST'])
def update_location():
    data = request.get_json() or {}
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Locations (user_id, latitude, longitude)
        VALUES (?, ?, ?)
    ''', (data['user_id'], data['latitude'], data['longitude']))
    conn.commit(); conn.close()
    return jsonify({"status":"success", "recieved":data})

@app.route('/api/latest_location/<int:user_id>')
def latest_location(user_id):
    conn = get_db_connection()
    row = conn.execute('''
        SELECT latitude, longitude, timestamp FROM Locations
        WHERE user_id = ? ORDER BY id DESC LIMIT 1
    ''', (user_id,)).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error":"No location recorded yet"}), 404
    return jsonify(dict(row))

@app.route('/api/register_patient', methods=['POST'])
def register_patient():
    data = request.get_json() or {}
    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO Users (name, age, gender, language, stage, role)
        VALUES (?, ?, ?, ?, ?, 'patient')
    ''', (data.get('name','Patient'), data.get('age'), data.get('gender'),
          data.get('language','English'), data.get('stage','Early')))
    new_id = cursor.lastrowid
    conn.commit(); conn.close()
    return jsonify({"status":"success", "user_id":new_id})

@app.route('/api/register_caregiver', methods=['POST'])
def register_caregiver():
    data = request.get_json() or {}
    conn = get_db_connection()
    cursor = conn.execute("INSERT INTO Users (name, role) VALUES (?, 'caregiver')", (data.get('name','Caregiver'),))
    new_id = cursor.lastrowid
    conn.commit(); conn.close()
    return jsonify({"status":"success", "user_id":new_id})

@app.route('/api/link_caregiver', methods=['POST'])
def link_caregiver():
    data = request.get_json() or {}
    conn = get_db_connection()
    conn.execute('INSERT INTO CaregiverLinks (caregiver_id, patient_id) VALUES (?, ?)',
                 (data['caregiver_id'], data['patient_id']))
    conn.commit(); conn.close()
    return jsonify({"status":"success"})

@app.route('/api/caregiver/<int:caregiver_id>/patients')
def get_linked_patients(caregiver_id):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT Users.id, Users.name, Users.stage
        FROM CaregiverLinks JOIN Users ON Users.id = CaregiverLinks.patient_id
        WHERE CaregiverLinks.caregiver_id = ?
    ''', (caregiver_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/trigger_alert', methods=['POST'])
def trigger_alert():
    data = request.get_json() or {}
    conn = get_db_connection()
    conn.execute('INSERT INTO Alerts (user_id, type, status) VALUES (?, ?, ?)',
                 (data['user_id'], data['type'], 'Active'))
    conn.commit(); conn.close()
    return jsonify({"status":"success"})

@app.route('/api/alerts/<int:user_id>')
def get_alerts(user_id):
    conn = get_db_connection()
    rows = conn.execute('''
        SELECT type, status, timestamp FROM Alerts
        WHERE user_id = ? ORDER BY id DESC LIMIT 5
    ''', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
