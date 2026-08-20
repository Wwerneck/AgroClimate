from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config.settings import get_settings  # noqa: E402

WIDTH = 1600
HEIGHT = 900
BG = "#f8fafc"
INK = "#0f172a"
MUTED = "#64748b"
GREEN = "#16a34a"
BLUE = "#2563eb"
ORANGE = "#ea580c"
RED = "#b91c1c"
GRID = "#dbe4ef"
CARD = "#ffffff"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_header(draw: ImageDraw.ImageDraw, title: str, subtitle: str) -> None:
    draw.rectangle((0, 0, WIDTH, HEIGHT), fill=BG)
    draw.rectangle((90, 70, 98, 154), fill=GREEN)
    draw.text((120, 62), title, fill=INK, font=font(54, bold=True))
    draw.text((122, 138), subtitle, fill=MUTED, font=font(25))


def draw_card(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], title: str, value: str, accent: str) -> None:
    draw.rounded_rectangle(xy, radius=18, fill=CARD, outline="#dbe4ef", width=2)
    x1, y1, _, _ = xy
    draw.text((x1 + 28, y1 + 24), title, fill=MUTED, font=font(24))
    draw.text((x1 + 28, y1 + 70), value, fill=INK, font=font(44, bold=True))
    draw.rectangle((x1, y1, x1 + 8, y1 + 140), fill=accent)


def draw_line_chart(draw: ImageDraw.ImageDraw, frame: pd.DataFrame, xy: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill=CARD, outline="#dbe4ef", width=2)
    draw.text((x1 + 30, y1 + 24), "Tendencia termica das cidades mais quentes", fill=INK, font=font(30, bold=True))
    plot = (x1 + 75, y1 + 95, x2 - 220, y2 - 70)
    px1, py1, px2, py2 = plot
    for i in range(5):
        y = py1 + i * (py2 - py1) / 4
        draw.line((px1, y, px2, y), fill=GRID, width=1)
    latest = frame[frame["event_date"] == frame["event_date"].max()]
    cities = latest.sort_values("avg_temperature", ascending=False)["city"].head(5).tolist()
    dates = sorted(frame["event_date"].unique())
    min_temp = frame["avg_temperature"].min() - 1
    max_temp = frame["avg_temperature"].max() + 1
    palette = [RED, ORANGE, GREEN, BLUE, "#7c3aed"]
    for idx, city in enumerate(cities):
        series = frame[frame["city"] == city].sort_values("event_date")
        points = []
        for _, row in series.iterrows():
            x = px1 + dates.index(row["event_date"]) * (px2 - px1) / max(len(dates) - 1, 1)
            y = py2 - (row["avg_temperature"] - min_temp) * (py2 - py1) / (max_temp - min_temp)
            points.append((x, y))
        if len(points) > 1:
            draw.line(points, fill=palette[idx], width=5, joint="curve")
        for point in points[-1:]:
            draw.ellipse((point[0] - 7, point[1] - 7, point[0] + 7, point[1] + 7), fill=palette[idx])
        draw.text((px2 + 30, y1 + 100 + idx * 38), city, fill=palette[idx], font=font(22, bold=True))
    draw.text((px1, py2 + 22), pd.Timestamp(dates[0]).strftime("%d/%m"), fill=MUTED, font=font(20))
    draw.text((px2 - 55, py2 + 22), pd.Timestamp(dates[-1]).strftime("%d/%m"), fill=MUTED, font=font(20))


def draw_bar_chart(draw: ImageDraw.ImageDraw, data: pd.DataFrame, xy: tuple[int, int, int, int], title: str) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=18, fill=CARD, outline="#dbe4ef", width=2)
    draw.text((x1 + 30, y1 + 24), title, fill=INK, font=font(30, bold=True))
    max_value = max(float(data["value"].max()), 1)
    bar_x = x1 + 270
    bar_max = x2 - 110
    y = y1 + 92
    row_step = max(30, min(52, (y2 - y - 30) / max(len(data), 1)))
    bar_height = max(18, min(32, row_step - 12))
    for _, row in data.iterrows():
        width = (bar_max - bar_x) * float(row["value"]) / max_value
        color = row.get("color", GREEN)
        draw.text((x1 + 30, y + 8), str(row["label"])[:24], fill=INK, font=font(22))
        draw.rounded_rectangle((bar_x, y, bar_x + width, y + bar_height), radius=8, fill=color)
        draw.text((bar_x + width + 14, y + 2), row["display"], fill=MUTED, font=font(21))
        y += row_step


def save_overview(weather: pd.DataFrame, agriculture: pd.DataFrame, out: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    latest_date = pd.to_datetime(weather["event_date"].max()).strftime("%d/%m/%Y")
    draw_header(draw, "AgroClimate", "Data platform for weather risk and Brazilian agriculture analytics")
    cards = [
        ("Latest weather", latest_date, GREEN),
        ("Gold weather rows", f"{len(weather):,}".replace(",", "."), BLUE),
        ("Agriculture facts", f"{len(agriculture):,}".replace(",", "."), ORANGE),
        ("Crops tracked", str(agriculture["product_name"].nunique()), RED),
    ]
    for i, item in enumerate(cards):
        draw_card(draw, (90 + i * 365, 215, 420 + i * 365, 355), *item)
    draw_line_chart(draw, weather, (90, 410, 1510, 820))
    image.save(out)


def save_climate_card(weather: pd.DataFrame, out: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw_header(draw, "Climate monitoring", "Daily temperature, rain and risk indicators for key agricultural cities")
    draw_line_chart(draw, weather, (90, 210, 1510, 585))
    latest = weather[weather["event_date"] == weather["event_date"].max()].copy()
    latest["value"] = latest["avg_temperature"]
    latest["label"] = latest["city"] + "/" + latest["state"]
    latest["display"] = latest["avg_temperature"].map(lambda value: f"{value:.1f} C")
    latest["color"] = latest["avg_temperature"].map(_temperature_color)
    draw_bar_chart(
        draw,
        latest.sort_values("value", ascending=False).head(4),
        (90, 625, 1510, 850),
        "Latest temperature ranking",
    )
    image.save(out)


def save_agriculture_card(weather: pd.DataFrame, agriculture: pd.DataFrame, out: Path) -> None:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)
    draw_header(draw, "Agriculture exposure", "IBGE PAM production summaries connected to current climate risk")
    production = agriculture.groupby("product_name", as_index=False)["produced_quantity"].sum()
    production["value"] = production["produced_quantity"]
    production["label"] = production["product_name"]
    production["display"] = production["produced_quantity"].map(lambda value: f"{value / 1_000_000:.1f}M t")
    production["color"] = [GREEN, ORANGE, BLUE][: len(production)]
    draw_bar_chart(draw, production.sort_values("value", ascending=False), (90, 210, 760, 500), "Production by crop")

    latest_risk = weather[weather["event_date"] == weather["event_date"].max()]
    risk_columns = ["drought_risk", "heat_risk", "heavy_rain_risk"]
    latest_risk = latest_risk.assign(risk_events=latest_risk[risk_columns].eq("high").sum(axis=1))
    risk_by_state = latest_risk.groupby("state", as_index=False)["risk_events"].sum()
    production_state = (
        agriculture.groupby("territory_name", as_index=False)["produced_quantity"]
        .sum()
        .nlargest(8, "produced_quantity")
    )
    production_state["value"] = production_state["produced_quantity"]
    production_state["label"] = production_state["territory_name"]
    production_state["display"] = production_state["produced_quantity"].map(lambda value: f"{value / 1_000_000:.1f}M t")
    production_state["color"] = GREEN
    draw_bar_chart(draw, production_state, (820, 210, 1510, 720), "Top producing states")
    total_risk = int(risk_by_state["risk_events"].sum())
    draw.text((100, 575), "Current high-risk events", fill=MUTED, font=font(28))
    draw.text((100, 620), str(total_risk), fill=RED, font=font(92, bold=True))
    draw.text(
        (100, 725),
        "Risk events are calculated from heat, drought and heavy rain indicators.",
        fill=MUTED,
        font=font(25),
    )
    image.save(out)


def _temperature_color(value: float) -> str:
    if value >= 28:
        return RED
    if value >= 24:
        return ORANGE
    return BLUE


def main() -> None:
    settings = get_settings()
    out = PROJECT_ROOT / "docs" / "screenshots"
    out.mkdir(parents=True, exist_ok=True)
    weather = pd.read_parquet(settings.gold_dir / "weather_daily")
    agriculture = pd.read_parquet(settings.gold_dir / "agriculture_summary")
    save_overview(weather, agriculture, out / "linkedin-01-overview.png")
    save_climate_card(weather, out / "linkedin-02-climate-monitoring.png")
    save_agriculture_card(weather, agriculture, out / "linkedin-03-agriculture-exposure.png")


if __name__ == "__main__":
    main()
