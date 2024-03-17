import datetime
import hashlib
import json
import time
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageFont


class WeatherApi:
    API_HOST = "https://devapi.qweather.com"

    def __init__(
        self,
        key: str,
        publicid: str | int,
        locationid: str | int = "101010200",
        coordinates: str | tuple[int] = "",
    ):
        self.key: str = key
        self.publicid: str = str(publicid)
        self.locationid: str = str(locationid)
        self.coordinates: str = (f"{coordinates[0]},{coordinates[1]}"
                                 if isinstance(coordinates, tuple) else coordinates)

    def _get_data(self, path: str, data: dict[str, str]) -> dict[str, Any]:
        data = {
            **data,
            "publicid": self.publicid,
            "t": int(time.time()),
        }
        if data.get("sign"):
            del data["sign"]

        query = "&".join([f"{k}={v}" for k, v in sorted(data.items())])
        data["sign"] = hashlib.md5((query + self.key).encode("utf-8")).hexdigest()

        response = requests.get(f"{self.API_HOST}{path}", params=data)
        if response.status_code != 200:
            return {}
        else:
            return response.json()

    def _get_location(self, location: str) -> str:
        if not location:
            if self.coordinates:
                location = self.coordinates
            else:
                location = self.locationid
        return location

    def _get_grid_data(self, location: str, slug: str, key: str):
        location = self._get_location(location)
        return self._get_data(f"/v7/grid-weather/{slug}" if "," in location else f"/v7/weather/{slug}", {
            "location": location,
        }).get(key)

    def get_current_weather(self, location: str = "") -> dict[str, str]:
        return self._get_grid_data(location, "now", "now")

    def get_hourly_forecast(self, location: str = "") -> list[dict[str, str]]:
        return self._get_grid_data(location, "24h", "hourly")

    def get_daily_forecast(self, location: str = "") -> list[dict[str, str]]:
        return self._get_grid_data(location, "7d", "daily")

    def get_warning(self, location: str = "") -> list[dict[str, str]]:
        return self._get_data("/v7/warning/now", {
            "location": self._get_location(location),
        }).get("warning")

    def get_air_quality(self, location: str = "") -> list[dict[str, str]]:
        return self._get_data("/v7/air/now", {
            "location": self._get_location(location),
        }).get("now")

    def get_precipitation(self, location: str = "") -> list[dict[str, Any]]:
        return self._get_data("/v7/minutely/5m", {
            "location": self._get_location(location),
        })


class WeatherDraw:
    FONT_WEATHER_18 = ImageFont.truetype(r"external/qweather-icons/font/fonts/qweather-icons.ttf", 18)
    FONT_WEATHER_36 = ImageFont.truetype(r"external/qweather-icons/font/fonts/qweather-icons.ttf", 36)
    TIMEZONE = datetime.datetime.now().tzinfo

    def __init__(
            self,
            font_12: ImageFont.FreeTypeFont,
            font_18: ImageFont.FreeTypeFont,
            text_color: str | tuple[int, int, int] = (255, 255, 255),
            basic_image: Image.Image = None,
    ) -> None:
        self.font_12 = font_12
        self.font_18 = font_18
        if isinstance(text_color, str):
            self.text_color = tuple(map(int, text_color.split(",")))
        else:
            self.text_color = text_color

        with open("external/qweather-icons/font/qweather-icons.json", "r", -1, "utf8") as reader:
            self.weather_icons = json.load(reader)

        if basic_image != None:
            self.basic_image = basic_image
        else:
            self.basic_image = Image.new("RGB", (200, 80), (0, 0, 0))

    def get_current_weather(self, current_weather: dict[str, str]) -> Image.Image:
        image = self.basic_image.copy()
        draw = ImageDraw.Draw(image)

        draw.text(
            (100, 10),
            "实时天气",
            self.text_color,
            self.font_18,
            "mm",
        )

        draw.text(
            (40, 50),
            chr(self.weather_icons[current_weather["icon"]]),
            self.text_color,
            self.FONT_WEATHER_36,
            "mm",
        )
        draw.text(
            (120, 30),
            f'{current_weather["text"]} {current_weather["temp"]}℃',
            self.text_color,
            self.font_12,
            "mm",
        )
        draw.text(
            (120, 50),
            f'{current_weather["windDir"]}{current_weather["windScale"]}级',
            self.text_color,
            self.font_12,
            "mm",
        )
        draw.text(
            (120, 70),
            f'湿度 {current_weather["humidity"]}%',
            self.text_color,
            self.font_12,
            "mm",
        )

        return image

    def get_hourly_forecast(self, hourly_forecast: list[dict[str, str]]) -> Image.Image:
        image = self.basic_image.copy()
        draw = ImageDraw.Draw(image)

        draw.text(
            (100, 10),
            "小时预报",
            self.text_color,
            self.font_18,
            "mm",
        )
        now = datetime.datetime.now().astimezone(self.TIMEZONE)
        i = 0
        for item in hourly_forecast:
            time = datetime.datetime.fromisoformat(item["fxTime"]).astimezone(self.TIMEZONE)
            if time < now:
                continue
            draw.text(
                (50 * i + 25, 30),
                time.strftime("%H:%M"),
                self.text_color,
                self.font_12,
                "mm",
            )
            draw.text(
                (50 * i + 25, 50),
                chr(self.weather_icons[item["icon"]]),
                self.text_color,
                self.FONT_WEATHER_18,
                "mm",
            )
            draw.text(
                (50 * i + 25, 70),
                f'{item["temp"]}℃',
                self.text_color,
                self.font_12,
                "mm",
            )
            i += 1
            if i >= 4:
                break

        return image

    def get_daily_forecast(self, daily_forecast: list[dict[str, str]]) -> Image.Image:
        image = self.basic_image.copy()
        draw = ImageDraw.Draw(image)

        draw.text(
            (100, 10),
            "日间预报",
            self.text_color,
            self.font_18,
            "mm",
        )
        today = datetime.datetime.today().astimezone(self.TIMEZONE)
        i = 0
        for item in daily_forecast:
            date = datetime.datetime.strptime(item["fxDate"], "%Y-%m-%d").astimezone(self.TIMEZONE)
            if date < today:
                continue
            draw.text(
                (60 * i + 10 + 30, 30),
                date.strftime("%m-%d"),
                self.text_color,
                self.font_12,
                "mm",
            )
            draw.text(
                (60 * i + 10 + 15, 50),
                chr(self.weather_icons[item["iconDay"]]),
                self.text_color,
                self.FONT_WEATHER_18,
                "mm",
            )
            draw.text(
                (60 * i + 10 + 45, 50),
                chr(self.weather_icons[item["iconNight"]]),
                self.text_color,
                self.FONT_WEATHER_18,
                "mm",
            )
            draw.text(
                (60 * i + 10 + 30, 70),
                f'{item["tempMin"]}-{item["tempMax"]}℃',
                self.text_color,
                self.font_12,
                "mm",
            )
            i += 1
            if i >= 3:
                break

        return image

    def get_warning(self, warning: list[dict[str, str]]) -> Image.Image:
        image = self.basic_image.copy()
        draw = ImageDraw.Draw(image)

        draw.text(
            (100, 10),
            "预警信息",
            self.text_color,
            self.font_18,
            "mm",
        )
        if len(warning) == 0:
            draw.text(
                (100, 50),
                "暂无预警",
                self.text_color,
                self.font_12,
                "mm",
            )
            return image

        left = 10
        if len(warning) == 1:
            left = 70
        elif len(warning) == 2:
            left = 40
        for i, item in enumerate(warning[:3]):
            draw.text(
                (60 * i + left + 30, 30),
                chr(self.weather_icons[item["type"]]),
                self.text_color,
                self.FONT_WEATHER_18,
                "mm",
            )
            warning_type = item["typeName"]
            if item.get("level"):
                warning_detail = item["level"]
            else:
                text = item.get("text", item.get("title"))
                type_name_index = text.find(warning_type)
                warning_detail = text[type_name_index + len(warning_type):text.find("预警", type_name_index)]
            draw.text(
                (60 * i + left + 30, 50),
                warning_type,
                self.text_color,
                self.font_12,
                "mm",
            )
            draw.text(
                (60 * i + left + 30, 70),
                warning_detail,
                self.text_color,
                self.font_12,
                "mm",
            )

        return image

    def get_air_quality(self, air_quality: dict[str, str]) -> Image.Image:
        image = self.basic_image.copy()
        draw = ImageDraw.Draw(image)

        draw.text(
            (100, 10),
            "空气质量",
            self.text_color,
            self.font_18,
            "mm",
        )

        draw.text(
            (100, 30),
            f'AQI {air_quality["aqi"]} {air_quality["category"]}',
            self.text_color,
            self.font_12,
            "mm",
        )
        draw.text(
            (60, 50),
            "PM10",
            self.text_color,
            self.font_12,
            "mm",
        )
        draw.text(
            (140, 50),
            "PM2.5",
            self.text_color,
            self.font_12,
            "mm",
        )
        draw.text(
            (60, 70),
            f'{air_quality["pm10"]} μg/m³',
            self.text_color,
            self.font_12,
            "mm",
        )
        draw.text(
            (140, 70),
            f'{air_quality["pm2p5"]} μg/m³',
            self.text_color,
            self.font_12,
            "mm",
        )

        return image

    def get_precipitation(self, precipitation: dict[str, Any]) -> Image.Image:
        image = self.basic_image.copy()
        draw = ImageDraw.Draw(image)

        draw.text(
            (100, 10),
            "降水情报",
            self.text_color,
            self.font_18,
            "mm",
        )

        draw.text(
            (100, 30),
            precipitation["summary"],
            self.text_color,
            self.font_12,
            "mm",
        )
        now = datetime.datetime.now().astimezone(self.TIMEZONE)
        i = 0
        precipitation_iter = iter(precipitation["minutely"])
        for item in precipitation_iter:
            time = datetime.datetime.fromisoformat(item["fxTime"]).astimezone(self.TIMEZONE)
            if time < now:
                continue
            draw.text(
                (50 * i + 25, 50),
                time.strftime("%H:%M"),
                self.text_color,
                self.font_12,
                "mm",
            )
            draw.text(
                (50 * i + 25, 70),
                f'{float(item["precip"]) * 100:.0f}%',
                self.text_color,
                self.font_12,
                "mm",
            )
            i += 1
            if i >= 4:
                break
            next(precipitation_iter)
            next(precipitation_iter)
            next(precipitation_iter)

        return image
