from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import get_settings  # noqa: E402

st.set_page_config(page_title="AgroClimate", page_icon="AG", layout="wide")

settings = get_settings()

RISK_LABELS = {"normal": "Normal", "high": "Alto"}
RISK_LEVEL_COLORS = {"Normal": "#15803d", "Atencao": "#ca8a04", "Critico": "#b91c1c"}
CHART_PALETTE = ["#166534", "#2563eb", "#ca8a04", "#7c3aed", "#dc2626", "#0891b2", "#4d7c0f", "#9333ea"]
IBGE_STATE_CODE_TO_UF = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1320px;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #0f172a;
        font-size: 1.18rem;
        font-weight: 750;
        margin-bottom: 0.1rem;
    }

    [data-testid="stSidebar"] .stCaptionContainer {
        color: #475569;
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.55rem 0.7rem;
        margin: 0.4rem 0 1rem;
    }

    [data-testid="stSidebar"] label p {
        color: #334155;
        font-size: 0.86rem;
        font-weight: 650;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="input"] > div {
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        min-height: 2.7rem;
        box-shadow: none;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div:hover,
    [data-testid="stSidebar"] [data-baseweb="input"] > div:hover {
        border-color: #16a34a;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
    }

    div[data-testid="stMetricValue"] {
        color: #0f172a;
        font-size: 1.55rem;
        font-weight: 760;
    }

    div[data-testid="stMetricLabel"] p {
        color: #475569;
        font-size: 0.85rem;
        font-weight: 650;
    }

    .agro-hero {
        border-left: 5px solid #16a34a;
        padding: 0.2rem 0 0.3rem 1rem;
        margin-bottom: 1rem;
    }

    .agro-hero h1 {
        margin: 0;
        color: #0f172a;
        font-size: 2rem;
        line-height: 1.15;
    }

    .agro-hero p {
        color: #475569;
        margin: 0.4rem 0 0;
        font-size: 1rem;
    }

    .agro-insight {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.9rem 1rem;
        color: #334155;
        min-height: 5.4rem;
    }

    .agro-insight strong {
        color: #0f172a;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        border-bottom: 1px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.55rem 0.9rem;
        font-weight: 650;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300)
def load_weather_from_postgres() -> pd.DataFrame:
    query = """
        SELECT
            d.full_date,
            l.city,
            l.state,
            l.region,
            l.latitude,
            l.longitude,
            f.avg_temperature,
            f.max_temperature,
            f.min_temperature,
            f.total_precipitation,
            f.avg_humidity,
            f.avg_wind_speed,
            f.max_wind_speed,
            f.solar_radiation,
            f.evapotranspiration,
            f.days_without_rain,
            f.precipitation_accumulated_7d,
            f.precipitation_accumulated_30d,
            f.avg_temperature_7d,
            f.avg_temperature_30d,
            f.thermal_amplitude,
            f.drought_risk,
            f.heat_risk,
            f.heavy_rain_risk
        FROM fact_weather_daily f
        JOIN dim_date d ON d.date_id = f.date_id
        JOIN dim_location l ON l.location_id = f.location_id
        ORDER BY d.full_date, l.city
    """
    with psycopg.connect(settings.postgres_dsn) as conn:
        return pd.read_sql(query, conn)


@st.cache_data(ttl=300)
def load_weather(gold_updated_at: float | None) -> tuple[pd.DataFrame, str]:
    try:
        data = load_weather_from_postgres()
        source_label = "PostgreSQL warehouse"
    except Exception:
        gold_path = settings.gold_dir / "weather_daily"
        data = pd.read_parquet(gold_path).rename(columns={"event_date": "full_date"})
        source_label = "Gold Parquet local"

    data["full_date"] = pd.to_datetime(data["full_date"])
    risk_columns = ["drought_risk", "heat_risk", "heavy_rain_risk"]
    for column in risk_columns:
        if column not in data:
            data[column] = "normal"

    data["risk_events"] = data[risk_columns].eq("high").sum(axis=1)
    data["risk_level"] = pd.cut(
        data["risk_events"],
        bins=[-1, 0, 1, 3],
        labels=["Normal", "Atencao", "Critico"],
    )
    return data.sort_values(["full_date", "state", "city"]), source_label


def gold_dataset_updated_at() -> float | None:
    gold_path = settings.gold_dir / "weather_daily"
    if not gold_path.exists():
        return None
    return max(path.stat().st_mtime for path in gold_path.rglob("*.parquet"))


def agriculture_dataset_updated_at() -> float | None:
    agriculture_path = settings.gold_dir / "agriculture_summary"
    if not agriculture_path.exists():
        return None
    parquet_files = list(agriculture_path.rglob("*.parquet"))
    return max(path.stat().st_mtime for path in parquet_files) if parquet_files else None


@st.cache_data(ttl=300)
def load_agriculture(gold_updated_at: float | None) -> pd.DataFrame:
    agriculture_path = settings.gold_dir / "agriculture_summary"
    if not agriculture_path.exists():
        return pd.DataFrame()
    data = pd.read_parquet(agriculture_path)
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    numeric_columns = [
        "produced_quantity",
        "harvested_area",
        "production_value",
        "reported_yield_kg_ha",
        "reported_yield_t_ha",
        "calculated_yield_t_ha",
    ]
    for column in numeric_columns:
        if column in data:
            data[column] = pd.to_numeric(data[column], errors="coerce")
    return data.sort_values(["year", "territory_name", "product_name"])


def format_delta(current: float, previous: float | None, suffix: str = "") -> str | None:
    if previous is None or pd.isna(previous):
        return None
    return f"{current - previous:+.1f}{suffix}"


def latest_snapshot(frame: pd.DataFrame) -> tuple[pd.Series, pd.Series | None]:
    latest_date = frame["full_date"].max()
    latest = frame[frame["full_date"] == latest_date]
    previous_dates = sorted(frame.loc[frame["full_date"] < latest_date, "full_date"].unique())
    previous = frame[frame["full_date"] == previous_dates[-1]] if previous_dates else None

    current = pd.Series(
        {
            "avg_temperature": latest["avg_temperature"].mean(),
            "total_precipitation": latest["total_precipitation"].sum(),
            "avg_humidity": latest["avg_humidity"].mean(),
            "risk_events": latest["risk_events"].sum(),
        }
    )
    if previous is None:
        return current, None

    baseline = pd.Series(
        {
            "avg_temperature": previous["avg_temperature"].mean(),
            "total_precipitation": previous["total_precipitation"].sum(),
            "avg_humidity": previous["avg_humidity"].mean(),
            "risk_events": previous["risk_events"].sum(),
        }
    )
    return current, baseline


def risk_summary(frame: pd.DataFrame) -> pd.DataFrame:
    return (
        frame.groupby(["city", "state"], as_index=False)
        .agg(
            dias_monitorados=("full_date", "nunique"),
            eventos_de_risco=("risk_events", "sum"),
            maior_sequencia_seca=("days_without_rain", "max"),
            chuva_7d_max=("precipitation_accumulated_7d", "max"),
            temperatura_maxima=("max_temperature", "max"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
        )
        .sort_values(["eventos_de_risco", "maior_sequencia_seca", "temperatura_maxima"], ascending=False)
    )


def plot_layout(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        font={"family": "Arial, sans-serif", "color": "#334155"},
        title={"font": {"size": 18, "color": "#0f172a"}},
        legend_title_text="",
        margin={"l": 10, "r": 10, "t": 55, "b": 10},
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    fig.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig.update_yaxes(gridcolor="#e2e8f0", linecolor="#e2e8f0")
    return fig


def render_insights(frame: pd.DataFrame) -> None:
    summary = risk_summary(frame)
    hottest = frame.loc[frame["max_temperature"].idxmax()]
    rainiest = (
        frame.groupby(["city", "state"], as_index=False)["total_precipitation"].sum().nlargest(1, "total_precipitation")
    )
    riskiest = summary.iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.markdown(
        f"""
        <div class="agro-insight">
            <strong>Ponto de atencao</strong><br>
            {riskiest.city}/{riskiest.state} concentra {int(riskiest.eventos_de_risco)} eventos de risco
            no periodo filtrado.
        </div>
        """,
        unsafe_allow_html=True,
    )
    col2.markdown(
        f"""
        <div class="agro-insight">
            <strong>Maior temperatura</strong><br>
            {hottest.city}/{hottest.state} registrou {hottest.max_temperature:.1f} C em
            {hottest.full_date:%d/%m/%Y}.
        </div>
        """,
        unsafe_allow_html=True,
    )
    col3.markdown(
        f"""
        <div class="agro-insight">
            <strong>Maior acumulado de chuva</strong><br>
            {rainiest.iloc[0].city}/{rainiest.iloc[0].state} acumulou
            {rainiest.iloc[0].total_precipitation:.1f} mm.
        </div>
        """,
        unsafe_allow_html=True,
    )


data, source_label = load_weather(gold_dataset_updated_at())
agriculture = load_agriculture(agriculture_dataset_updated_at())

with st.sidebar:
    st.header("Filtros")
    st.caption(f"Fonte ativa: {source_label}")

    min_date = data["full_date"].min().date()
    max_date = data["full_date"].max().date()
    date_range = st.date_input("Periodo", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if len(date_range) == 2:
        start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start_date = end_date = pd.to_datetime(date_range[0])

    states = sorted(data["state"].dropna().unique())
    selected_state = st.selectbox("Estado", ["Todos", *states])
    selected_states = states if selected_state == "Todos" else [selected_state]

    available_cities = sorted(data.loc[data["state"].isin(selected_states), "city"].dropna().unique())
    selected_city = st.selectbox("Cidade", ["Todas", *available_cities])
    selected_cities = available_cities if selected_city == "Todas" else [selected_city]

    risk_options = ["Normal", "Atencao", "Critico"]
    selected_risk = st.selectbox("Risco", ["Todos", *risk_options])
    selected_risks = risk_options if selected_risk == "Todos" else [selected_risk]

filtered = data[
    (data["full_date"].between(start_date, end_date))
    & (data["state"].isin(selected_states))
    & (data["city"].isin(selected_cities))
    & (data["risk_level"].astype(str).isin(selected_risks))
].copy()

st.markdown(
    """
    <div class="agro-hero">
        <h1>AgroClimate</h1>
        <p>Visao executiva de clima, chuva e risco para regioes agricolas monitoradas.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if filtered.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

current, previous = latest_snapshot(filtered)
latest_date = filtered["full_date"].max().strftime("%d/%m/%Y")

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Temperatura media",
    f"{current['avg_temperature']:.1f} C",
    format_delta(current["avg_temperature"], None if previous is None else previous["avg_temperature"], " C"),
)
col2.metric(
    "Chuva no ultimo dia",
    f"{current['total_precipitation']:.1f} mm",
    format_delta(current["total_precipitation"], None if previous is None else previous["total_precipitation"], " mm"),
)
col3.metric(
    "Umidade media",
    f"{current['avg_humidity']:.1f}%",
    format_delta(current["avg_humidity"], None if previous is None else previous["avg_humidity"], "%"),
)
col4.metric(
    "Eventos de risco",
    f"{int(current['risk_events'])}",
    format_delta(current["risk_events"], None if previous is None else previous["risk_events"]),
)

st.caption(
    f"Ultima leitura: {latest_date} | {filtered['city'].nunique()} cidades | "
    f"{filtered['state'].nunique()} estados | {len(filtered):,} registros".replace(",", ".")
)

render_insights(filtered)

overview_tab, risk_tab, water_tab, agriculture_tab, table_tab = st.tabs(
    ["Panorama", "Riscos", "Balanco hidrico", "Agricultura", "Analise basica"]
)

with overview_tab:
    left, right = st.columns([1.35, 1])

    daily_state = (
        filtered.groupby(["full_date", "state"], as_index=False)
        .agg(avg_temperature=("avg_temperature", "mean"), total_precipitation=("total_precipitation", "sum"))
        .sort_values("full_date")
    )
    fig_temp = px.line(
        daily_state,
        x="full_date",
        y="avg_temperature",
        color="state",
        markers=True,
        color_discrete_sequence=CHART_PALETTE,
        title="Temperatura media por estado",
        labels={"full_date": "Data", "avg_temperature": "Temperatura media (C)", "state": "Estado"},
    )
    left.plotly_chart(plot_layout(fig_temp), use_container_width=True)

    latest_points = filtered[filtered["full_date"] == filtered["full_date"].max()]
    fig_map = px.scatter_mapbox(
        latest_points,
        lat="latitude",
        lon="longitude",
        color="risk_level",
        size="total_precipitation",
        hover_name="city",
        hover_data={
            "state": True,
            "avg_temperature": ":.1f",
            "total_precipitation": ":.1f",
            "latitude": False,
            "longitude": False,
        },
        zoom=3,
        height=430,
        title="Mapa da ultima leitura",
        color_discrete_map=RISK_LEVEL_COLORS,
    )
    fig_map.update_layout(mapbox_style="carto-positron")
    right.plotly_chart(plot_layout(fig_map), use_container_width=True)

    trend_source = filtered.copy().sort_values(["city", "full_date"])
    trend_source["temperature_rolling_3d"] = trend_source.groupby("city")["avg_temperature"].transform(
        lambda series: series.rolling(3, min_periods=1).mean()
    )
    latest_temperature = (
        trend_source[trend_source["full_date"] == trend_source["full_date"].max()]
        .groupby(["city", "state"], as_index=False)
        .agg(avg_temperature=("avg_temperature", "mean"), max_temperature=("max_temperature", "max"))
        .sort_values("avg_temperature", ascending=False)
    )
    highlighted_cities = latest_temperature.head(6)["city"].tolist()
    trend_highlight = trend_source[trend_source["city"].isin(highlighted_cities)]

    st.subheader("Tendencia termica por cidade")
    st.caption("Linhas mostram media movel de 3 dias; o ranking destaca a temperatura media mais recente.")

    trend_col, rank_col = st.columns([1.55, 0.9])
    fig_trend = px.line(
        trend_highlight,
        x="full_date",
        y="temperature_rolling_3d",
        color="city",
        markers=True,
        color_discrete_sequence=CHART_PALETTE,
        title="Evolucao da temperatura media",
        labels={"full_date": "Data", "temperature_rolling_3d": "Temperatura media 3d (C)", "city": "Cidade"},
    )
    fig_trend.update_traces(line={"width": 3}, marker={"size": 7})
    fig_trend.update_layout(
        height=430,
        hovermode="x unified",
        legend={"orientation": "h", "y": -0.25, "x": 0},
        margin={"l": 10, "r": 10, "t": 55, "b": 80},
    )
    trend_col.plotly_chart(plot_layout(fig_trend), use_container_width=True)

    latest_temperature = latest_temperature.assign(
        city_label=latest_temperature["city"] + "/" + latest_temperature["state"]
    )
    fig_latest_temp = px.bar(
        latest_temperature.sort_values("avg_temperature"),
        x="avg_temperature",
        y="city_label",
        color="avg_temperature",
        text=latest_temperature["avg_temperature"].map(lambda value: f"{value:.1f} C"),
        orientation="h",
        color_continuous_scale=["#60a5fa", "#fde68a", "#fb923c", "#b91c1c"],
        title="Temperatura mais recente",
        labels={"avg_temperature": "Temperatura media (C)", "city_label": "Cidade"},
    )
    fig_latest_temp.update_traces(textposition="outside", cliponaxis=False)
    fig_latest_temp.update_layout(
        height=430,
        showlegend=False,
        coloraxis_showscale=False,
        margin={"l": 110, "r": 60, "t": 55, "b": 35},
        xaxis={"rangemode": "tozero"},
        yaxis={"categoryorder": "total ascending"},
    )
    rank_col.plotly_chart(plot_layout(fig_latest_temp), use_container_width=True)
with risk_tab:
    summary = risk_summary(filtered)
    left, right = st.columns([1.15, 1])

    top_risk = summary[summary["eventos_de_risco"] > 0].head(10)
    if top_risk.empty:
        left.info("Nenhum evento de risco alto encontrado para os filtros atuais.")
    else:
        top_risk = top_risk.assign(city_label=top_risk["city"] + "/" + top_risk["state"])
        fig_ranking = px.bar(
            top_risk,
            x="eventos_de_risco",
            y="city_label",
            color="state",
            text="eventos_de_risco",
            orientation="h",
            color_discrete_sequence=CHART_PALETTE,
            title="Cidades com eventos de risco alto",
            labels={"eventos_de_risco": "Eventos", "city_label": "Cidade", "state": "Estado"},
        )
        fig_ranking.update_traces(textposition="outside", cliponaxis=False)
        fig_ranking.update_layout(
            yaxis={"categoryorder": "total ascending"},
            xaxis={"dtick": 5, "rangemode": "tozero"},
            margin={"l": 110, "r": 45, "t": 55, "b": 25},
        )
        left.plotly_chart(plot_layout(fig_ranking), use_container_width=True)

    risk_counts = (
        filtered[["drought_risk", "heat_risk", "heavy_rain_risk"]]
        .eq("high")
        .sum()
        .rename(index={"drought_risk": "Seca", "heat_risk": "Calor", "heavy_rain_risk": "Chuva forte"})
        .reset_index()
    )
    risk_counts.columns = ["risk_type", "events"]
    risk_counts = risk_counts[risk_counts["events"] > 0]
    if risk_counts["events"].sum() > 0:
        total_risk_events = risk_counts["events"].sum()
        risk_counts = risk_counts.assign(
            percentage=(risk_counts["events"] / total_risk_events * 100).round(1),
            label=lambda frame: frame["events"].astype(int).astype(str)
            + " eventos ("
            + frame["percentage"].astype(str)
            + "%)",
        )
        fig_risk_bar = px.bar(
            risk_counts.sort_values("events"),
            x="events",
            y="risk_type",
            color="risk_type",
            text="label",
            orientation="h",
            title="Alertas altos por tipo",
            labels={"events": "Eventos", "risk_type": "Tipo de alerta"},
            color_discrete_map={"Seca": "#b91c1c", "Calor": "#ea580c", "Chuva forte": "#2563eb"},
        )
        fig_risk_bar.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Eventos: %{x}<extra></extra>",
        )
        fig_risk_bar.update_layout(
            showlegend=False,
            xaxis={"rangemode": "tozero", "dtick": 5},
            yaxis={"categoryorder": "total ascending"},
            margin={"l": 90, "r": 130, "t": 55, "b": 35},
        )
        right.plotly_chart(plot_layout(fig_risk_bar), use_container_width=True)
    else:
        right.info("Nenhum alerta alto encontrado para os filtros atuais.")

    st.dataframe(
        summary.rename(
            columns={
                "city": "Cidade",
                "state": "UF",
                "dias_monitorados": "Dias monitorados",
                "eventos_de_risco": "Eventos de risco",
                "maior_sequencia_seca": "Maior sequencia seca",
                "chuva_7d_max": "Max. chuva 7d",
                "temperatura_maxima": "Temp. maxima",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

with water_tab:
    rain_daily = (
        filtered.groupby(["full_date", "state"], as_index=False)
        .agg(total_precipitation=("total_precipitation", "sum"), evapotranspiration=("evapotranspiration", "sum"))
        .sort_values("full_date")
    )
    fig_water = go.Figure()
    for state in rain_daily["state"].unique():
        state_data = rain_daily[rain_daily["state"] == state]
        fig_water.add_trace(
            go.Bar(x=state_data["full_date"], y=state_data["total_precipitation"], name=f"Chuva {state}")
        )
        fig_water.add_trace(
            go.Scatter(
                x=state_data["full_date"],
                y=state_data["evapotranspiration"],
                mode="lines+markers",
                name=f"ET {state}",
            )
        )
    fig_water.update_layout(
        barmode="group",
        title="Chuva acumulada versus evapotranspiracao",
        xaxis_title="Data",
        yaxis_title="mm",
    )
    st.plotly_chart(plot_layout(fig_water), use_container_width=True)

    city_rain = (
        filtered.groupby(["city", "state"], as_index=False)
        .agg(
            chuva_total=("total_precipitation", "sum"),
            chuva_30d_max=("precipitation_accumulated_30d", "max"),
            dias_sem_chuva=("days_without_rain", "max"),
        )
        .sort_values("chuva_total", ascending=False)
    )
    fig_city_rain = px.bar(
        city_rain.head(15),
        x="city",
        y="chuva_total",
        color="state",
        color_discrete_sequence=CHART_PALETTE,
        title="Cidades com maior chuva acumulada",
        labels={"city": "Cidade", "chuva_total": "Chuva total (mm)", "state": "Estado"},
    )
    st.plotly_chart(plot_layout(fig_city_rain), use_container_width=True)

with agriculture_tab:
    if agriculture.empty:
        st.info("Dados agricolas ainda nao foram processados para Gold.")
    else:
        latest_agriculture_year = int(agriculture["year"].max())
        latest_agriculture = agriculture[agriculture["year"] == latest_agriculture_year].copy()
        latest_agriculture["state"] = latest_agriculture["territory_code"].astype(str).map(IBGE_STATE_CODE_TO_UF)
        latest_climate_risk = (
            filtered[filtered["full_date"] == filtered["full_date"].max()]
            .groupby("state", as_index=False)
            .agg(
                eventos_de_risco=("risk_events", "sum"),
                temperatura_media=("avg_temperature", "mean"),
                chuva_total=("total_precipitation", "sum"),
            )
        )
        agriculture_risk = latest_agriculture.merge(
            latest_climate_risk,
            on="state",
            how="left",
        )
        agriculture_risk["eventos_de_risco"] = agriculture_risk["eventos_de_risco"].fillna(0)
        agriculture_risk["temperatura_media"] = agriculture_risk["temperatura_media"].fillna(
            agriculture_risk["temperatura_media"].mean()
        )
        agriculture_risk["chuva_total"] = agriculture_risk["chuva_total"].fillna(0)
        agriculture_risk["bubble_size"] = agriculture_risk["eventos_de_risco"].clip(lower=1)
        state_exposure = (
            agriculture_risk.groupby(["state", "territory_name"], as_index=False)
            .agg(
                produced_quantity=("produced_quantity", "sum"),
                eventos_de_risco=("eventos_de_risco", "max"),
                temperatura_media=("temperatura_media", "mean"),
                chuva_total=("chuva_total", "mean"),
            )
            .dropna(subset=["state"])
        )
        production_max = state_exposure["produced_quantity"].max()
        temperature_min = state_exposure["temperatura_media"].min()
        temperature_range = state_exposure["temperatura_media"].max() - temperature_min
        risk_max = max(float(state_exposure["eventos_de_risco"].max()), 1)
        state_exposure["production_weight"] = state_exposure["produced_quantity"] / production_max
        state_exposure["temperature_weight"] = (
            (state_exposure["temperatura_media"] - temperature_min) / temperature_range if temperature_range else 0
        )
        state_exposure["risk_weight"] = state_exposure["eventos_de_risco"] / risk_max
        state_exposure["agroclimate_score"] = (
            100
            * (
                0.5 * state_exposure["production_weight"]
                + 0.3 * state_exposure["risk_weight"]
                + 0.2 * state_exposure["temperature_weight"]
            )
        ).round(1)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ano agricola", str(latest_agriculture_year))
        col2.metric("Culturas", f"{latest_agriculture['product_name'].nunique()}")
        col3.metric("Estados", f"{latest_agriculture['territory_name'].nunique()}")
        col4.metric("Producao total", f"{latest_agriculture['produced_quantity'].sum() / 1_000_000:.1f} mi t")

        left, right = st.columns([1.15, 1])
        production_by_product = (
            latest_agriculture.groupby("product_name", as_index=False)["produced_quantity"]
            .sum()
            .sort_values("produced_quantity", ascending=False)
        )
        fig_products = px.bar(
            production_by_product.head(12),
            x="product_name",
            y="produced_quantity",
            color="product_name",
            color_discrete_sequence=CHART_PALETTE,
            title="Producao agricola por cultura",
            labels={"product_name": "Cultura", "produced_quantity": "Quantidade produzida (t)"},
        )
        left.plotly_chart(plot_layout(fig_products), use_container_width=True)

        production_by_state = (
            latest_agriculture.groupby("territory_name", as_index=False)["produced_quantity"]
            .sum()
            .sort_values("produced_quantity", ascending=False)
        )
        fig_states = px.bar(
            production_by_state.head(12),
            x="produced_quantity",
            y="territory_name",
            orientation="h",
            color="produced_quantity",
            color_continuous_scale="Viridis",
            title="Estados com maior producao",
            labels={"territory_name": "UF", "produced_quantity": "Quantidade produzida (t)"},
        )
        fig_states.update_layout(yaxis={"categoryorder": "total ascending"})
        right.plotly_chart(plot_layout(fig_states), use_container_width=True)

        top_exposure = agriculture_risk.sort_values(["eventos_de_risco", "produced_quantity"], ascending=False).head(15)
        fig_exposure = px.scatter(
            top_exposure,
            x="produced_quantity",
            y="reported_yield_t_ha",
            size="bubble_size",
            color="product_name",
            hover_name="territory_name",
            hover_data={"eventos_de_risco": True, "bubble_size": False},
            color_discrete_sequence=CHART_PALETTE,
            title="Producao agricola e risco climatico atual",
            labels={
                "produced_quantity": "Quantidade produzida (t)",
                "reported_yield_t_ha": "Produtividade informada (t/ha)",
                "product_name": "Cultura",
            },
        )
        st.plotly_chart(plot_layout(fig_exposure), use_container_width=True)

        fig_score = px.bar(
            state_exposure.sort_values("agroclimate_score", ascending=False).head(12),
            x="agroclimate_score",
            y="territory_name",
            color="eventos_de_risco",
            orientation="h",
            color_continuous_scale="YlOrRd",
            title="Indice agroclimatico por UF",
            labels={
                "agroclimate_score": "Score",
                "territory_name": "UF",
                "eventos_de_risco": "Eventos de risco",
            },
        )
        fig_score.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(plot_layout(fig_score), use_container_width=True)

        agriculture_table = latest_agriculture[
            [
                "year",
                "territory_name",
                "product_name",
                "produced_quantity",
                "harvested_area",
                "reported_yield_t_ha",
                "calculated_yield_t_ha",
                "production_value",
            ]
        ].sort_values("produced_quantity", ascending=False)
        st.dataframe(
            agriculture_table.rename(
                columns={
                    "year": "Ano",
                    "territory_name": "UF",
                    "product_name": "Cultura",
                    "produced_quantity": "Producao",
                    "harvested_area": "Area colhida",
                    "reported_yield_t_ha": "Produtividade informada",
                    "calculated_yield_t_ha": "Produtividade calculada",
                    "production_value": "Valor da producao",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

with table_tab:
    display_columns = [
        "full_date",
        "city",
        "state",
        "region",
        "avg_temperature",
        "max_temperature",
        "total_precipitation",
        "avg_humidity",
        "days_without_rain",
        "drought_risk",
        "heat_risk",
        "heavy_rain_risk",
    ]
    table = filtered[display_columns].sort_values(["full_date", "state", "city"], ascending=[False, True, True])
    table = table.rename(
        columns={
            "full_date": "Data",
            "city": "Cidade",
            "state": "UF",
            "region": "Regiao",
            "avg_temperature": "Temp. media",
            "max_temperature": "Temp. maxima",
            "total_precipitation": "Chuva total",
            "avg_humidity": "Umidade media",
            "days_without_rain": "Dias sem chuva",
            "drought_risk": "Risco seca",
            "heat_risk": "Risco calor",
            "heavy_rain_risk": "Risco chuva forte",
        }
    )
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button(
        "Baixar CSV filtrado",
        table.to_csv(index=False).encode("utf-8"),
        file_name="agroclimate_filtered.csv",
        mime="text/csv",
    )
