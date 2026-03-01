import streamlit as st
import pandas as pd
import altair as alt
import database as db

def render():
    stats = db.get_statistics(st.session_state.user_id)
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        c1.metric("Запитів", stats['translations'])
        
        # Використовуємо нашу нову оптимізовану лічилку!
        c2.metric("Слів", db.get_word_count(st.session_state.user_id))
        
        tot = stats['correct'] + stats['wrong']
        acc = int((stats['correct']/tot*100)) if tot > 0 else 0
        c3.metric("Точність", f"{acc}%")
        
    st.markdown("### 📈 Динаміка")
    daily_data = db.get_daily_training_stats(st.session_state.user_id)
    if daily_data:
        df = pd.DataFrame(daily_data)
        
        # 🐛 ФІКС БАГУ: Називаємо колонки англійською всередині датафрейму
        df['total_words'] = df['correct_count'] + df['wrong_count']
        df['date_str'] = pd.to_datetime(df['train_date']).dt.strftime('%d.%m')
        
        y_max = df['total_words'].max() * 1.5 if df['total_words'].max() > 0 else 10
        
        # 🎨 А отут через 'title' задаємо красиві українські підписи
        chart = alt.Chart(df).mark_line(point=True, color='#6366f1', strokeWidth=3).encode(
            x=alt.X('date_str', sort=None, title='Дата'),
            y=alt.Y('total_words', scale=alt.Scale(domain=[0, y_max]), title='Вивчено слів'),
            tooltip=[
                alt.Tooltip('train_date', title='Дата'),
                alt.Tooltip('total_words', title='Всього'),
                alt.Tooltip('correct_count', title='Правильно'),
                alt.Tooltip('wrong_count', title='Помилок')
            ]
        ).properties(height=350).interactive()
        
        st.altair_chart(chart, use_container_width=True)
    else: 
        st.info("Тренуйся більше, щоб побачити графік!")
