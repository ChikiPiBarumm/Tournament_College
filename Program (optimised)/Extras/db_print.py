import sqlite3


def print_table(cursor, table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    print(f"\n{table_name}:")
    for row in rows:
        print(row)


# Connect to SQLite database
conn = sqlite3.connect('tournament_management.db')

# Create a cursor object to execute SQL commands
cursor = conn.cursor()

# Print each table
tables = ['Participants', 'Teams', 'Events', 'EventParticipants']
for table in tables:
    print_table(cursor, table)

# Close the connection
conn.close()
