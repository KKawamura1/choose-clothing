#!/usr/bin/env python3
"""Daily clothing recommendation app based on forecast temperatures."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


CLOTHING_ITEMS = {
    "1": "肌着",
    "2": "綿の長袖",
    "3": "ポリエステルの長袖",
    "4": "薄いコート",
    "5": "分厚いコート",
    "6": "半袖の服",
}

DEFAULT_NTFY_SERVER = "https://ntfy.sh"

OUTFIT_LEVELS = [
    {
        "level": 1,
        "label": "暑い日",
        "items": ["1", "6"],
        "min_score": 27,
    },
    {
        "level": 2,
        "label": "少し暑い日",
        "items": ["1", "2"],
        "min_score": 21,
    },
    {
        "level": 3,
        "label": "ふつうの日",
        "items": ["1", "2", "3"],
        "min_score": 15,
    },
    {
        "level": 4,
        "label": "少し寒い日",
        "items": ["1", "2", "3", "4"],
        "min_score": 10,
    },
    {
        "level": 5,
        "label": "寒い日",
        "items": ["1", "2", "3", "5"],
        "min_score": -100,
    },
]


@dataclass(frozen=True)
class Forecast:
    max_temp: float
    min_temp: float


def temperature_score(max_temp: float, min_temp: float) -> float:
    """Weighted score that leans slightly toward daytime highs."""
    return max_temp * 0.6 + min_temp * 0.4


def choose_outfit(max_temp: float, min_temp: float) -> dict[str, object]:
    score = temperature_score(max_temp, min_temp)
    for outfit in OUTFIT_LEVELS:
        if score >= outfit["min_score"]:
            return {
                "level": outfit["level"],
                "label": outfit["label"],
                "items": outfit["items"],
                "item_names": [CLOTHING_ITEMS[item] for item in outfit["items"]],
                "score": round(score, 1),
                "max_temp": max_temp,
                "min_temp": min_temp,
            }
    raise RuntimeError("No outfit level matched")


def fetch_forecast(latitude: float, longitude: float) -> Forecast:
    params = urllib.parse.urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min",
            "forecast_days": 1,
            "timezone": "auto",
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{params}"
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "choose-clothing-app/1.0",
        },
    )

    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.load(response)
            break
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"Failed to fetch forecast: {last_error}")

    daily = payload["daily"]
    return Forecast(
        max_temp=float(daily["temperature_2m_max"][0]),
        min_temp=float(daily["temperature_2m_min"][0]),
    )


def format_recommendation(recommendation: dict[str, object]) -> str:
    items = " / ".join(recommendation["item_names"])
    return (
        f"{recommendation['label']}。"
        f"最高{recommendation['max_temp']}℃、最低{recommendation['min_temp']}℃。"
        f"おすすめ: {items}"
    )


def send_notification(title: str, message: str) -> None:
    if platform.system() != "Darwin":
        print("Notification is only supported on macOS in this version.", file=sys.stderr)
        return

    script = (
        'display notification "{}" with title "{}"'
        .format(message.replace('"', '\\"'), title.replace('"', '\\"'))
    )
    subprocess.run(["osascript", "-e", script], check=True)


def send_ntfy_notification(server: str, topic: str, title: str, message: str) -> None:
    normalized_server = server.strip() or DEFAULT_NTFY_SERVER
    url = f"{normalized_server.rstrip('/')}/{urllib.parse.quote(topic, safe='')}"
    request = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        headers={
            "Title": title,
            "Priority": "default",
            "Tags": "tshirt",
            "User-Agent": "choose-clothing-app/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10):
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Choose an outfit from max/min temperatures."
    )
    parser.add_argument("--max-temp", type=float, help="Daily maximum temperature")
    parser.add_argument("--min-temp", type=float, help="Daily minimum temperature")
    parser.add_argument("--latitude", type=float, help="Latitude for weather lookup")
    parser.add_argument("--longitude", type=float, help="Longitude for weather lookup")
    parser.add_argument(
        "--notify",
        action="store_true",
        help="Send a macOS notification with the recommendation",
    )
    parser.add_argument(
        "--ntfy-topic",
        help="Send a push notification to the ntfy topic",
    )
    parser.add_argument(
        "--ntfy-server",
        default=os.environ.get("NTFY_SERVER") or DEFAULT_NTFY_SERVER,
        help="ntfy server URL (default: https://ntfy.sh or non-empty $NTFY_SERVER)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.max_temp is not None and args.min_temp is not None:
        forecast = Forecast(max_temp=args.max_temp, min_temp=args.min_temp)
    elif args.latitude is not None and args.longitude is not None:
        try:
            forecast = fetch_forecast(args.latitude, args.longitude)
        except (urllib.error.URLError, KeyError, IndexError, ValueError) as exc:
            print(f"Failed to fetch forecast: {exc}", file=sys.stderr)
            return 1
    else:
        print(
            "Pass either --max-temp and --min-temp, or --latitude and --longitude.",
            file=sys.stderr,
        )
        return 1

    recommendation = choose_outfit(forecast.max_temp, forecast.min_temp)
    message = format_recommendation(recommendation)
    print(message)

    if args.notify:
        try:
            send_notification("今日の服装", message)
        except subprocess.CalledProcessError as exc:
            print(f"Failed to send notification: {exc}", file=sys.stderr)
            return 1

    ntfy_topic = args.ntfy_topic or os.environ.get("NTFY_TOPIC")
    if ntfy_topic:
        try:
            send_ntfy_notification(
                server=args.ntfy_server,
                topic=ntfy_topic,
                title="今日の服装",
                message=message,
            )
        except urllib.error.URLError as exc:
            print(f"Failed to send ntfy notification: {exc}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
