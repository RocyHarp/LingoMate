import streamlit as st
import os
import pandas as pd
from PIL import Image
import altair as alt
from logic import backendLogic
import database as db  # Імпортуємо як db
import random
import time

st.set_page_config(page_title="LingoMate", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# --- CSS i Config ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .viewerBadge_container {display: none !important;}
            [data-testid="stCreatorBadge"] {display: none !important;}
            [data-testid="stViewerBadge"] {display: none !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Стилі ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #020617; font-family: 'Inter', sans-serif; color: #f1f5f9; }
    h1, h2, h3, h4 { color: #f8fafc !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #1e293b !important; border: 1px solid #475569 !important; border-radius: 12px !important; padding: 16px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5) !important; }
    div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important; border: none !important; color: white !important; font-weight: 600 !important; }
    .vocab-row { background-color: #0f172a; padding: 8px 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #3b82f6; display: flex; align-items: center; justify-content: space-between; }
    .lang-label { text-align: center; padding: 8px; background: #111827; border-radius: 8px; border: 1px solid #334155; font-weight: 600; color: #94a3b8; cursor: default; }
    .lang-active { color: #3b82f6; border-color: #3b82f6; }
    .friend-card { background: #1e293b; padding: 10px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #334155; }
    .synonym-box { margin-top: 10px; padding: 10px; background: #0f172a; border-radius: 8px; border-left: 3px solid #a855f7; font-size: 14px; }
    .synonym-word { font-weight: bold; color: #e2e8f0; }
    .synonym-meaning { color: #4ade80; }
    .synonym-nuance { color: #94a3b8; font-style: italic; font-size: 12px; display: block; margin-top: 2px;}
    </style>
""", unsafe_allow_html=True)

db.init_db()
@st.cache_resource
def get_logic(): return backendLogic()
logic = get_logic()

# --- СИСТЕМА ВХОДУ ---
if "user_id" not in st.session_state:
    _, cent, _ = st.columns([1, 1.5, 1])
    with cent:
        st.markdown("<h1 style='text-align:center;'>⚡ LingoMate</h1>", unsafe_allow_html=True)
        tab_log, tab_reg = st.tabs(["🔑 Вхід", "📝 Реєстрація"])
        
        with tab_log:
            u = st.text_input("Username", key="l_u")
            p = st.text_input("Password", type="password", key="l_p")
            if st.button("Увійти", type="primary"):
                user = db.login_user(u, p)
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.is_premium = user[1]
                    st.session_state.username = u # Зберігаємо ім'я
                    st.rerun()
                else: st.error("Невірний логін або пароль")
                
        with tab_reg:
            ru = st.text_input("Новий Username", key="r_u")
            re = st.text_input("Електронна пошта", key="r_e")
            rp = st.text_input("Новий Password", type="password", key="r_p")
            rp2 = st.text_input("Повторіть Password", type="password", key="r_p2")
            
            if st.button("Створити акаунт"):
                if not ru or not re or not rp or not rp2:
                    st.warning("Будь ласка, заповніть всі поля.")
                elif "@" not in re or "." not in re:
                    st.warning("Введіть коректну електронну пошту.")
                elif rp != rp2:
                    st.error("Паролі не співпадають!")
                else:
                    if db.register_user(ru, re, rp):
                        st.success("Успішно! Тепер увійдіть.")
                    else: 
                        st.error("Цей логін або пошта вже зайняті.")
    st.stop()

# --- НОВИЙ САЙДБАР (ПРОФІЛЬ + ДРУЗІ) ---
with st.sidebar:
    # Отримуємо актуальне ім'я з бази, якщо його немає в сесії
    current_username = st.session_state.get("username", db.get_username(st.session_state.user_id))
    st.markdown(f"## 👤 {current_username}")
    
    # 1. ID та Друзі
    with st.expander("🤝 Мої Друзі", expanded=True):
        st.caption("Твій ID для друзів:")
        st.code(str(st.session_state.user_id), language="text")
        
        new_friend_id = st.text_input("Додати друга (ID)", placeholder="Введи цифру...", label_visibility="collapsed")
        if st.button("Додати"):
            res_msg = db.add_friend(st.session_state.user_id, new_friend_id)
            if "Успішно" in res_msg: st.success(res_msg)
            else: st.error(res_msg)
            time.sleep(1)
            st.rerun()

        st.markdown("---")
        friends = db.get_friends_leaderboard(st.session_state.user_id)
        if friends:
            st.caption("🏆 Рейтинг друзів:")
            for f in friends:
                st.markdown(f"""
                <div class="friend-card">
                    <b>👤 {f['username']}</b><br>
                    📚 Слів: {f['total_words']} | ✅ {f.get('total_correct', 0) or 0}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Додай друзів, щоб бачити їх прогрес!")

    # 2. Налаштування
    with st.expander("⚙️ Налаштування"):
        st.caption("Зміна пароля")
        new_p = st.text_input("Новий пароль", type="password", key="new_pass_set")
        if st.button("Змінити пароль"):
            if len(new_p) >= 4:
                if db.change_password(st.session_state.user_id, new_p): st.success("Готово!")
            else: st.warning("Мін. 4 символи.")
            
        st.markdown("---")
        if st.button("🚪 Вийти"):
            del st.session_state.user_id
            st.rerun()
            
        st.markdown("---")
        st.caption("Небезпечна зона")
        if st.button("❌ Видалити акаунт"):
            st.session_state.confirm_delete = True

        if st.session_state.get("confirm_delete", False):
            st.error("Точно видалити?")
            c_d1, c_d2 = st.columns(2)
            with c_d1:
                if st.button("ТАК", type="primary"):
                    db.delete_account(st.session_state.user_id)
                    del st.session_state.user_id
                    st.rerun()
            with c_d2:
                if st.button("НІ"):
                    st.session_state.confirm_delete = False
                    st.rerun()


# --- ГОЛОВНА ЧАСТИНА ---
c_head, c_space = st.columns([5, 1])
with c_head: st.markdown("## ⚡ LingoMate")

t_trans, t_dict, t_train, t_stats = st.tabs(["Перекладач", "Словник", "Тренування", "Статистика"])

# --- 1. ПЕРЕКЛАДАЧ (ЗБЕРЕЖЕНО ВЕСЬ ФУНКЦІОНАЛ) ---
with t_trans:
    st.write("")
    current_mode = st.session_state.get("input_mode", "⌨️ Текст")
    text_height = 280 if "Фото" in current_mode else 150

    c1, c2 = st.columns([2, 1])
    with c1:
        if "trans_src" not in st.session_state: st.session_state.trans_src = "🇬🇧 English"
        if "trans_dst" not in st.session_state: st.session_state.trans_dst = "🇺🇦 Ukrainian"
        if 'input_text' not in st.session_state: st.session_state.input_text = ""
        
        ls_col1, ls_btn, ls_col2 = st.columns([4, 1, 4])
        with ls_col1: st.markdown(f'<div class="lang-label lang-active">{st.session_state.trans_src}</div>', unsafe_allow_html=True)
        with ls_btn:
            if st.button("⇄", use_container_width=True):
                st.session_state.trans_src, st.session_state.trans_dst = st.session_state.trans_dst, st.session_state.trans_src
                st.rerun()
        with ls_col2: st.markdown(f'<div class="lang-label lang-active">{st.session_state.trans_dst}</div>', unsafe_allow_html=True)
        st.write("")
        
        text_input = st.text_area("Введіть текст", value=st.session_state.input_text, height=text_height, placeholder="Type something...", label_visibility="collapsed")
        
        if st.button("🚀 Перекласти", type="primary", use_container_width=True):
            if text_input:
                db.increment_translation_count(st.session_state.user_id)
                with st.spinner("Analyzing..."):
                    direction_code = "EN-UA" if "English" in st.session_state.trans_src else "UA-EN"
                    use_ai_val = st.session_state.get("use_ai_toggle", False) 
                    res = logic.analyze_with_ai(text_input, direction_code, use_ai=use_ai_val)
                    st.session_state.results = res
                    st.session_state.input_text = text_input

    with c2:
        with st.container(border=True):
            st.markdown("**Налаштування**")
            is_premium = st.session_state.get("is_premium", 0) == 1
            if is_premium: st.toggle("✨ Smart AI", value=True, key="use_ai_toggle")
            else:
                st.toggle("🔒 Smart AI (Premium)", value=False, disabled=True, key="use_ai_toggle")
                st.caption("ШІ аналіз заблоковано.")
            st.divider()
            mode = st.radio("Режим", ["⌨️ Текст", "📸 Фото"], key="input_mode", label_visibility="collapsed")
            if "Фото" in mode:
                f = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
                if f and st.button("📷 Сканувати"):
                    img = Image.open(f)
                    img.save("temp.png")
                    text_input = logic.get_text_from_image("temp.png")
                    st.session_state.input_text = text_input
                    st.rerun()

    if 'results' in st.session_state and st.session_state.results:
        res = st.session_state.results
        st.write("")
        with st.container(border=True):
            st.caption("РЕЗУЛЬТАТ")
            st.markdown(f"<h3 style='color:#a5b4fc; margin-top:-10px;'>{res['translation']}</h3>", unsafe_allow_html=True)
            col_act1, col_act2 = st.columns([1, 4])
            existing = db.get_word_by_text(st.session_state.user_id, st.session_state.input_text)
            with col_act1:
                if existing:
                    if st.button("🔄 Оновити"):
                        db.update_word_meaning(st.session_state.user_id, st.session_state.input_text, res['translation'])
                        st.toast("Оновлено!")
                else:
                    if st.button("💾 Зберегти"):
                        db.save_word(st.session_state.user_id, st.session_state.input_text, res['translation'], "phrase")
                        st.toast("Збережено!")
        
        if res.get('context_ua'):
            if "ERROR" in res['context_ua']: st.error(res['context_ua'])
            elif res['context_ua'].strip(): st.info(f"🧠 **Аналіз:** {res['context_ua']}")

        # РОЗБІР СЛІВ (ЗБЕРЕЖЕНО!)
        if res.get('vocabulary'):
            st.write("")
            with st.expander("🧩 Детальний розбір речення", expanded=True):
                all_db_words = db.get_all_words(st.session_state.user_id)
                db_word_set = {w['word'].lower().strip() for w in all_db_words}
                
                for item in res['vocabulary']:
                    if isinstance(item, dict):
                        w_text = item.get('word', '???')
                        w_trans = item.get('translation', '???')
                        w_type = item.get('type', '')
                    elif isinstance(item, str):
                        w_text = item; w_trans = "—"; w_type = ""
                    else: continue 

                    c_w, c_t, c_btn = st.columns([3, 4, 3])
                    with c_w:
                        st.markdown(f"**{w_text}**")
                        if w_type: st.caption(w_type)
                    with c_t: st.markdown(f"<span style='color:#4ade80'>{w_trans}</span>", unsafe_allow_html=True)
                    with c_btn:
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if w_text.lower().strip() in db_word_set: st.markdown("✅")
                            else:
                                if st.button("💾", key=f"save_vocab_{w_text}_{random.randint(1,10000)}"):
                                    db.save_word(st.session_state.user_id, w_text, w_trans, w_type if w_type else "auto")
                                    st.toast(f"Додано: {w_text}")
                                    time.sleep(0.5); st.rerun()
                        with btn_col2:
                            if w_text and w_text != "???":
                                if st.button("❔", key=f"nuance_{w_text}_{random.randint(1,10000)}"):
                                    with st.spinner("⏳"):
                                        res_nuance = logic.explain_nuance(w_text, st.session_state.input_text)
                                        if res_nuance and isinstance(res_nuance, dict):
                                            st.session_state[f"expl_{w_text}"] = res_nuance.get('explanation', '')
                                        else: st.toast("AI не відповів.", icon="⚠️")
                    
                    if f"expl_{w_text}" in st.session_state: st.info(f"💡 {st.session_state[f'expl_{w_text}']}")
                    st.divider()

# --- 2. СЛОВНИК (ЗБЕРЕЖЕНО ВЕСЬ ФУНКЦІОНАЛ) ---
with t_dict:
    c_search, c_add = st.columns([4, 1])
    with c_search: search = st.text_input("Пошук", placeholder="Знайти слово...", label_visibility="collapsed")
    with c_add:
        with st.popover("⚡ Авто-наповнення", use_container_width=True):
            st.markdown("Скільки слів?")
            num_words = st.slider("", 1, 30, 5)
            if st.session_state.get("is_premium", 0) == 1: use_ai_dict = st.toggle("✨ AI Підбірка", value=True)
            else: use_ai_dict = st.toggle("🔒 AI Підбірка", value=False, disabled=True)
            
            if st.button("Завантажити", type="primary"):
                with st.spinner("Генерую список..."):
                    new = logic.fetch_and_translate_words(num_words, use_ai=use_ai_dict)
                    if new:
                        for i in new:
                            if isinstance(i, dict): db.save_word(st.session_state.user_id, i.get('word', ''), i.get('meaning', ''), i.get('type', 'auto'))
                        st.success(f"Додано слів!")
                        time.sleep(1); st.rerun()
                    else: st.error("Помилка.")
    
    st.write("")
    grouped_words = db.get_grouped_words(st.session_state.user_id)
    filtered = []
    for p in grouped_words:
        match_parent = search.lower() in p['word'].lower() or search.lower() in p['meaning'].lower()
        match_child = any(search.lower() in child['word'].lower() for child in p['synonyms'])
        if match_parent or match_child: filtered.append(p)
    
    if not filtered: st.info("Порожньо.")
    else:
        cols = st.columns(3)
        for idx, w in enumerate(filtered):
            with cols[idx % 3]:
                with st.container(border=True):
                    c_text, c_menu = st.columns([8, 1])
                    with c_text:
                        st.markdown(f"**{w['word']}**")
                        st.markdown(f"<span style='color:#4ade80;'>{w['meaning']}</span>", unsafe_allow_html=True)
                        st.caption(f"✅{w['correct_count']} ❌{w['wrong_count']}")
                        if f"dict_expl_{w['id']}" in st.session_state:
                             st.info(f"💡 {st.session_state[f'dict_expl_{w['id']}']}")
                    with c_menu:
                        with st.popover("⋮", use_container_width=False):
                            if st.button("❔ Пояснити нюанс", key=f"explain_{w['id']}"):
                                with st.spinner("Аналізую..."):
                                    res_nuance = logic.explain_nuance(w['word'], meaning=w['meaning'])
                                    if res_nuance and isinstance(res_nuance, dict):
                                        st.session_state[f"dict_expl_{w['id']}"] = res_nuance.get('explanation', '')
                                        db.save_synonym(st.session_state.user_id, w['id'], res_nuance.get('synonym_en', ''), res_nuance.get('synonym_ua', ''), "Плутаючий синонім")
                                        st.rerun()
                            if st.button("🔗 Знайти синоніми", key=f"syn_{w['id']}"):
                                with st.spinner(f"Шукаю синоніми..."):
                                    synonyms = logic.find_synonyms(w['word'], w['meaning'])
                                    if synonyms:
                                        for syn in synonyms: db.save_synonym(st.session_state.user_id, w['id'], syn['word'], syn['translation'], syn['nuance'])
                                        st.rerun()
                            st.divider()
                            new_mean = st.text_input("Переклад", value=w['meaning'], key=f"edit_txt_{w['id']}")
                            if st.button("💾 Зберегти", key=f"save_{w['id']}"):
                                db.update_word_meaning(st.session_state.user_id, w['word'], new_mean)
                                st.rerun()
                            if st.button("🗑️ Видалити", key=f"del_{w['id']}"):
                                db.delete_word(st.session_state.user_id, w['word'])
                                st.rerun()
                    if w['synonyms']:
                        with st.expander(f"Синоніми ({len(w['synonyms'])})", expanded=True):
                            for child in w['synonyms']:
                                st.markdown(f"""
                                <div class="synonym-box">
                                    <span class="synonym-word">{child['word']}</span> - 
                                    <span class="synonym-meaning">{child['meaning']}</span>
                                    <span class="synonym-nuance">💡 {child['nuance']}</span>
                                </div>""", unsafe_allow_html=True)
                                col_s_act = st.button("🗑️", key=f"del_child_{child['id']}")
                                if col_s_act:
                                     db.delete_word(st.session_state.user_id, child['word']); st.rerun()

# --- 3. ТРЕНУВАННЯ (ПОВЕРНУВ РЕЖИМИ + ДОДАВ РОЗУМНИЙ ПІДБІР!) ---
with t_train:
    # 1. Вибір джерела слів (НОВЕ)
    c_source, c_mode = st.columns([1, 1])
    with c_source:
        train_source = st.radio("Підбір слів:", ["🎲 Випадковий", "🧠 Розумний"], horizontal=True)
    with c_mode:
        mode = st.radio("Режим:", ["Картки", "Письмо (EN ➜ UA)", "Письмо (UA ➜ EN)"], horizontal=True)
        
    all_words_flat = db.get_all_words(st.session_state.user_id)
    if not all_words_flat: st.warning("Додайте слова.")
    else:
        # Старт сесії тренування
        if 'train_start_time' not in st.session_state:
            st.session_state.train_start_time = time.time()
        
        # ЛОГІКА ПІДБОРУ СЛІВ
        if 'train_session' not in st.session_state:
             st.session_state.train_session = []
             
        # Якщо список пустий або ми хочемо оновити
        if not st.session_state.train_session:
            if train_source == "🧠 Розумний":
                 # Беремо 10 слів з розумного підбору
                 st.session_state.train_session = db.get_words_for_smart_training(st.session_state.user_id, 10)
            if not st.session_state.train_session: # Якщо розумний порожній або режим випадковий
                 temp = all_words_flat.copy()
                 random.shuffle(temp)
                 st.session_state.train_session = temp[:10]
            st.session_state.train_idx = 0

        # Поточне слово
        idx = st.session_state.train_idx
        if idx >= len(st.session_state.train_session):
             st.success("🎉 Тренування завершено!")
             if st.button("Ще раз"):
                 st.session_state.train_session = []
                 st.rerun()
        else:
            curr = st.session_state.train_session[idx]
            
            # ВІДОБРАЖЕННЯ
            st.write("")
            if 'show_answer' not in st.session_state: st.session_state.show_answer = False
            
            q_text = curr['word']
            is_synonym = curr['parent_id'] is not None
            sub_text = "Синонім" if is_synonym else curr['word_type']
            
            if mode == "Письмо (UA ➜ EN)":
                q_text = curr['meaning']
                sub_text = "Як це англійською?" + (" (Синонім)" if is_synonym else "")
                
            with st.container(border=True):
                st.markdown(f"<h1 style='text-align:center; margin-top:-10px; margin-bottom: 20px;'>{q_text}</h1>", unsafe_allow_html=True)
                if is_synonym and curr['nuance'] and mode != "Письмо (UA ➜ EN)":
                     st.info(f"💡 Підказка: {curr['nuance']}")
                else: st.markdown(f"<div style='text-align:center; color:#64748b; margin-bottom:20px;'>{sub_text}</div>", unsafe_allow_html=True)
            
            # ЛОГІКА ВІДПОВІДІ
            if mode == "Картки":
                if st.session_state.show_answer:
                    st.success(f"**{curr['meaning']}**")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅ Знаю", use_container_width=True):
                            ts = min(time.time() - st.session_state.train_start_time, 60)
                            db.update_daily_training_stats(st.session_state.user_id, True, ts)
                            db.update_word_stats(st.session_state.user_id, curr['word'], True)
                            st.session_state.train_idx += 1
                            st.session_state.show_answer = False
                            st.session_state.train_start_time = time.time()
                            st.rerun()
                    with b2:
                        if st.button("❌ Не знаю", use_container_width=True):
                            ts = min(time.time() - st.session_state.train_start_time, 60)
                            db.update_daily_training_stats(st.session_state.user_id, False, ts)
                            db.update_word_stats(st.session_state.user_id, curr['word'], False)
                            st.session_state.train_idx += 1
                            st.session_state.show_answer = False
                            st.session_state.train_start_time = time.time()
                            st.rerun()
                else:
                    if st.button("Показати відповідь", type="primary", use_container_width=True):
                        st.session_state.show_answer = True
                        st.rerun()
            else:
                ans = st.text_input("Відповідь", placeholder="...", label_visibility="collapsed")
                if st.button("Перевірити", type="primary", use_container_width=True):
                    is_cor = False
                    if mode == "Письмо (EN ➜ UA)":
                         opts = [x.strip().lower() for x in curr['meaning'].replace('/', ',').split(',')]
                         if ans.strip().lower() in opts: is_cor = True
                    elif mode == "Письмо (UA ➜ EN)":
                         if ans.strip().lower() == curr['word'].strip().lower(): is_cor = True
                         
                    ts = min(time.time() - st.session_state.train_start_time, 60)
                    if is_cor:
                        st.success("🎉 Correct!")
                        db.update_daily_training_stats(st.session_state.user_id, True, ts)
                        db.update_word_stats(st.session_state.user_id, curr['word'], True)
                    else:
                        st.error(f"Wrong. It was: {curr['meaning'] if 'EN' in mode else curr['word']}")
                        db.update_daily_training_stats(st.session_state.user_id, False, ts)
                        db.update_word_stats(st.session_state.user_id, curr['word'], False)
                    
                    time.sleep(1.5)
                    st.session_state.train_idx += 1
                    st.session_state.train_start_time = time.time()
                    st.rerun()
            
            # Кнопка пропуску
            if st.button("Пропустити"):
                 st.session_state.train_idx += 1; st.rerun()

# --- 4. СТАТИСТИКА (ЗБЕРЕЖЕНО!) ---
with t_stats:
    stats = db.get_statistics(st.session_state.user_id)
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Запитів", stats['translations'])
        c2.metric("Слів", len(db.get_all_words(st.session_state.user_id)))
        tot = stats['correct'] + stats['wrong']
        acc = int((stats['correct']/tot*100)) if tot > 0 else 0
        c3.metric("Точність", f"{acc}%")
        
    st.markdown("### 📈 Динаміка")
    daily_data = db.get_daily_training_stats(st.session_state.user_id)
    if daily_data:
        df = pd.DataFrame(daily_data)
        df['Всього'] = df['correct_count'] + df['wrong_count']
        df['Дата'] = pd.to_datetime(df['train_date']).dt.strftime('%d.%m')
        
        y_max = df['Всього'].max() * 1.5 if df['Всього'].max() > 0 else 10
        chart = alt.Chart(df).mark_line(point=True, color='#6366f1', strokeWidth=3).encode(
            x=alt.X('Дата', sort=None),
            y=alt.Y('Всього', scale=alt.Scale(domain=[0, y_max])),
            tooltip=['train_date', 'Всього', 'correct_count', 'wrong_count']
        ).properties(height=350).interactive()
        st.altair_chart(chart, use_container_width=True)
    else: st.info("Тренуйся більше, щоб побачити графік!")
