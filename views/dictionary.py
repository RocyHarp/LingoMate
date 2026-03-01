import streamlit as st
import time
import database as db

def render(logic):
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