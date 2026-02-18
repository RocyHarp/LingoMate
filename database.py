import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extras import RealDictCursor
import hashlib
import streamlit as st

# 1. Кешуємо ПУЛ з'єднань
@st.cache_resource
def get_pool():
    return ThreadedConnectionPool(1, 20, st.secrets["DB_URL"])

def get_db_connection():
    return get_pool().getconn()

def release_db_connection(conn):
    get_pool().putconn(conn)

# 2. МЕГА-ВАЖЛИВО: Кешуємо створення таблиць (виконається ЛИШЕ 1 раз!)
@st.cache_resource
def init_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, username TEXT UNIQUE, email TEXT UNIQUE, password TEXT, is_premium INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS words (id SERIAL PRIMARY KEY, user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, word TEXT, meaning TEXT, word_type TEXT, correct_count INTEGER DEFAULT 0, wrong_count INTEGER DEFAULT 0, parent_id INTEGER DEFAULT NULL, nuance TEXT DEFAULT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS global_stats (user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE, stat_value INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS daily_training (user_id INTEGER REFERENCES users(id) ON DELETE CASCADE, train_date DATE DEFAULT CURRENT_DATE, time_spent INTEGER DEFAULT 0, correct_count INTEGER DEFAULT 0, wrong_count INTEGER DEFAULT 0, PRIMARY KEY (user_id, train_date))''')
        conn.commit()
    except Exception as e: print("DB Init Error:", e)
    finally:
        if conn: release_db_connection(conn)

def register_user(username, email, password):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username.strip(), email.strip(), hashed_pw))
        conn.commit()
        return True
    except psycopg2.IntegrityError: return False
    finally:
        if conn: release_db_connection(conn)

def login_user(username, password):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('SELECT id, is_premium FROM users WHERE username = %s AND password = %s', (username, hashed_pw))
        return cursor.fetchone()
    except: return None
    finally:
        if conn: release_db_connection(conn)

# --- ФУНКЦІЇ ЧИТАННЯ (Запам'ятовуємо результати, щоб не літати в БД) ---

@st.cache_data(show_spinner=False)
def get_all_words(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM words WHERE user_id = %s ORDER BY id DESC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    except: return []
    finally:
        if conn: release_db_connection(conn)

def get_grouped_words(user_id):
    all_w = get_all_words(user_id)
    parents, children_map = [], {}
    for w in all_w:
        if w['parent_id'] is None:
            w['synonyms'] = []
            parents.append(w)
        else:
            pid = w['parent_id']
            if pid not in children_map: children_map[pid] = []
            children_map[pid].append(w)
    for p in parents:
        if p['id'] in children_map: p['synonyms'] = children_map[p['id']]
    return parents

def get_word_by_text(user_id, word_text):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM words WHERE user_id = %s AND word = %s', (user_id, word_text.strip()))
        row = cursor.fetchone()
        return dict(row) if row else None
    except: return None
    finally:
        if conn: release_db_connection(conn)

@st.cache_data(show_spinner=False)
def get_statistics(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT stat_value FROM global_stats WHERE user_id = %s', (user_id,))
        res = cursor.fetchone()
        total_trans = res[0] if res else 0
        cursor.execute('SELECT SUM(correct_count), SUM(wrong_count) FROM words WHERE user_id = %s', (user_id,))
        row = cursor.fetchone()
        return {"translations": total_trans, "correct": row[0] if row and row[0] else 0, "wrong": row[1] if row and row[1] else 0}
    except: return {"translations": 0, "correct": 0, "wrong": 0}
    finally:
        if conn: release_db_connection(conn)

@st.cache_data(show_spinner=False)
def get_daily_training_stats(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT train_date, time_spent, correct_count, wrong_count FROM daily_training WHERE user_id = %s ORDER BY train_date ASC', (user_id,))
        return [dict(row) for row in cursor.fetchall()]
    except: return []
    finally:
        if conn: release_db_connection(conn)


# --- ФУНКЦІЇ ЗАПИСУ (При зміні даних ми очищаємо кеш) ---

def clear_db_cache():
    # Очищаємо збережені дані, щоб інтерфейс оновився
    st.cache_data.clear()

def save_word(user_id, word, meaning, word_type):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM words WHERE user_id = %s AND word = %s', (user_id, word.strip()))
        if cursor.fetchone(): return False
        cursor.execute('INSERT INTO words (user_id, word, meaning, word_type, correct_count, wrong_count) VALUES (%s, %s, %s, %s, 0, 0)', (user_id, word.strip(), meaning.strip(), word_type.strip()))
        conn.commit()
        clear_db_cache()
        return True
    except: return False
    finally:
        if conn: release_db_connection(conn)

def save_synonym(user_id, parent_id, word, meaning, nuance):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO words (user_id, word, meaning, word_type, correct_count, wrong_count, parent_id, nuance) VALUES (%s, %s, %s, 'synonym', 0, 0, %s, %s)''', (user_id, word.strip(), meaning.strip(), parent_id, nuance.strip()))
        conn.commit()
        clear_db_cache()
        return True
    except: return False
    finally:
        if conn: release_db_connection(conn)

def update_word_meaning(user_id, word_text, new_meaning):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE words SET meaning = %s WHERE user_id = %s AND word = %s', (new_meaning.strip(), user_id, word_text.strip()))
        conn.commit()
        clear_db_cache()
        return True
    except: return False
    finally:
        if conn: release_db_connection(conn)

def delete_word(user_id, word_text):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM words WHERE user_id = %s AND word = %s', (user_id, word_text))
        conn.commit()
        clear_db_cache()
        return True
    except: return False
    finally:
        if conn: release_db_connection(conn)

def reset_word_stats(user_id, word):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE words SET correct_count = 0, wrong_count = 0 WHERE user_id = %s AND word = %s', (user_id, word))
        conn.commit()
        clear_db_cache()
        return True
    except: return False
    finally:
        if conn: release_db_connection(conn)

def increment_translation_count(user_id):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO global_stats (user_id, stat_value) VALUES (%s, 0) ON CONFLICT (user_id) DO NOTHING', (user_id,))
        cursor.execute('UPDATE global_stats SET stat_value = stat_value + 1 WHERE user_id = %s', (user_id,))
        conn.commit()
        clear_db_cache()
    except: pass
    finally:
        if conn: release_db_connection(conn)

def update_word_stats(user_id, word, is_correct):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if is_correct: cursor.execute('UPDATE words SET correct_count = correct_count + 1 WHERE user_id = %s AND word = %s', (user_id, word))
        else: cursor.execute('UPDATE words SET wrong_count = wrong_count + 1 WHERE user_id = %s AND word = %s', (user_id, word))
        conn.commit()
        clear_db_cache()
    except: pass
    finally:
        if conn: release_db_connection(conn)

def update_daily_training_stats(user_id, is_correct, time_spent_sec):
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO daily_training (user_id, train_date, time_spent, correct_count, wrong_count) VALUES (%s, CURRENT_DATE, 0, 0, 0) ON CONFLICT (user_id, train_date) DO NOTHING''', (user_id,))
        if is_correct is True:
            cursor.execute("UPDATE daily_training SET correct_count = correct_count + 1, time_spent = time_spent + %s WHERE user_id = %s AND train_date = CURRENT_DATE", (int(time_spent_sec), user_id))
        elif is_correct is False:
            cursor.execute("UPDATE daily_training SET wrong_count = wrong_count + 1, time_spent = time_spent + %s WHERE user_id = %s AND train_date = CURRENT_DATE", (int(time_spent_sec), user_id))
        conn.commit()
        clear_db_cache()
    except: pass
    finally:
        if conn: release_db_connection(conn)