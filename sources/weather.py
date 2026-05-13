import requests
from dataclasses import dataclass
from typing import Optional
import config


@dataclass
class HourlyForecast:
    time: str
    temp_c: float
    description: str


@dataclass
class WeatherReport:
    location: str
    temp_c: float
    feels_like_c: float
    description: str
    humidity: int
    wind_kph: float
    hourly: list[HourlyForecast]
    error: Optional[str] = None

    @property
    def temp_f(self) -> float:
        return self.temp_c * 9 / 5 + 32

    @property
    def feels_like_f(self) -> float:
        return self.feels_like_c * 9 / 5 + 32


def fetch() -> WeatherReport:
    location = config.WEATHER_LOCATION
    url = f"https://wttr.in/{requests.utils.quote(location)}?format=j1"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        return WeatherReport(
            location=location, temp_c=0, feels_like_c=0,
            description="Unavailable", humidity=0, wind_kph=0, hourly=[],
            error=str(exc),
        )

    current = data["current_condition"][0]
    desc = current["weatherDesc"][0]["value"]

    hourly_raw = data.get("weather", [{}])[0].get("hourly", [])
    hourly = [
        HourlyForecast(
            time=f"{int(h['time']) // 100:02d}:00",
            temp_c=float(h["tempC"]),
            description=h["weatherDesc"][0]["value"],
        )
        for h in hourly_raw
    ]

    return WeatherReport(
        location=data["nearest_area"][0]["areaName"][0]["value"],
        temp_c=float(current["temp_C"]),
        feels_like_c=float(current["FeelsLikeC"]),
        description=desc,
        humidity=int(current["humidity"]),
        wind_kph=float(current["windspeedKmph"]),
        hourly=hourly,
    )
