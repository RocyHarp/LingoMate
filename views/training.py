import streamlit as st
import time
import random
import database as db

def render():
    st.markdown("### 🧠 Тренажер")
    
    c_source, c_mode, c_count, c_go = st.columns([1, 1, 1, 1])
    with c_source:
        train_source = st.radio("Джерело:", ["🎲 Випадкове", "🧠 Розумне"], key="rad_train_src")
    with c_mode:
        mode_train = st.radio("Режим:", ["Картки", "Письмо EN-UA", "Письмо UA-EN"], key="rad_train_mod")
    with c_count:
        count_opt = st.radio("Кількість:", [10, 30, 50, "∞ Всі"], key="rad_train_cnt")
    
    with c_go:
        st.write("") 
        if st.button("🔄 Почати", type="primary", use_container_width=True, key="btn_start_train"):
            st.session_state.train_start_time = time.time()
            st.session_state.train_session = []
            st.session_state.session_score = 0
            st.session_state.session_earned_xp = 0 
            st.session_state.bonus_awarded = False
            
            all_words_flat = db.get_all_words(st.session_state.user_id)
            if isinstance(count_opt, int): limit = count_opt
            else: limit = len(all_words_flat)

            if "Розумне" in train_source:
                 st.session_state.train_session = db.get_words_for_smart_training(st.session_state.user_id, limit)
            
            if not st.session_state.get("train_session") and all_words_flat:
                 temp = all_words_flat.copy()
                 random.shuffle(temp)
                 st.session_state.train_session = temp[:limit]
            
            st.session_state.train_idx = 0
            st.rerun()

    if 'train_session' in st.session_state and st.session_state.train_session:
        idx = st.session_state.train_idx
        total_q = len(st.session_state.train_session)
        
        # --- КІНЕЦЬ ТРЕНУВАННЯ ---
        if idx >= total_q:
             score = st.session_state.get('session_score', 0)
             percent = int((score / total_q) * 100) if total_q > 0 else 0
             
             if not st.session_state.get('bonus_awarded', False):
                 if percent >= 75:
                     db.add_user_bonus_xp(st.session_state.user_id, 50) 
                     st.session_state.session_earned_xp += 50
                 st.session_state.bonus_awarded = True
             
             st.balloons()
             with st.container(border=True):
                 st.markdown(f"<h2 style='text-align:center'>Тренування завершено! 🎉</h2>", unsafe_allow_html=True)
                 st.markdown(f"<h3 style='text-align:center; color:#3b82f6'>{score} / {total_q} ({percent}%)</h3>", unsafe_allow_html=True)
                 
                 if percent == 100: msg = "🔥 Ідеально! Ти машина!"
                 elif percent >= 75: msg = "😎 Чудовий результат!"
                 elif percent >= 50: msg = "👍 Непогано, але можна краще."
                 else: msg = "🐢 Треба ще підучити слова."
                 
                 st.info(msg)
                 if percent >= 75: st.success(f"🎁 Бонус за відмінний результат: +50 XP")
                 st.success(f"⭐ Загалом зароблено за тренування: {st.session_state.session_earned_xp} XP")
                 
                 if st.button("Ще раз?", use_container_width=True):
                     st.session_state.train_session = []
                     st.rerun()
                     
        # --- ПРОЦЕС ТРЕНУВАННЯ ---
        else:
            curr = st.session_state.train_session[idx]
            st.markdown(f"<h3 style='margin:0; color:#60a5fa;'>{idx + 1} <span style='color:gray; font-size:18px;'>/ {total_q}</span></h3>", unsafe_allow_html=True)
            st.progress((idx) / total_q)

            st.write("")
            if 'show_answer' not in st.session_state: st.session_state.show_answer = False
            
            q_text = curr['word']
            is_synonym = curr['parent_id'] is not None
            sub_text = "Синонім" if is_synonym else curr.get('word_type', '')
            
            if "UA-EN" in mode_train:
                q_text = curr['meaning']
                sub_text = "Як це англійською?" + (" (Синонім)" if is_synonym else "")
                
            with st.container(border=True):
                st.markdown(f"<h1 style='text-align:center; margin-top:-10px; margin-bottom: 20px;'>{q_text}</h1>", unsafe_allow_html=True)
                if is_synonym and curr.get('nuance') and "UA-EN" not in mode_train:
                     st.info(f"💡 Підказка: {curr['nuance']}")
                else: 
                     if sub_text: st.markdown(f"<div style='text-align:center; color:#64748b; margin-bottom:20px;'>{sub_text}</div>", unsafe_allow_html=True)
            
            if mode_train == "Картки":
                if st.session_state.show_answer:
                    st.success(f"**{curr['meaning']}**")
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("✅ Знаю", use_container_width=True, key=f"k_btn_{idx}"):
                            ts = min(time.time() - st.session_state.train_start_time, 60)
                            db.update_daily_training_stats(st.session_state.user_id, True, ts)
                            db.update_word_stats(st.session_state.user_id, curr['word'], True) 
                            
                            st.session_state.session_earned_xp += 5
                            st.session_state.session_score += 1
                            st.session_state.train_idx += 1
                            st.session_state.show_answer = False
                            st.session_state.train_start_time = time.time()
                            st.rerun()
                    with b2:
                        if st.button("❌ Не знаю", use_container_width=True, key=f"nk_btn_{idx}"):
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
                ans = st.text_input("Відповідь", placeholder="...", label_visibility="collapsed", key=f"ans_in_{idx}")
                if st.button("Перевірити", type="primary", use_container_width=True, key=f"chk_btn_{idx}"):
                    is_cor = False
                    if "EN-UA" in mode_train:
                         opts = [x.strip().lower() for x in curr['meaning'].replace('/', ',').split(',')]
                         if ans.strip().lower() in opts: is_cor = True
                    elif "UA-EN" in mode_train:
                         if ans.strip().lower() == curr['word'].strip().lower(): is_cor = True
                         
                    ts = min(time.time() - st.session_state.train_start_time, 60)
                    if is_cor:
                        st.success(f"🎉 Правильно! (+10 XP)")
                        db.update_daily_training_stats(st.session_state.user_id, True, ts)
                        db.update_word_stats(st.session_state.user_id, curr['word'], True) 
                        db.add_user_bonus_xp(st.session_state.user_id, 5) 
                        
                        st.session_state.session_earned_xp += 10
                        st.session_state.session_score += 1
                    else:
                        st.error(f"Помилка. Правильно: {curr['meaning'] if 'EN' in mode_train else curr['word']}")
                        db.update_daily_training_stats(st.session_state.user_id, False, ts)
                        db.update_word_stats(st.session_state.user_id, curr['word'], False)
                    
                    time.sleep(1.5)
                    st.session_state.train_idx += 1
                    st.session_state.train_start_time = time.time()
                    st.rerun()
            
            if st.button("Пропустити"):
                 st.session_state.train_idx += 1; st.rerun()
    else:
        if not db.get_all_words(st.session_state.user_id):
            st.warning("Спочатку додай слова в словник!")
        else:
            st.info("Натисни 'Почати'")