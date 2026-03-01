import streamlit as st
import pandas as pd
import altair as alt
import database as db

def render():
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
    else: 
        st.info("Тренуйся більше, щоб побачити графік!")