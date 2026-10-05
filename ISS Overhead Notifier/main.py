"""Email alerts when the ISS is close to VIT Vellore during nighttime."""

from __future__ import annotations

import os
import smtplib
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Any

import requests

ISS_API_URL = "http://api.open-notify.org/iss-now.json"
SUN_API_URL = "https://api.sunrise-sunset.org/json"

LOCATION_NAME = "VIT Vellore"
LATITUDE = 12.934968
LONGITUDE = 79.146881
NEARBY_DEGREES = 5.0
CHECK_INTERVAL_SECONDS = 60
ALERT_COOLDOWN_SECONDS = 60 * 60
REQUEST_TIMEOUT_SECONDS = 15


def get_iss_location() -> tuple[float, float]:
    """Return the ISS latitude and longitude from Open Notify."""
    response = requests.get(ISS_API_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    if data.get("message") != "success":
        raise RuntimeError(f"ISS API returned an unsuccessful response: {data}")

    position = data.get("iss_position")
    if not isinstance(position, dict):
        raise RuntimeError("ISS API response did not contain a position.")

    try:
        return float(position["latitude"]), float(position["longitude"])
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("ISS API returned an invalid position.") from error


def get_sun_times() -> tuple[datetime, datetime]:
    """Return today's sunrise and sunset as timezone-aware UTC datetimes."""
    response = requests.get(
        SUN_API_URL,
        params={"lat": LATITUDE, "lng": LONGITUDE, "formatted": 0},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    data: dict[str, Any] = response.json()

    if data.get("status") != "OK":
        raise RuntimeError(f"Sunrise-Sunset API returned an unsuccessful response: {data}")

    results = data.get("results")
    if not isinstance(results, dict):
        raise RuntimeError("Sunrise-Sunset API response did not contain results.")

    try:
        sunrise = datetime.fromisoformat(results["sunrise"].replace("Z", "+00:00"))
        sunset = datetime.fromisoformat(results["sunset"].replace("Z", "+00:00"))
    except (KeyError, AttributeError, TypeError, ValueError) as error:
        raise RuntimeError("Sunrise-Sunset API returned invalid times.") from error

    return sunrise, sunset


def is_nighttime(now: datetime, sunrise: datetime, sunset: datetime) -> bool:
    """Return whether ``now`` is before sunrise or after sunset."""
    now_utc = now.astimezone(timezone.utc)
    return now_utc < sunrise or now_utc > sunset


def is_iss_nearby(
    iss_latitude: float,
    iss_longitude: float,
    latitude: float = LATITUDE,
    longitude: float = LONGITUDE,
    tolerance: float = NEARBY_DEGREES,
) -> bool:
    """Use a simple coordinate window to determine whether the ISS is nearby."""
    return (
        abs(iss_latitude - latitude) <= tolerance
        and abs(iss_longitude - longitude) <= tolerance
    )


def send_email(iss_latitude: float, iss_longitude: float) -> None:
    """Send an alert to every configured recipient."""
    sender = os.environ.get("SMTP_EMAIL")
    password = os.environ.get("SMTP_PASSWORD")
    recipients_value = os.environ.get("ALERT_RECIPIENTS")
    if recipients_value:
        recipients = [
            address.strip()
            for address in recipients_value.replace(";", ",").split(",")
            if address.strip()
        ]
    else:
        recipient = os.environ.get("ALERT_RECIPIENT", sender)
        recipients = [recipient] if recipient else []

    if not sender or not password or not recipients:
        raise RuntimeError(
            "Set SMTP_EMAIL, SMTP_PASSWORD, and ALERT_RECIPIENTS environment variables."
        )

    message = EmailMessage()
    message["Subject"] = "The ISS may be visible above VIT Vellore!"
    message["From"] = sender
    message["To"] = ", ".join(recipients)
    message.set_content(
        f"The International Space Station is currently near {LOCATION_NAME}.\n\n"
        f"ISS coordinates: {iss_latitude:.3f}, {iss_longitude:.3f}\n"
        "Look up and enjoy the pass!"
    )

    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=REQUEST_TIMEOUT_SECONDS) as connection:
        connection.login(sender, password)
        connection.send_message(message)


def check_once(last_alert_at: float | None = None) -> float | None:
    """Check the conditions once and return the timestamp of a sent alert."""
    iss_latitude, iss_longitude = get_iss_location()
    sunrise, sunset = get_sun_times()
    now = datetime.now(timezone.utc)

    if not is_nighttime(now, sunrise, sunset):
        print("It is daytime; no alert needed.")
        return last_alert_at

    if not is_iss_nearby(iss_latitude, iss_longitude):
        print(f"ISS is at {iss_latitude:.2f}, {iss_longitude:.2f}; it is not nearby.")
        return last_alert_at

    current_timestamp = time.time()
    if (
        last_alert_at is not None
        and current_timestamp - last_alert_at < ALERT_COOLDOWN_SECONDS
    ):
        print("ISS is nearby, but the alert cooldown is active.")
        return last_alert_at

    send_email(iss_latitude, iss_longitude)
    print("ISS alert email sent.")
    return current_timestamp


def main() -> None:
    """Poll the APIs until the program is stopped."""
    print(f"Monitoring the ISS over {LOCATION_NAME}. Press Ctrl+C to stop.")
    last_alert_at = None
    while True:
        try:
            last_alert_at = check_once(last_alert_at)
        except (requests.RequestException, RuntimeError, ValueError) as error:
            print(f"Check failed: {error}")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()