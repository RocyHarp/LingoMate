import database as db

def get_xp_progress(user_id):
    stats = db.get_statistics(user_id)
    words_count = len(db.get_all_words(user_id))
    
    # Витягуємо бонуси
    bonus_xp = db.get_user_bonus_xp(user_id)
    
    # Базові XP + Бонусні XP
    total_xp = (words_count * 10) + (stats['translations'] * 2) + (stats['correct'] * 5) + bonus_xp
    
    level = (total_xp // 1000) + 1
    current_xp = total_xp % 1000
    progress_width = (current_xp / 1000) * 100
    
    return level, current_xp, progress_width