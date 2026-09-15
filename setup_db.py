import sqlite3

conn = sqlite3.connect('smriti.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS GameSessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    game_type TEXT,
    score INTEGER,
    difficulty TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    stage TEXT DEFAULT 'Early'
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS Locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    latitude REAL,
    longitude REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS CaregiverLinks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    caregiver_id INTEGER NOT NULL,
    patient_id INTEGER NOT NULL,
    FOREIGN KEY (caregiver_id) REFERENCES Users(id),
    FOREIGN KEY (patient_id) REFERENCES Users(id)
)
''')
 
cursor.execute('''
CREATE TABLE IF NOT EXISTS Alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES Users(id)
)
''')
conn.execute('''
    CREATE TABLE IF NOT EXISTS SafeZones (
        patient_id INTEGER PRIMARY KEY,
        center_lat REAL NOT NULL,
        center_lng REAL NOT NULL,
        radius_meters REAL NOT NULL DEFAULT 200,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES Users(id)
    )
''')

conn.execute('''
    CREATE TABLE IF NOT EXISTS Reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        reminder_time TEXT NOT NULL,
        repeat_daily INTEGER DEFAULT 1,
        active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (patient_id) REFERENCES Users(id)
    )
''')

zone = conn.execute('SELECT * FROM SafeZones WHERE patient_id = ?', (data['user_id'],)).fetchone()
if zone:
    dist = haversine_meters(data['latitude'], data['longitude'], zone['center_lat'], zone['center_lng'])
    if dist > zone['radius_meters']:
        conn.execute(
            "INSERT INTO Alerts (user_id, type, status) VALUES (?, ?, ?)",
            (data['user_id'], f"Geofence Breach ({int(dist)}m out)", 'Active')
        )
        conn.commit()

try:
    cursor.execute("ALTER TABLE Users ADD COLUMN role TEXT DEFAULT 'patient'")
except sqlite3.OperationalError:
    pass  
 
try:
    cursor.execute("ALTER TABLE Users ADD COLUMN age INTEGER")
except sqlite3.OperationalError:
    pass  
 
try:
    cursor.execute("ALTER TABLE Users ADD COLUMN gender TEXT")
except sqlite3.OperationalError:
    pass  

try:
    cursor.execute("ALTER TABLE Users ADD COLUMN language TEXT DEFAULT 'English'")
except sqlite3.OperationalError:
    pass  



conn.commit()
conn.close()
print("Database and table created successfully.")