import database as db

# 🏆 СПИСОК УСІХ ДОСЯГНЕНЬ (З винагородами XP)
ALL_ACHIEVEMENTS = [
    {"id": "w1", "icon": "🌱", "name": "Перший паросток", "desc": "Збережи 1 слово", "req_w": 1, "req_t": 0, "req_c": 0, "xp": 50},
    {"id": "w50", "icon": "📖", "name": "Книжковий черв'як", "desc": "Збережи 50 слів", "req_w": 50, "req_t": 0, "req_c": 0, "xp": 200},
    {"id": "w200", "icon": "🧠", "name": "Ходячий словник", "desc": "Збережи 200 слів", "req_w": 200, "req_t": 0, "req_c": 0, "xp": 500},
    {"id": "t10", "icon": "🔍", "name": "Дослідник", "desc": "10 перекладів", "req_w": 0, "req_t": 10, "req_c": 0, "xp": 100},
    {"id": "t100", "icon": "⚡", "name": "Кібер-лінгвіст", "desc": "100 перекладів", "req_w": 0, "req_t": 100, "req_c": 0, "xp": 400},
    {"id": "c20", "icon": "🎯", "name": "Снайпер", "desc": "20 правильних відповідей", "req_w": 0, "req_t": 0, "req_c": 20, "xp": 150},
    {"id": "c100", "icon": "🏆", "name": "Майстер арени", "desc": "100 правильних відповідей", "req_w": 0, "req_t": 0, "req_c": 100, "xp": 600},
]

def get_user_achievements(user_id):
    w_count = db.get_word_count(user_id)
    stats = db.get_statistics(user_id)
    t_count = stats['translations']
    c_count = stats['correct']
    
    results = []
    ach_xp_total = 0
    
    for ach in ALL_ACHIEVEMENTS:
        is_unlocked = (w_count >= ach['req_w'] and t_count >= ach['req_t'] and c_count >= ach['req_c'])
        if is_unlocked:
            ach_xp_total += ach['xp']
            
        results.append({**ach, "unlocked": is_unlocked})
        
    # Розблоковані зверху, заблоковані знизу
    results.sort(key=lambda x: x['unlocked'], reverse=True)
    return results, ach_xp_total

def get_xp_progress(user_id):
    stats = db.get_statistics(user_id)
    words_count = db.get_word_count(user_id)
    bonus_xp = db.get_user_bonus_xp(user_id)
    
    _, ach_xp = get_user_achievements(user_id)
    
    total_xp = (words_count * 10) + (stats['translations'] * 2) + (stats['correct'] * 5) + bonus_xp + ach_xp
    
    level = (total_xp // 1000) + 1
    current_xp = total_xp % 1000
    progress_width = (current_xp / 1000) * 100
    
    return level, current_xp, progress_width

def calc_level_from_raw_data(w_count, t_count, c_count, bonus_xp):
    ach_xp = 0
    for ach in ALL_ACHIEVEMENTS:
        if (w_count >= ach['req_w'] and t_count >= ach['req_t'] and c_count >= ach['req_c']):
            ach_xp += ach['xp']
    total = (w_count * 10) + (t_count * 2) + (c_count * 5) + bonus_xp + ach_xp
    return (total // 1000) + 1
