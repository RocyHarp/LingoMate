import database as db

def get_xp_progress(user_id):
    stats = db.get_statistics(user_id)
    
    # 🔥 Більше ніяких len(get_all_words)! Беремо тільки одну цифру:
    words_count = db.get_word_count(user_id)
    
    bonus_xp = db.get_user_bonus_xp(user_id)
    
    total_xp = (words_count * 10) + (stats['translations'] * 2) + (stats['correct'] * 5) + bonus_xp
    
    level = (total_xp // 1000) + 1
    current_xp = total_xp % 1000
    progress_width = (current_xp / 1000) * 100
    
    return level, current_xp, progress_width

# 🔥 Швидка формула для друзів (щоб не робити зайвих запитів до бази)
def calc_level_from_raw_data(words_count, translations, correct, bonus_xp):
    total_xp = (words_count * 10) + (translations * 2) + (correct * 5) + bonus_xp
    return (total_xp // 1000) + 1
