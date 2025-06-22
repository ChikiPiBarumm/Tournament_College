import sqlite3

# Connect to SQLite database (creates new database if not exists)
conn = sqlite3.connect('tournament_management.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Create Participants table
cursor.execute('''CREATE TABLE IF NOT EXISTS Participants (
                    ParticipantID INTEGER PRIMARY KEY,
                    Name TEXT UNIQUE,
                    TeamID INTEGER,
                    FOREIGN KEY (TeamID) REFERENCES Teams(TeamID)
                )''')

# Create Teams table
cursor.execute('''CREATE TABLE IF NOT EXISTS Teams (
                    TeamID INTEGER PRIMARY KEY,
                    TeamName TEXT UNIQUE
                )''')

# Create Events table
cursor.execute('''CREATE TABLE IF NOT EXISTS Events (
                    EventID INTEGER PRIMARY KEY,
                    EventName TEXT,
                    EventType TEXT,
                    PointsAllocated INTEGER
                )''')

# Create EventParticipants table
cursor.execute('''CREATE TABLE IF NOT EXISTS EventParticipants (
                    EventParticipantID INTEGER PRIMARY KEY,
                    EventID INTEGER,
                    ParticipantID INTEGER,
                    TeamID INTEGER,
                    PointsEarned INTEGER,
                    FOREIGN KEY (ParticipantID) REFERENCES Participants(ParticipantID),
                    FOREIGN KEY (TeamID) REFERENCES Teams(TeamID),
                    FOREIGN KEY (EventID) REFERENCES Events(EventID)
                )''')

events_data = [
    ('Capture the Flag', 'Team-based', 40),
    ('Quiz Bowl', 'Team-based', 40),
    ('Escape Room Challenge', 'Team-based', 40),
    ('Scavenger Hunt', 'Team-based', 40),
    ('Tug-of-War Tournament', 'Team-based', 40),
    ('Stand-Up Comedy Competition', 'Individual', 110),
    ('Mathematics Olympiad', 'Individual', 110),
    ('Solo Chess Tournament', 'Individual', 110),
    ('Cross-Country Race', 'Individual', 110),
    ('Debate Competition', 'Individual', 110)
]

cursor.executemany('''INSERT INTO Events (EventName, EventType, PointsAllocated)
                      VALUES (?, ?, ?)''', events_data)

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database created successfully.")
