import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Location:
    city: str
    state: str
    latitude: float
    longitude: float
    region: str


def load_locations(path: Path | None = None) -> list[Location]:
    location_path = path or Path(__file__).resolve().parents[1] / "config" / "locations.csv"
    with location_path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        return [
            Location(
                city=row["city"],
                state=row["state"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                region=row["region"],
            )
            for row in reader
        ]
