import sqlite3

def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    # Kullanıcı mesaj istatistikleri tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS message_stats (
                 user_id INTEGER PRIMARY KEY,
                 message_count INTEGER DEFAULT 0,
                 last_active TIMESTAMP
                 )''')
    
    # Moderasyon işlemleri tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS moderation_actions (
                 action_id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 action_type TEXT,
                 reason TEXT,
                 timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                 )''')
    
    conn.commit()
    conn.close()


def update_message_stats(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('SELECT message_count FROM message_stats WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if row:
        c.execute('UPDATE message_stats SET message_count = message_count + 1, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,))
    else:
        c.execute('INSERT INTO message_stats (user_id, message_count, last_active) VALUES (?, 1, CURRENT_TIMESTAMP)', (user_id,))
    
    conn.commit()
    conn.close()

def add_moderation_action(user_id, action_type, reason):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('INSERT INTO moderation_actions (user_id, action_type, reason) VALUES (?, ?, ?)', (user_id, action_type, reason))
    
    conn.commit()
    conn.close()

def get_moderation_actions(user_id):
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    
    c.execute('SELECT action_type, reason, timestamp FROM moderation_actions WHERE user_id = ?', (user_id,))
    actions = c.fetchall()
    
    conn.close()
    return actions
