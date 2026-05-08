import sqlite3
from datetime import datetime
import os

DB_FOLDER = r"C:\Users\Acer\CS - Project\data"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)
Trackit_DB = os.path.join(DB_FOLDER, "Trackit.db")


def init_db():
    connection = sqlite3.connect(Trackit_DB)
    cursor = connection.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE, 
        password TEXT VARCHAR(16) NOT NULL
    )
    ''')
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task_name TEXT NOT NULL,
        due_date TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        completed_on TEXT,
        FOREIGN KEY(user_id) REFERENCES user_profile(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT,
        content TEXT,
        FOREIGN KEY(user_id) REFERENCES user_profile(id)
    )
    """)
    connection.commit()
    connection.close()

def get_user_profile(id=None, name=None):
    conn = sqlite3.connect(Trackit_DB)
    conn.row_factory = sqlite3.Row 
    c = conn.cursor()
    
    if id:
        c.execute("SELECT * FROM user_profile WHERE id = ?", (id,))
    elif name:
        c.execute("SELECT * FROM user_profile WHERE name = ?", (name,))
    else:
        c.execute("SELECT * FROM user_profile LIMIT 1")
    
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def save_user_profile(profile):
    conn = sqlite3.connect(Trackit_DB)
    c = conn.cursor()
    user_id = profile.get('id')
    if user_id:
        c.execute("""
        UPDATE user_profile SET name=?, password=? WHERE id=?
        """, (profile['Name'], profile['Password'], user_id))
    else:
        c.execute("""
        INSERT INTO user_profile (name, password) VALUES (?, ?)
        """, (profile['Name'], profile['Password']))
    
    conn.commit()
    conn.close()

def get_tasks(user_id=None):
    import sqlite3
    conn = sqlite3.connect(Trackit_DB) 
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    if user_id:
        cursor.execute("""
            SELECT id, task_name AS name, due_date AS due, status 
            FROM tasks 
            WHERE user_id = ?
        """, (user_id,))
    else:
        cursor.execute("SELECT id, task_name AS name, due_date AS due, status FROM tasks")
        
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_task(task_data):
    conn = sqlite3.connect(Trackit_DB)
    c = conn.cursor()

    # Use .get() so it returns None instead of crashing if 'due' is missing
    due_date = task_data.get('due') 
    
    # If 'due' is missing, maybe try 'due_date' just in case?
    if not due_date:
        due_date = task_data.get('due_date')

    if isinstance(due_date, str):
        due_date_obj = datetime.strptime(due_date, "%Y-%m-%d").date()
    else:
        due_date_obj = due_date

    # Use the logic we built
    if due_date_obj and due_date_obj < datetime.now().date():
        status = "Late"
    else:
        status = task_data.get('status', 'Pending')

    query = """
    INSERT INTO tasks (user_id, task_name, due_date, status) 
    VALUES (?, ?, ?, ?)
    """

    c.execute(query, (
        task_data.get('user_id'), 
        task_data.get('task_name'), 
        due_date, 
        status
    ))
    
    conn.commit()
    conn.close()

def update_task_status(task_id, status):
    conn = sqlite3.connect(Trackit_DB)
    c = conn.cursor()
    completed_on = datetime.now().strftime("%Y-%m-%d") if status == 'Completed' else None
    c.execute("""
    UPDATE tasks SET status=?, completed_on=? WHERE id=?
    """, (status, completed_on, task_id))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = sqlite3.connect(Trackit_DB)
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def get_notes():
    user = get_user_profile()
    if not user: return []
    conn = sqlite3.connect(Trackit_DB)
    c = conn.cursor()
    c.execute("SELECT id, title, content FROM notes WHERE user_id=?", (user['id'],))
    rows = c.fetchall()
    conn.close()
    notes = []
    for r in rows:
        notes.append({"id": r[0], "title": r[1], "content": r[2]})
    return notes

def save_note(note):
    user = get_user_profile()
    if not user: return
    conn = sqlite3.connect(Trackit_DB)
    c = conn.cursor()
    if 'id' in note:
        c.execute("UPDATE notes SET title=?, content=? WHERE id=?", (note['title'], note['content'], note['id']))
    else:
        c.execute("INSERT INTO notes (user_id, title, content) VALUES (?, ?, ?)", (user['id'], note['title'], note['content']))
    conn.commit()
    conn.close()

def delete_note(note_id):
    import sqlite3
    conn = sqlite3.connect(Trackit_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()
    conn.close()
    
