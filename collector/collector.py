# collector/collector.py
import os
import time
import datetime
import csv
import json
import psycopg2
from FlightRadar24 import FlightRadar24API

# Параметры подключения к базе данных (получаются из переменных окружения)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "flights_db")
DB_USER = os.getenv("DB_USER", "myuser")
DB_PASS = os.getenv("DB_PASS", "mypass")

# Границы акватории Чёрного моря: [min_lat, max_lat, min_lon, max_lon]
BOUNDS = [40.5, 47.6, 26.8, 42.3]


def get_flight_data():
    """
    Получает данные с портала Flightradar24 через неофициальный API и возвращает список словарей.
    Для каждого рейса извлекаются: позывной, ICAO, авиакомпания, модель самолёта,
    маршрут (trail) и текущие координаты.
    """
    try:
        fr_api = FlightRadar24API()
        flights = fr_api.get_flights(bounds=BOUNDS)
    except Exception as e:
        print("Ошибка запроса к Flightradar24:", e)
        return []

    timestamp = datetime.datetime.utcnow().isoformat()
    results = []
    for flight_id, flight in flights.items():
        flight_data = flight.get('flight', {})
        callsign = flight_data.get('callsign')
        icao24 = flight_data.get('icao24')
        airline = flight_data.get('airline')  # может быть None, если данные отсутствуют
        aircraft = flight_data.get('aircraft', {})
        aircraft_model = aircraft.get('model')
        # Получаем маршрут – список координат, если доступно
        trail = flight.get('trail', [])
        route_json = json.dumps(trail) if trail else None
        # Определяем текущие координаты – берем последнюю точку из маршрута, если она есть
        if trail and len(trail) > 0:
            current_lat = trail[-1][0]
            current_lon = trail[-1][1]
        else:
            current_lat = None
            current_lon = None

        results.append({
            'timestamp': timestamp,
            'icao24': icao24,
            'callsign': callsign,
            'airline': airline,
            'aircraft_model': aircraft_model,
            'route': route_json,
            'current_lat': current_lat,
            'current_lon': current_lon
        })
    return results


def save_to_csv(records):
    """
    Сохраняет записи в CSV‑файл.
    Имя файла формируется по текущей дате (например, flights_2025-04-02.csv).
    """
    if not records:
        return

    date_str = records[0]['timestamp'][:10]  # извлекаем дату в формате YYYY-MM-DD
    filename = f"flights_{date_str}.csv"
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = list(records[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for rec in records:
            writer.writerow(rec)
    print(f"CSV сохранён: {filename}")


def save_to_db(records):
    """
    Сохраняет записи в таблицу PostgreSQL (таблица flights).
    """
    if not records:
        return

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        for rec in records:
            cur.execute("""
                INSERT INTO flights 
                (timestamp, icao24, callsign, airline, aircraft_model, route, current_lat, current_lon)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                rec['timestamp'], rec['icao24'], rec['callsign'], rec['airline'],
                rec['aircraft_model'], rec['route'], rec['current_lat'], rec['current_lon']
            ))
        conn.commit()
        cur.close()
        conn.close()
        print("Данные сохранены в базе данных.")
    except Exception as e:
        print("Ошибка при сохранении в БД:", e)


def init_db():
    """
    Инициализирует базу данных: создаёт таблицу flights, если она ещё не существует.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS flights (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMPTZ,
                icao24 VARCHAR(6),
                callsign VARCHAR(10),
                airline VARCHAR(50),
                aircraft_model VARCHAR(20),
                route TEXT,
                current_lat DOUBLE PRECISION,
                current_lon DOUBLE PRECISION
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("База данных и таблица flights инициализированы.")
    except Exception as e:
        print("Ошибка инициализации БД:", e)


if __name__ == "__main__":
    init_db()
    while True:
        print(f"\n[{datetime.datetime.utcnow().isoformat()}] Сбор данных с Flightradar24...")
        records = get_flight_data()
        if records:
            save_to_csv(records)
            save_to_db(records)
            print(f"Сохранено {len(records)} записей.")
        else:
            print("Нет данных для сохранения.")
        # Ждём 5 минут до следующего запроса
        time.sleep(300)
