import streamlit as st
import time
import random
from PIL import Image
import database as db

def render(logic):
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
            if st.button("⇄", use_container_width=True, key="swap_langs_main"):
                st.session_state.trans_src, st.session_state.trans_dst = st.session_state.trans_dst, st.session_state.trans_src
                st.rerun()
        with ls_col2: st.markdown(f'<div class="lang-label lang-active">{st.session_state.trans_dst}</div>', unsafe_allow_html=True)
        st.write("")
        
        text_input = st.text_area("Введення", value=st.session_state.input_text, height=text_height, placeholder="Введіть текст...", label_visibility="collapsed", key="area_trans_main")
        
        if st.button("🚀 Перекласти", type="primary", use_container_width=True, key="btn_translate_main"):
            if text_input:
                db.increment_translation_count(st.session_state.user_id)
                with st.spinner("Аналізую..."):
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
                st.caption("Преміум функція.")
            st.divider()
            mode = st.radio("Режим", ["⌨️ Текст", "📸 Фото"], key="input_mode", label_visibility="collapsed")
            if "Фото" in mode:
                f = st.file_uploader("Upload", type=["jpg", "png", "jpeg"], label_visibility="collapsed", key="file_ocr_main")
                if f and st.button("📷 Сканувати", key="btn_ocr_main"):
                    img = Image.open(f); img.save("temp.png")
                    st.session_state.input_text = logic.get_text_from_image("temp.png")
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
                    if st.button("🔄 Оновити", key="btn_update_word"):
                        db.update_word_meaning(st.session_state.user_id, st.session_state.input_text, res['translation'])
                        st.toast("Оновлено!")
                else:
                    if st.button("💾 Зберегти", key="btn_save_word"):
                        db.save_word(st.session_state.user_id, st.session_state.input_text, res['translation'], "phrase")
                        st.toast("Збережено! XP +10")
        
        if res.get('context_ua'):
            if "ERROR" in res['context_ua']: st.error(res['context_ua'])
            elif res['context_ua'].strip(): st.info(f"🧠 **Аналіз:** {res['context_ua']}")

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
                                    st.toast(f"Додано: {w_text} (+10 XP)")
                                    time.sleep(0.5); st.rerun()
                        with btn_col2:
                            if w_text and w_text != "???":
                                if st.button("❔", key=f"nuance_{w_text}_{random.randint(1,10000)}"):
                                    with st.spinner("⏳"):
                                        res_nuance = logic.explain_nuance(w_text, st.session_state.input_text)
                                        if res_nuance and isinstance(res_nuance, dict):
                                            st.session_state[f"dict_expl_{w_text}"] = res_nuance.get('explanation', '')
                                        else: st.toast("AI не відповів.", icon="⚠️")
                    
                    if f"expl_{w_text}" in st.session_state: st.info(f"💡 {st.session_state[f'expl_{w_text}']}")
                    st.divider()