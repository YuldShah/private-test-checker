import sqlite3
import uuid


def init_db():
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS user_states (telegram_id INTEGER PRIMARY KEY, status TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_results (user_id INTEGER PRIMARY KEY, test INTEGER, score INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS user_tokens (user_id INTEGER PRIMARY KEY, token TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS user_sessions (telegram_id INTEGER PRIMARY KEY, user_id INTEGER)')
    conn.commit()
    conn.close()


def get_user_state(telegram_id):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('SELECT status FROM user_states WHERE telegram_id = ?', (telegram_id,))
    state = c.fetchone()
    conn.close()
    return state[0] if state else None


def set_user_state(user_id, state):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('REPLACE INTO user_states (telegram_id, status) VALUES (?, ?)', (user_id, state))
    conn.commit()
    conn.close()


def generate_tokens(n):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('DELETE FROM user_tokens')
    for i in range(1, n + 1):
        token = str(uuid.uuid4())
        c.execute('INSERT INTO user_tokens (user_id, token) VALUES (?, ?)', (i, token))
    conn.commit()
    conn.close()


def add_tokens(last, n):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    for i in range(last + 1, last + n + 1):
        token = str(uuid.uuid4())
        c.execute('INSERT INTO user_tokens (user_id, token) VALUES (?, ?)', (i, token))
    conn.commit()
    conn.close()


def get_user_id(user_token):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM user_tokens WHERE token = ?', (user_token,))
    token = c.fetchone()
    conn.close()
    return token[0] if token else None


def setup_user_session(telegram_id, user_id):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('REPLACE INTO user_sessions (telegram_id, user_id) VALUES (?, ?)', (telegram_id, user_id))
    conn.commit()
    conn.close()


def get_user_session_info(telegram_id):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM user_sessions WHERE telegram_id = ?', (telegram_id,))
    session = c.fetchone()
    conn.close()
    return session[0] if session else None


def add_result(user_id, test, score):
    conn = sqlite3.connect('main.db')
    c = conn.cursor()
    c.execute('REPLACE INTO user_results (user_id, test, score) VALUES (?, ?, ?)', (user_id, test, score))
    conn.commit()
    conn.close()
