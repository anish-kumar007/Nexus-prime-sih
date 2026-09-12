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
    data = request.get_json()
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO Users (id, name, stage) VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET stage = excluded.stage
    ''', (data['user_id'], data.get('name', 'Patient'), data['stage']))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "stage": data['stage']})

@app.route('/api/save_score', methods=['POST'])
def save_score():
    data = request.get_json()
    conn = get_db_connection()
    conn.execute('INSERT INTO GameSessions (user_id, game_type, score, difficulty) VALUES (?, ?, ?, ?)',
        (data['user_id'], data['game_type'], data['score'], data.get('difficulty', 'Easy')))
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "message": "Score saved to database"})


@app.route('/api/progress/<int:user_id>')
def get_progress(user_id):
    conn = get_db_connection()
    rows = conn.execute(
        'SELECT game_type, score, difficulty, timestamp FROM GameSessions WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    conn.close()
    results = [dict(row) for row in rows]
    return jsonify({"user_id": user_id, "history": results})


@app.route('/api/update_location', methods=['POST'])
def update_location():
    data = request.get_json()
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO Locations (user_id, latitude, longitude) VALUES (?, ?, ?)',
        (data['user_id'], data['latitude'], data['longitude'])
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "success", "recieved": data})

@app.route('/api/latest_location/<int:user_id>')
def latest_location(user_id):
    conn = get_db_connection()
    row = conn.execute(
        'SELECT latitude, longitude, timestamp FROM Locations WHERE user_id = ? ORDER BY id DESC LIMIT 1',
        (user_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return jsonify({"error": "No location recorded yet"}), 404
    return jsonify(dict(row))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)