import streamlit as st
import os
import pandas as pd
from PIL import Image
import altair as alt
from logic import backendLogic
from database import init_db, save_word, save_synonym, get_grouped_words, get_all_words, delete_word, increment_translation_count, update_word_stats, get_statistics, get_word_by_text, update_word_meaning, reset_word_stats, login_user, register_user, update_daily_training_stats, get_daily_training_stats
import random
import time

st.set_page_config(page_title="LingoMate", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    .stApp { background-color: #020617; font-family: 'Inter', sans-serif; color: #f1f5f9; }
    h1, h2, h3, h4 { color: #f8fafc !important; }
    [data-testid="stVerticalBlockBorderWrapper"] { background-color: #1e293b !important; border: 1px solid #475569 !important; border-radius: 12px !important; padding: 16px !important; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5) !important; }
    [data-testid="stPopover"] { display: inline-block; position: relative; z-index: 99 !important; }
    [data-testid="stPopover"] > button { background-color: transparent !important; border: none !important; color: #e2e8f0 !important; opacity: 0.2 !important; transition: all 0.2s ease-in-out !important; height: 40px !important; width: 40px !important; min-height: 40px !important; display: flex !important; align-items: center !important; justify-content: center !important; padding: 0 !important; margin: 0 !important; font-size: 24px !important; }
    [data-testid="stPopover"] > button:hover { opacity: 1 !important; background-color: rgba(255, 255, 255, 0.1) !important; color: #ffffff !important; border-radius: 8px !important; cursor: pointer !important; }
    [data-testid="stPopover"] > button::after { display: none !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #111827; padding: 8px; border-radius: 12px; border: 1px solid #334155; }
    .stTabs [data-baseweb="tab"] { background-color: transparent; border: none; color: #94a3b8; font-weight: 600; border-radius: 10px; padding: 8px 16px; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #3b82f6; color: white; border-radius: 10px; }
    div.stButton > button, div.stLinkButton > a { background: #1e293b !important; color: #e2e8f0 !important; border: 1px solid #334155 !important; border-radius: 8px !important; font-weight: 500 !important; text-decoration: none !important; display: flex !important; justify-content: center !important; align-items: center !important; width: 100% !important; box-shadow: none !important; }
    div.stButton > button:hover, div.stLinkButton > a:hover { border-color: #6366f1 !important; color: white !important; background-color: #334155 !important; }
    div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important; border: none !important; color: white !important; font-weight: 600 !important; }
    .stTextInput > div > div > input, .stTextArea > div > div > textarea { background-color: #020617 !important; border: 1px solid #334155 !important; color: #f8fafc !important; border-radius: 8px !important; }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #6366f1 !important; }
    .vocab-row { background-color: #0f172a; padding: 8px 12px; border-radius: 8px; margin-bottom: 8px; border-left: 3px solid #3b82f6; display: flex; align-items: center; justify-content: space-between; }
    .lang-label { text-align: center; padding: 8px; background: #111827; border-radius: 8px; border: 1px solid #334155; font-weight: 600; color: #94a3b8; cursor: default; }
    .lang-active { color: #3b82f6; border-color: #3b82f6; }
    .synonym-box { margin-top: 10px; padding: 10px; background: #0f172a; border-radius: 8px; border-left: 3px solid #a855f7; font-size: 14px; }
    .synonym-word { font-weight: bold; color: #e2e8f0; }
    .synonym-meaning { color: #4ade80; }
    .synonym-nuance { color: #94a3b8; font-style: italic; font-size: 12px; display: block; margin-top: 2px;}
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} [data-testid="stSidebar"] {display: none;}
    </style>
""", unsafe_allow_html=True)

init_db()
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
                user = login_user(u, p)
                if user:
                    st.session_state.user_id = user[0]
                    st.session_state.is_premium = user[1]
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
                    st.error("Паролі не співпадають! Спробуйте ще раз.")
                else:
                    if register_user(ru, re, rp):
                        st.success("Успішно! Тепер увійдіть у вкладці 'Вхід'.")
                    else: 
                        st.error("Цей логін або електронна пошта вже зайняті.")
    st.stop()

# --- ШАПКА ---
c_head, c_exit = st.columns([5, 1])
with c_head: st.markdown("## ⚡ LingoMate")
with c_exit: 
    if st.button("🚪 Вийти"):
        del st.session_state.user_id
        st.rerun()

t_trans, t_dict, t_train, t_stats = st.tabs(["Перекладач", "Словник", "Тренування", "Статистика"])

# --- 1. ПЕРЕКЛАДАЧ ---
with t_trans:
    st.write("")
    
    # --- ДИНАМІЧНА ВИСОТА ---
    # Читаємо поточний режим, щоб вирівняти висоту колонок (280px для фото, 150px для тексту)
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
        
        # Використовуємо змінну text_height
        text_input = st.text_area("Введіть текст", value=st.session_state.input_text, height=text_height, placeholder="Type something...", label_visibility="collapsed")
        
        if st.button("🚀 Перекласти", type="primary", use_container_width=True):
            if text_input:
                increment_translation_count(st.session_state.user_id)
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
            if is_premium:
                st.toggle("✨ Smart AI", value=True, key="use_ai_toggle")
            else:
                st.toggle("🔒 Smart AI (Premium)", value=False, disabled=True, key="use_ai_toggle")
                st.caption("ШІ аналіз заблоковано.")
            st.divider()
            
            # --- ДОДАНО key="input_mode" ---
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
            existing = get_word_by_text(st.session_state.user_id, st.session_state.input_text)
            with col_act1:
                if existing:
                    if st.button("🔄 Оновити"):
                        update_word_meaning(st.session_state.user_id, st.session_state.input_text, res['translation'])
                        st.toast("Оновлено!")
                else:
                    if st.button("💾 Зберегти"):
                        save_word(st.session_state.user_id, st.session_state.input_text, res['translation'], "phrase")
                        st.toast("Збережено!")
        
        if res.get('context_ua'):
            if "ERROR" in res['context_ua']: st.error(res['context_ua'])
            elif res['context_ua'].strip(): st.info(f"🧠 **Аналіз:** {res['context_ua']}")

        # РОЗБІР СЛІВ
        if res.get('vocabulary'):
            st.write("")
            with st.expander("🧩 Детальний розбір речення", expanded=True):
                all_db_words = get_all_words(st.session_state.user_id)
                db_word_set = {w['word'].lower().strip() for w in all_db_words}
                
                for item in res['vocabulary']:
                    if isinstance(item, dict):
                        w_text = item.get('word', '???')
                        w_trans = item.get('translation', '???')
                        w_type = item.get('type', '')
                    elif isinstance(item, str):
                        w_text = item
                        w_trans = "—" 
                        w_type = ""
                    else:
                        continue 

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
                                if st.button("💾", key=f"save_vocab_{w_text}_{random.randint(1,10000)}", help="Зберегти"):
                                    save_word(st.session_state.user_id, w_text, w_trans, w_type if w_type else "auto")
                                    st.toast(f"Додано: {w_text}")
                                    time.sleep(0.5)
                                    st.rerun()
                        with btn_col2:
                            if w_text and w_text != "???":
                                if st.button("❔", key=f"nuance_{w_text}_{random.randint(1,10000)}", help="Пояснити"):
                                    with st.spinner("⏳"):
                                        res_nuance = logic.explain_nuance(w_text, st.session_state.input_text)
                                        if res_nuance and isinstance(res_nuance, dict):
                                            st.session_state[f"expl_{w_text}"] = res_nuance.get('explanation', '')
                                        else:
                                            st.toast("AI не відповів.", icon="⚠️")
                    
                    if f"expl_{w_text}" in st.session_state: st.info(f"💡 {st.session_state[f'expl_{w_text}']}")
                    st.divider()

# --- 2. СЛОВНИК ---
with t_dict:
    c_search, c_add = st.columns([4, 1])
    with c_search: search = st.text_input("Пошук", placeholder="Знайти слово...", label_visibility="collapsed")
    with c_add:
        with st.popover("⚡ Авто-наповнення", use_container_width=True):
            st.markdown("Скільки слів?")
            num_words = st.slider("", 1, 30, 5)
            # ВІЗУАЛЬНИЙ ЗАМОЧОК ШІ
            if st.session_state.get("is_premium", 0) == 1:
                use_ai_dict = st.toggle("✨ AI Підбірка", value=True)
            else:
                use_ai_dict = st.toggle("🔒 AI Підбірка", value=False, disabled=True)
            
            if st.button("Завантажити", type="primary"):
                with st.spinner("Генерую список..."):
                    new = logic.fetch_and_translate_words(num_words, use_ai=use_ai_dict)
                    if new:
                        count_added = 0
                        for i in new:
                            if isinstance(i, dict):
                                save_word(st.session_state.user_id, i.get('word', ''), i.get('meaning', ''), i.get('type', 'auto'))
                                count_added += 1
                            elif isinstance(i, str):
                                save_word(st.session_state.user_id, i, "—", "auto")
                                count_added += 1
                        
                        st.success(f"Додано {count_added} слів!")
                        time.sleep(1)
                    else: st.error("Помилка.")
                st.rerun()
    st.write("")
    grouped_words = get_grouped_words(st.session_state.user_id)
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
                            st.caption("Дії")
                            
                            if st.button("❔ Пояснити нюанс", key=f"explain_{w['id']}"):
                                with st.spinner("Аналізую..."):
                                    res_nuance = logic.explain_nuance(w['word'], meaning=w['meaning'])
                                    if res_nuance and isinstance(res_nuance, dict):
                                        st.session_state[f"dict_expl_{w['id']}"] = res_nuance.get('explanation', '')
                                        save_synonym(st.session_state.user_id, w['id'], res_nuance.get('synonym_en', ''), res_nuance.get('synonym_ua', ''), "Плутаючий синонім")
                                        st.toast(f"Додано синонім: {res_nuance.get('synonym_en')}")
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("AI не відповів.")

                            if st.button("🔗 Знайти синоніми", key=f"syn_{w['id']}"):
                                with st.spinner(f"Шукаю синоніми..."):
                                    synonyms = logic.find_synonyms(w['word'], w['meaning'])
                                    if synonyms:
                                        for syn in synonyms: save_synonym(st.session_state.user_id, w['id'], syn['word'], syn['translation'], syn['nuance'])
                                        st.toast(f"Знайдено!")
                                        time.sleep(1)
                                        st.rerun()
                                    else: st.error("Нічого не знайдено.")
                            st.divider()
                            new_mean = st.text_input("Переклад", value=w['meaning'], key=f"edit_txt_{w['id']}")
                            if st.button("💾 Зберегти", key=f"save_{w['id']}"):
                                update_word_meaning(st.session_state.user_id, w['word'], new_mean)
                                st.rerun()
                            st.link_button("🌐 Google", f"https://www.google.com/search?q={w['word']} meaning")
                            if st.button("🔄 Скинути", key=f"reset_{w['id']}"):
                                reset_word_stats(st.session_state.user_id, w['word'])
                                st.rerun()
                            if st.button("🗑️ Видалити", key=f"del_{w['id']}"):
                                delete_word(st.session_state.user_id, w['word'])
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
                                col_s_stats, col_s_act = st.columns([4, 1])
                                with col_s_stats: st.caption(f"Прогрес: ✅{child['correct_count']} ❌{child['wrong_count']}")
                                with col_s_act:
                                     if st.button("🗑️", key=f"del_child_{child['id']}"):
                                         delete_word(st.session_state.user_id, child['word'])
                                         st.rerun()

# --- 3. ТРЕНУВАННЯ ---
with t_train:
    all_words_flat = get_all_words(st.session_state.user_id)
    if not all_words_flat: st.warning("Додайте слова.")
    else:
        # Старт таймеру для рахунку часу
        if 'train_start_time' not in st.session_state:
            st.session_state.train_start_time = time.time()
            
        _, mid, _ = st.columns([1, 2, 1])
        with mid:
            mode = st.radio("Режим", ["Картки", "Письмо (EN ➜ UA)", "Письмо (UA ➜ EN)"], horizontal=True)
            st.write("")
            if 'train_idx' not in st.session_state: st.session_state.train_idx = random.randint(0, len(all_words_flat) - 1)
            if 'show_answer' not in st.session_state: st.session_state.show_answer = False
            if 'feedback_msg' not in st.session_state: st.session_state.feedback_msg = None
            
            curr = all_words_flat[st.session_state.train_idx % len(all_words_flat)]
            q_text = curr['word']
            is_synonym = curr['parent_id'] is not None
            sub_text = "Синонім" if is_synonym else curr['word_type']
            if mode == "Письмо (UA ➜ EN)":
                q_text = curr['meaning']
                sub_text = "Як це англійською?" + (" (Синонім)" if is_synonym else "")
                
            with st.container(border=True):
                c_spacer, c_menu = st.columns([10, 1])
                with c_menu:
                    with st.popover("⋮", use_container_width=False):
                        st.caption("Управління")
                        if st.button("🗑️ Видалити", key=f"del_train_{curr['id']}", type="primary"):
                            delete_word(st.session_state.user_id, curr['word'])
                            st.rerun()
                        new_tr_train = st.text_input("Змінити переклад", value=curr['meaning'], key=f"edit_train_{curr['id']}")
                        if st.button("💾 Зберегти", key=f"save_train_{curr['id']}"):
                            update_word_meaning(st.session_state.user_id, curr['word'], new_tr_train)
                            st.rerun()
                st.markdown(f"<h1 style='text-align:center; margin-top:-40px; margin-bottom: 20px;'>{q_text}</h1>", unsafe_allow_html=True)
                if is_synonym and curr['nuance'] and mode != "Письмо (UA ➜ EN)":
                     st.info(f"💡 Підказка: {curr['nuance']}")
                else: st.markdown(f"<div style='text-align:center; color:#64748b; margin-bottom:20px;'>{sub_text}</div>", unsafe_allow_html=True)
            st.write("")
            
            if mode == "Картки":
                if st.session_state.show_answer:
                    st.success(f"**{curr['meaning']}**")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅ Знаю", use_container_width=True):
                            ts = min(time.time() - st.session_state.train_start_time, 60) # макс 60с на 1 слово
                            update_daily_training_stats(st.session_state.user_id, True, ts)
                            update_word_stats(st.session_state.user_id, curr['word'], True)
                            st.session_state.train_idx = random.randint(0, len(all_words_flat) - 1)
                            st.session_state.show_answer = False
                            st.session_state.train_start_time = time.time()
                            st.rerun()
                    with b2:
                        if st.button("❌ Не знаю", use_container_width=True):
                            ts = min(time.time() - st.session_state.train_start_time, 60)
                            update_daily_training_stats(st.session_state.user_id, False, ts)
                            update_word_stats(st.session_state.user_id, curr['word'], False)
                            st.session_state.train_idx = random.randint(0, len(all_words_flat) - 1)
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
                        st.session_state.feedback_msg = "correct"
                        update_daily_training_stats(st.session_state.user_id, True, ts)
                        update_word_stats(st.session_state.user_id, curr['word'], True)
                    else:
                        st.session_state.feedback_msg = "wrong"
                        update_daily_training_stats(st.session_state.user_id, False, ts)
                        update_word_stats(st.session_state.user_id, curr['word'], False)
                
                if st.session_state.feedback_msg == "correct":
                    st.success("🎉 Correct!")
                    if st.button("Next", use_container_width=True):
                        st.session_state.feedback_msg = None
                        st.session_state.train_idx = random.randint(0, len(all_words_flat) - 1)
                        st.session_state.train_start_time = time.time()
                        st.rerun()
                elif st.session_state.feedback_msg == "wrong":
                    real = curr['meaning'] if "EN ➜ UA" in mode else curr['word']
                    st.error(f"Wrong. It was: {real}")
                    if st.button("Next", use_container_width=True):
                        st.session_state.feedback_msg = None
                        st.session_state.train_idx = random.randint(0, len(all_words_flat) - 1)
                        st.session_state.train_start_time = time.time()
                        st.rerun()
# --- 4. СТАТИСТИКА ---
with t_stats:
    stats = get_statistics(st.session_state.user_id)
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Запитів", stats['translations'])
        c2.metric("Слів", len(get_all_words(st.session_state.user_id)))
        tot = stats['correct'] + stats['wrong']
        acc = int((stats['correct']/tot*100)) if tot > 0 else 0
        c3.metric("Точність", f"{acc}%")
        
    st.markdown("### 📈 Динаміка тренувань")
    daily_data = get_daily_training_stats(st.session_state.user_id)
    
    if not daily_data:
        st.info("Ще немає даних по днях. Пройди своє перше тренування!")
    else:
        df = pd.DataFrame(daily_data)
        # Готуємо дані для графіку
        df['Всього відповідей'] = df['correct_count'] + df['wrong_count']
        df['Правильно'] = df['correct_count']
        df['Помилок'] = df['wrong_count']
        df['Час у тренуванні'] = df['time_spent'].apply(lambda x: f"{int(x//60)} хв {int(x%60)} с")
        df['Дата'] = pd.to_datetime(df['train_date']).dt.strftime('%d.%m.%Y')

        # --- НОВА ЛОГІКА ДЛЯ ОСІ Y ---
        # Знаходимо максимальну кількість відповідей і множимо на 1.5
        max_answers = df['Всього відповідей'].max()
        # Ставимо запобіжник: якщо максимум 0 (наприклад, тільки почав), хай верхня межа буде 10
        y_max = max_answers * 1.5 if max_answers > 0 else 10 

        # Створюємо графік Altair з новим масштабом (scale=alt.Scale(domain=[0, y_max]))
        chart = alt.Chart(df).mark_line(point=True, color='#6366f1', strokeWidth=3).encode(
            x=alt.X('Дата', title='День', sort=None),
            y=alt.Y('Всього відповідей', title='Кількість відповідей', scale=alt.Scale(domain=[0, y_max])),
            tooltip=['Дата', 'Всього відповідей', 'Правильно', 'Помилок', 'Час у тренуванні']
        ).properties(height=350).interactive()

        st.altair_chart(chart, use_container_width=True)