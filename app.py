import streamlit as st
import time
import database as db
from logic import backendLogic
from utils import get_xp_progress, calc_level_from_raw_data
from views import translate, dictionary, training, stats

# --- 1. НАЛАШТУВАННЯ СТОРІНКИ ---
st.set_page_config(page_title="LingoMate", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

def load_css(file_name):
    with open(file_name, "r") as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
load_css("style.css")

db.init_db()
@st.cache_resource
def get_logic(): return backendLogic()
logic = get_logic()

if 'show_menu' not in st.session_state: st.session_state.show_menu = False
if 'active_tab' not in st.session_state: st.session_state.active_tab = "trans"

# Функція визначення Титулу (Рангу) на основі рівня
def get_rank_title(level):
    if level < 5: return "🌱 Новачок"
    elif level < 10: return "📚 Студент"
    elif level < 20: return "🎓 Знавець"
    elif level < 50: return "🧠 Майстер"
    else: return "👑 Легенда"

# ==========================================
#  МОДАЛЬНЕ ВІКНО АВАТАРІВ
# ==========================================
@st.dialog("Обери свій аватар")
def avatar_modal():
    avatars = ["🦊", "🐱", "🐶", "🐼", "🐻", "🤖", "👽", "👻", "🤓", "😎", "👾", "🧙‍♂️", "🦁", "🐯", "🐸", "🐵"]
    a_cols = st.columns(4)
    for i, av in enumerate(avatars):
        if a_cols[i % 4].button(av, key=f"set_av_{i}", use_container_width=True):
            try: db.update_user_avatar(st.session_state.user_id, av)
            except: pass
            st.session_state.avatar = av
            st.rerun()

# ==========================================
#  ЕКРАН ВХОДУ
# ==========================================
if "user_id" not in st.session_state:
    st.write(""); st.write("")
    _, cent, _ = st.columns([1, 1.2, 1])
    with cent:
        st.markdown("<h1 style='text-align:center;'>⚡ LingoMate</h1>", unsafe_allow_html=True)
        with st.container(border=True):
            tab_log, tab_reg = st.tabs(["Вхід", "Реєстрація"])
            with tab_log:
                u = st.text_input("Логін", key="l_u")
                p = st.text_input("Пароль", type="password", key="l_p")
                if st.button("Увійти", type="primary", use_container_width=True):
                    user = db.login_user(u, p)
                    if user:
                        st.session_state.user_id = user[0]
                        st.session_state.is_premium = user[1]
                        st.session_state.username = u
                        st.session_state.show_menu = True
                        try: st.session_state.avatar = db.get_user_avatar(user[0])
                        except: st.session_state.avatar = "🦊"
                        st.rerun()
                    else: st.error("Помилка входу")
            with tab_reg:
                ru = st.text_input("Новий логін", key="r_u")
                re = st.text_input("Email", key="r_e")
                rp = st.text_input("Новий пароль", type="password", key="r_p")
                if st.button("Створити акаунт", use_container_width=True):
                    if db.register_user(ru, re, rp): st.success("Готово! Увійдіть.")
                    else: st.error("Помилка реєстрації")
    st.stop()

# ==========================================
#  ШАПКА ТА ЛЕЯУТ
# ==========================================
header_col1, header_col2, header_space = st.columns([0.06, 0.3, 0.64])
with header_col1:
    if st.button("⚡", key="main_toggle"):
        st.session_state.show_menu = not st.session_state.show_menu
        st.rerun()
    st.markdown("""<script>
    const buttons = window.parent.document.querySelectorAll('button');
    buttons.forEach(btn => { if (btn.innerText === '⚡') btn.classList.add('menu-btn'); });
    </script>""", unsafe_allow_html=True)
with header_col2:
    st.markdown('<div class="app-logo">LingoMate</div>', unsafe_allow_html=True)

if st.session_state.show_menu:
    col_menu, col_main = st.columns([1.3, 4])
else:
    col_menu = None
    col_main = st.container()

# ==========================================
#  ОНОВЛЕНЕ БОКОВЕ МЕНЮ 
# ==========================================
if col_menu:
    with col_menu:
        with st.container(border=True):
            
            # --- 1. БЛОК ПРОФІЛЮ ---
            st.write("") 
            current_av = st.session_state.get("avatar", "🦊")
            st.markdown(f'<div class="profile-avatar-display">{current_av}</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="edit-avatar-container">', unsafe_allow_html=True)
            _, c_edit_btn, _ = st.columns([1, 2, 1]) 
            with c_edit_btn:
                 if st.button("✏️ Змінити", key="change_av_small_btn", use_container_width=True, help="Обрати новий аватар"):
                     avatar_modal()
            st.markdown('</div>', unsafe_allow_html=True)
            
            username = st.session_state.get("username", "User")
            is_pro = st.session_state.get("is_premium", 0) == 1
            pro_badge = '<span class="pro-badge">PRO</span>' if is_pro else ''
            
            st.markdown(f'<div class="profile-title">{username} {pro_badge}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="profile-id">ID: {st.session_state.user_id}</div>', unsafe_allow_html=True)
            
            # --- 2. РІВЕНЬ ТА РАНГ ---
            lvl, curr_xp, prog_width = get_xp_progress(st.session_state.user_id)
            rank = get_rank_title(lvl)
            
            st.markdown(f"""
            <div class="level-container">
                <div class="level-header">
                    <span>Рівень {lvl}</span>
                    <span>{curr_xp} / 1000 XP</span>
                </div>
                <div class="level-rank">{rank}</div>
                <div class="progress-track">
                    <div class="progress-fill" style="width: {prog_width}%;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # --- 3. СТАТИСТИКА (ОПТИМІЗОВАНО) ---
            total_w = db.get_word_count(st.session_state.user_id) # Швидка лічилка!
            stats_db = db.get_statistics(st.session_state.user_id)
            
            st.markdown(f"""
            <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                <div class="menu-stat-box" style="flex: 1;">
                    <div class="menu-stat-num">{total_w}</div>
                    <div class="menu-stat-label">Слів</div>
                </div>
                <div class="menu-stat-box" style="flex: 1;">
                    <div class="menu-stat-num">{stats_db['translations']}</div>
                    <div class="menu-stat-label">Перекладів</div>
                </div>
            </div>""", unsafe_allow_html=True)
            # --- 4. ДРУЗІ (ОПТИМІЗОВАНО) ---
            with st.expander("👥 Друзі та Рейтинг", expanded=True):
                new_f = st.text_input("ID друга", label_visibility="collapsed", placeholder="Введи ID...", key="f_input_side")
                if st.button("➕ Додати друга", use_container_width=True, key="add_friend_btn_side"):
                    msg = db.add_friend(st.session_state.user_id, new_f)
                    if "Успішно" in msg: st.success(msg)
                    else: st.warning(msg)
                    time.sleep(1); st.rerun()
                
                friends = db.get_friends_leaderboard(st.session_state.user_id)
                if friends:
                    for f in friends:
                        f_name = f['username']
                        f_words = f.get('total_words', 0)
                        
                        # Миттєво рахуємо рівень друга з готових цифр:
                        f_lvl = calc_level_from_raw_data(
                            f['total_words'], 
                            f['translations'], 
                            f.get('total_correct', 0) if f.get('total_correct') else 0, 
                            f.get('bonus_xp', 0)
                        )
                        f_av = f.get('avatar', '👤')
                            
                        st.markdown(f"""
                        <div class="friend-card">
                            <div class="friend-avatar">{f_av}</div>
                            <div style="flex:1;">
                                <div style="font-weight:bold; font-size:14px; color:#f8fafc;">{f_name}</div>
                                <div style="font-size:11px; color:#94a3b8;">Рівень {f_lvl} • {f_words} слів</div>
                            </div>
                        </div>""", unsafe_allow_html=True)
                else: st.caption("Ти поки що самотній вовк 🐺")

            # --- 5. РОЗШИРЕНІ НАЛАШТУВАННЯ ---
            with st.expander("⚙️ Налаштування акаунта", expanded=False):
                st.markdown("**Змінити Нікнейм**")
                new_nick = st.text_input("Новий нік", value=st.session_state.username, label_visibility="collapsed", key="change_nick_in")
                if st.button("Зберегти нік", use_container_width=True, key="save_nick_btn"):
                    try:
                        if db.change_username(st.session_state.user_id, new_nick):
                            st.session_state.username = new_nick
                            st.success("Нік змінено!")
                            time.sleep(1); st.rerun()
                        else: st.error("Цей нік вже зайнятий!")
                    except Exception as e: st.error("Помилка бази даних.")

                st.markdown("---")
                st.markdown("**Змінити Пароль**")
                np = st.text_input("Новий пароль", type="password", label_visibility="collapsed", key="ch_pass_side")
                if st.button("Зберегти пароль", use_container_width=True, key="save_pass_btn_side"):
                    if db.change_password(st.session_state.user_id, np): st.success("Пароль оновлено!")
                
                st.markdown('<div class="danger-zone"><div class="danger-text">⚠️ НЕБЕЗПЕЧНА ЗОНА</div></div>', unsafe_allow_html=True)
                if st.button("🗑️ Видалити профіль", use_container_width=True, type="secondary", key="del_acc_btn"):
                    db.delete_account(st.session_state.user_id)
                    del st.session_state.user_id; st.rerun()

            st.write("")
            if st.button("🚪 Вийти з акаунта", use_container_width=True, key="logout_btn_side", type="primary"):
                del st.session_state.user_id; st.rerun()

# ==========================================
#  КОНТЕНТ (СПРАВА)
# ==========================================
with col_main:
    nav1, nav2, nav3, nav4 = st.columns(4)
    if nav1.button("💬 Перекладач", use_container_width=True, type="primary" if st.session_state.active_tab == "trans" else "secondary"): 
        st.session_state.active_tab = "trans"; st.rerun()
    if nav2.button("📚 Словник", use_container_width=True, type="primary" if st.session_state.active_tab == "dict" else "secondary"): 
        st.session_state.active_tab = "dict"; st.rerun()
    if nav3.button("🧠 Тренування", use_container_width=True, type="primary" if st.session_state.active_tab == "train" else "secondary"): 
        st.session_state.active_tab = "train"; st.rerun()
    if nav4.button("📊 Статистика", use_container_width=True, type="primary" if st.session_state.active_tab == "stats" else "secondary"): 
        st.session_state.active_tab = "stats"; st.rerun()
    
    st.write("---")

    # ВИКЛИК ВКЛАДОК З ПРАВИЛЬНИМИ ПАРАМЕТРАМИ
    if st.session_state.active_tab == "trans":
        translate.render(logic)
    elif st.session_state.active_tab == "dict":
        dictionary.render(logic)
    elif st.session_state.active_tab == "train":
        training.render()
    elif st.session_state.active_tab == "stats":
        stats.render()
