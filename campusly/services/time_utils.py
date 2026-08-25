from __future__ import annotations

import os
from datetime import date, datetime, time
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "America/Monterrey"


def get_app_timezone() -> ZoneInfo:
    timezone_name = os.getenv("CAMPUSLY_TIMEZONE", DEFAULT_TIMEZONE)
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def now_local() -> datetime:
    return datetime.now(get_app_timezone())


def today_local() -> date:
    return now_local().date()


def current_time_local() -> time:
    return now_local().time().replace(microsecond=0, tzinfo=None)


def cuatrimestre_for_date(value: date) -> int:
    month = value.month
    if month <= 4:
        return 1
    if month <= 8:
        return 2
    return 3


def current_academic_period() -> tuple[int, int]:
    current_date = today_local()
    return current_date.year, cuatrimestre_for_date(current_date)
