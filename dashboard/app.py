# dashboard/app.py
import os
import pandas as pd
import psycopg2
import streamlit as st

# Получаем параметры подключения к БД из переменных окружения
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "flights_db")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASS = os.getenv("DB_PASS", "mypass")


def load_data():
    """
    Загружает данные за последние 24 часа из таблицы flights.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        query = "SELECT * FROM flights WHERE timestamp >= NOW() - INTERVAL '1 day';"
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Ошибка подключения к БД: {e}")
        return pd.DataFrame()


# Кэшируем данные на 5 минут, чтобы не нагружать базу
df = st.cache_data(load_data, ttl=300)()

st.title("Мониторинг рейсов над Чёрным морем (Flightradar24)")

if df.empty:
    st.write("Нет данных для отображения.")
else:
    st.subheader("Данные за последние 24 часа")
    st.write(df.head())

    # Группировка по моделям самолётов
    if 'aircraft_model' in df.columns:
        model_counts = df['aircraft_model'].value_counts().dropna()
        st.subheader("Распределение типов самолётов")
        st.bar_chart(model_counts)

    # Группировка по авиакомпаниям
    if 'airline' in df.columns:
        airline_counts = df['airline'].value_counts().dropna()
        st.subheader("Распределение по авиакомпаниям")
        st.bar_chart(airline_counts)

    # Отображение текущих позиций бортов на карте
    if 'current_lat' in df.columns and 'current_lon' in df.columns:
        latest_positions = df.dropna(subset=['current_lat', 'current_lon'])
        st.subheader("Текущее положение бортов")
        # Для st.map переименовываем колонки в 'lat' и 'lon'
        st.map(latest_positions[['current_lat', 'current_lon']].rename(
            columns={'current_lat': 'lat', 'current_lon': 'lon'}))
