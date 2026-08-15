# Data Dictionary

| Field | Type | Description | Unit | Origin | Layer | Nullable |
| --- | --- | --- | --- | --- | --- | --- |
| timestamp | string | Observation timestamp | timezone local | Open-Meteo | Bronze | no |
| city | string | Brazilian city | n/a | config | Bronze+ | no |
| state | string | Brazilian state code | n/a | config | Bronze+ | no |
| latitude | double | Location latitude | degrees | config/API | Bronze+ | no |
| longitude | double | Location longitude | degrees | config/API | Bronze+ | no |
| temperature_2m | double | Air temperature at 2m | Celsius | Open-Meteo | Bronze/Silver | yes |
| precipitation_mm | double | Hourly precipitation | mm | Open-Meteo | Bronze/Silver | yes |
| avg_temperature | numeric | Daily average temperature | Celsius | Gold | Warehouse | yes |
| total_precipitation | numeric | Daily precipitation total | mm | Gold | Warehouse | yes |
| drought_risk | text | Exploratory drought risk flag | category | rule-based | Gold/Warehouse | yes |

