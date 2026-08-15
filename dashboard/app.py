from __future__ import annotations

import pandas as pd
import plotly.express as px
import psycopg
import streamlit as st

from src.config.settings import get_settings

st.set_page_config(page_title="AgroClimate", layout="wide")
st.title("AgroClimate Data Platform")

settings = get_settings()


@st.cache_data(ttl=300)
def load_weather() -> pd.DataFrame:
    query = """
        SELECT
            d.full_date,
            l.city,
            l.state,
            f.avg_temperature,
            f.total_precipitation,
            f.avg_humidity,
            f.avg_wind_speed,
            f.days_without_rain,
            f.drought_risk,
            f.heat_risk,
            f.heavy_rain_risk
        FROM fact_weather_daily f
        JOIN dim_date d ON d.date_id = f.date_id
        JOIN dim_location l ON l.location_id = f.location_id
        ORDER BY d.full_date
    """
    with psycopg.connect(settings.postgres_dsn) as conn:
        return pd.read_sql(query, conn)


try:
    data = load_weather()
except Exception as exc:
    gold_path = settings.gold_dir / "weather_daily"
    try:
        data = pd.read_parquet(gold_path)
        st.warning(f"PostgreSQL indisponivel. Exibindo fallback local Gold Parquet. Detalhe: {exc}")
        data = data.rename(columns={"event_date": "full_date"})
    except Exception:
        st.error(f"PostgreSQL ainda nao retornou dados: {exc}")
        st.stop()

states = sorted(data["state"].dropna().unique())
selected_state = st.sidebar.selectbox("Estado", ["Todos", *states])
filtered = data if selected_state == "Todos" else data[data["state"] == selected_state]

cities = sorted(filtered["city"].dropna().unique())
selected_city = st.sidebar.selectbox("Cidade", ["Todas", *cities])
filtered = filtered if selected_city == "Todas" else filtered[filtered["city"] == selected_city]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Temperatura media", f"{filtered['avg_temperature'].mean():.1f} C")
col2.metric("Chuva acumulada", f"{filtered['total_precipitation'].sum():.1f} mm")
col3.metric("Umidade media", f"{filtered['avg_humidity'].mean():.1f}%")
col4.metric("Vento medio", f"{filtered['avg_wind_speed'].mean():.1f} km/h")

st.plotly_chart(
    px.line(filtered, x="full_date", y="avg_temperature", color="city", title="Temperatura media diaria"),
    use_container_width=True,
)
st.plotly_chart(
    px.bar(filtered, x="city", y="total_precipitation", color="state", title="Precipitacao por cidade"),
    use_container_width=True,
)
