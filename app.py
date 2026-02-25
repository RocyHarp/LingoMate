import streamlit as st
import os
import pandas as pd
from PIL import Image
import altair as alt
from logic import backendLogic
import database as db  # Імпортуємо як db для зручності
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
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #020617; font-family: 'Inter', sans-serif; color: #f1f5f9; }
    div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important; border: none !important; color: white !important; font-weight: 600 !important; }
    .vocab-row { background-color: #0f172a; padding: 8px 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #3b82f6; display: flex; align-items: center; justify-content: space-between; }
    .lang-label { text-align: center; padding: 8px; background: #111827; border-radius: 8px; border: 1px solid #334155; font-weight: 600; color: #94a3b8; cursor: default; }
    .lang-active { color: #3b82f6; border-color: #3b82f6; }
    .friend-card { background: #1e293b; padding: 10px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #334155; }
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
                if rp != rp2: st.error("Паролі не співпадають!")
                elif len(rp) < 4: st.warning("Пароль занадто короткий")
                elif db.register_user(ru, re, rp):
                    st.success("Успішно! Увійдіть.")
                else: st.error("Логін зайнятий.")
    st.stop()

# --- БІЧНА ПАНЕЛЬ (ПРОФІЛЬ) ---
with st.sidebar:
    st.markdown(f"## 👤 Профіль: {db.get_username(st.session_state.user_id)}")
    
    # 1. ID та Друзі
    with st.expander("🤝 Мої Друзі", expanded=True):
        st.caption("Твій унікальний ID:")
        st.code(str(st.session_state.user_id), language="text")
        
        new_friend_id = st.text_input("Введи ID друга", placeholder="Напр: 5", label_visibility="collapsed")
        if st.button("Додати друга"):
            res_msg = db.add_friend(st.session_state.user_id, new_friend_id)
            if "Успішно" in res_msg: st.success(res_msg)
            else: st.error(res_msg)
            time.sleep(1)
            st.rerun()

        st.markdown("---")
        friends = db.get_friends_leaderboard(st.session_state.user_id)
        if friends:
            for f in friends:
                st.markdown(f"""
                <div class="friend-card">
                    <b>👤 {f['username']}</b><br>
                    📚 Слів: {f['total_words']} | ✅ Правильно: {f.get('total_correct', 0) or 0}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("У тебе ще немає друзів. Обміняйся ID!")

    # 2. Налаштування акаунту
    with st.expander("⚙️ Налаштування"):
        st.markdown("**Зміна пароля**")
        new_p = st.text_input("Новий пароль", type="password", key="new_pass_set")
        if st.button("Змінити пароль"):
            if len(new_p) >= 4:
                if db.change_password(st.session_state.user_id, new_p): st.success("Пароль змінено!")
            else: st.warning("Мінімум 4 символи.")
            
        st.markdown("---")
        st.markdown("**Небезпечна зона**")
        if st.button("❌ Видалити акаунт"):
            st.session_state.confirm_delete = True

        if st.session_state.get("confirm_delete", False):
            st.error("Ти впевнений? Це незворотно!")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("Так, видалити", type="primary"):
                    db.delete_account(st.session_state.user_id)
                    del st.session_state.user_id
                    st.rerun()
            with col_d2:
                if st.button("Ні, скасувати"):
                    st.session_state.confirm_delete = False
                    st.rerun()

    st.markdown("---")
    if st.button("🚪 Вийти з акаунту"):
        del st.session_state.user_id
        st.rerun()

# --- ОСНОВНИЙ ЕКРАН ---
t_trans, t_dict, t_train, t_stats = st.tabs(["Перекладач", "Словник", "Тренування", "Статистика"])

# --- ВКЛАДКА: ПЕРЕКЛАДАЧ ---
with t_trans:
    current_mode = st.session_state.get("input_mode", "⌨️ Текст")
    text_height = 280 if "Фото" in current_mode else 150
    
    c1, c2 = st.columns([2, 1])
    with c1:
        if "trans_src" not in st.session_state: st.session_state.trans_src = "🇬🇧 English"
        if "trans_dst" not in st.session_state: st.session_state.trans_dst = "🇺🇦 Ukrainian"
        if 'input_text' not in st.session_state: st.session_state.input_text = ""
        
        ls_btn_cols = st.columns([4, 1, 4])
        with ls_btn_cols[0]: st.markdown(f'<div class="lang-label lang-active">{st.session_state.trans_src}</div>', unsafe_allow_html=True)
        with ls_btn_cols[1]: 
            if st.button("⇄", use_container_width=True):
                st.session_state.trans_src, st.session_state.trans_dst = st.session_state.trans_dst, st.session_state.trans_src
                st.rerun()
        with ls_btn_cols[2]: st.markdown(f'<div class="lang-label lang-active">{st.session_state.trans_dst}</div>', unsafe_allow_html=True)
        
        text_input = st.text_area("Введення", value=st.session_state.input_text, height=text_height, label_visibility="collapsed")
        
        if st.button("🚀 Перекласти", type="primary", use_container_width=True):
            if text_input:
                db.increment_translation_count(st.session_state.user_id)
                with st.spinner("Analyzing..."):
                    direction = "EN-UA" if "English" in st.session_state.trans_src else "UA-EN"
                    res = logic.analyze_with_ai(text_input, direction, use_ai=st.session_state.get("use_ai_toggle", False))
                    st.session_state.results = res
                    st.session_state.input_text = text_input

    with c2:
        with st.container(border=True):
            st.markdown("**Опції**")
            st.toggle("✨ Smart AI", value=True, key="use_ai_toggle")
            st.divider()
            mode = st.radio("Ввід", ["⌨️ Текст", "📸 Фото"], key="input_mode")
            if "Фото" in mode:
                f = st.file_uploader("Upload", type=["jpg", "png"], label_visibility="collapsed")
                if f and st.button("📷 Скан"):
                    img = Image.open(f)
                    img.save("temp.png")
                    st.session_state.input_text = logic.get_text_from_image("temp.png")
                    st.rerun()

    if 'results' in st.session_state and st.session_state.results:
        res = st.session_state.results
        with st.container(border=True):
            st.markdown(f"<h3 style='color:#a5b4fc'>{res['translation']}</h3>", unsafe_allow_html=True)
            if db.get_word_by_text(st.session_state.user_id, st.session_state.input_text):
                if st.button("🔄 Оновити в словнику"):
                    db.update_word_meaning(st.session_state.user_id, st.session_state.input_text, res['translation'])
                    st.toast("Оновлено!")
            else:
                if st.button("💾 Додати в словник"):
                    db.save_word(st.session_state.user_id, st.session_state.input_text, res['translation'], "phrase")
                    st.toast("Збережено!")

# --- ВКЛАДКА: СЛОВНИК ---
with t_dict:
    col_s, col_add = st.columns([4, 1])
    with col_s: search = st.text_input("Пошук", placeholder="...", label_visibility="collapsed")
    with col_add:
        with st.popover("⚡ Наповнення"):
            num_w = st.slider("К-сть", 1, 30, 5)
            use_ai_gen = st.toggle("AI Generator", value=True)
            if st.button("Завантажити"):
                with st.spinner("Wait..."):
                    new_w = logic.fetch_and_translate_words(num_w, use_ai=use_ai_gen)
                    for i in new_w:
                         if isinstance(i, dict): db.save_word(st.session_state.user_id, i['word'], i['meaning'], i['type'])
                st.rerun()
                
    words = db.get_grouped_words(st.session_state.user_id)
    filtered = [w for w in words if search.lower() in w['word'].lower() or search.lower() in w['meaning'].lower()]
    
    if not filtered: st.info("Пусто.")
    else:
        for w in filtered:
            with st.expander(f"{w['word']} — {w['meaning']}"):
                c1, c2 = st.columns([3, 1])
                with c1: st.write(f"✅ {w['correct_count']} | ❌ {w['wrong_count']}")
                with c2:
                    if st.button("🗑️", key=f"d_{w['id']}"):
                        db.delete_word(st.session_state.user_id, w['word'])
                        st.rerun()

# --- ВКЛАДКА: ТРЕНУВАННЯ (ОНОВЛЕНА!) ---
with t_train:
    st.markdown("### 🏋️‍♂️ Тренажер слів")
    
    # ВИБІР РЕЖИМУ ТРЕНУВАННЯ
    col_mode, col_start = st.columns([3, 1])
    with col_mode:
        train_type = st.radio("Тип підбору:", ["🎲 Випадковий", "🧠 Розумний (Робота над помилками)"], horizontal=True)
    with col_start:
        if st.button("🔄 Почати нове тренування", use_container_width=True, type="primary"):
            st.session_state.current_index = 0
            st.session_state.score = 0
            st.session_state.train_start_time = time.time()
            
            if "Розумний" in train_type:
                # 🔥 ТУТ МИ НАРЕШТІ ВИКЛИКАЄМО РОЗУМНУ ФУНКЦІЮ
                st.session_state.training_session_words = db.get_words_for_smart_training(st.session_state.user_id, 10)
                if not st.session_state.training_session_words:
                    st.warning("Немає слів з помилками! Вмикаю випадковий режим.")
                    all_w = db.get_all_words(st.session_state.user_id)
                    random.shuffle(all_w)
                    st.session_state.training_session_words = all_w[:10]
            else:
                all_w = db.get_all_words(st.session_state.user_id)
                random.shuffle(all_w)
                st.session_state.training_session_words = all_w[:10]
            st.rerun()

    # ПРОЦЕС ТРЕНУВАННЯ
    if 'training_session_words' in st.session_state and st.session_state.training_session_words:
        session_words = st.session_state.training_session_words
        idx = st.session_state.get('current_index', 0)
        
        if idx < len(session_words):
            current_word = session_words[idx]
            
            # Прогрес бар
            st.progress((idx) / len(session_words))
            
            with st.container(border=True):
                st.markdown(f"<h2 style='text-align:center'>{current_word['word']}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align:center; color:gray'>Як це перекласти?</p>", unsafe_allow_html=True)
                
                ans = st.text_input("Твоя відповідь", key=f"t_q_{idx}")
                
                if st.button("Перевірити"):
                    ts = time.time() - st.session_state.train_start_time
                    correct_opts = [x.strip().lower() for x in current_word['meaning'].split(',')]
                    
                    if ans.strip().lower() in correct_opts or ans.strip().lower() == current_word['meaning'].strip().lower():
                        st.success("🎉 Правильно!")
                        db.update_word_stats(st.session_state.user_id, current_word['word'], True)
                        db.update_daily_training_stats(st.session_state.user_id, True, ts)
                        st.session_state.score += 1
                    else:
                        st.error(f"❌ Помилка! Правильно: {current_word['meaning']}")
                        db.update_word_stats(st.session_state.user_id, current_word['word'], False)
                        db.update_daily_training_stats(st.session_state.user_id, False, ts)
                    
                    time.sleep(1.5)
                    st.session_state.current_index += 1
                    st.session_state.train_start_time = time.time() # скидаємо таймер для наступного слова
                    st.rerun()
        else:
            st.balloons()
            st.success(f"Тренування завершено! Результат: {st.session_state.score}/{len(session_words)}")
            if st.button("Ще раз?"):
                st.session_state.training_session_words = []
                st.rerun()
    else:
        st.info("Натисни 'Почати нове тренування' 👆")

# --- ВКЛАДКА: СТАТИСТИКА ---
with t_stats:
    stats = db.get_statistics(st.session_state.user_id)
    c1, c2, c3 = st.columns(3)
    c1.metric("Всього перекладів", stats['translations'])
    c2.metric("Вивчено слів", len(db.get_all_words(st.session_state.user_id)))
    total = stats['correct'] + stats['wrong']
    acc = int(stats['correct']/total*100) if total > 0 else 0
    c3.metric("Точність", f"{acc}%")
    
    daily = db.get_daily_training_stats(st.session_state.user_id)
    if daily:
        df = pd.DataFrame(daily)
        df['total'] = df['correct_count'] + df['wrong_count']
        chart = alt.Chart(df).mark_line(point=True).encode(
            x='train_date', y='total', tooltip=['train_date', 'total', 'correct_count']
        )
        st.altair_chart(chart, use_container_width=True)
