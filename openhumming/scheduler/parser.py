import re
from dataclasses import dataclass


DAY_OF_WEEK_MAP = {
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "日": "0",
    "天": "0",
}


@dataclass(slots=True)
class ParsedSchedule:
    cron: str
    title: str
    prompt: str
    source: str


def parse_schedule_text(text: str) -> ParsedSchedule:
    normalized = " ".join(text.strip().split())

    parsed = _parse_daily(normalized)
    if parsed:
        return parsed

    parsed = _parse_weekly(normalized)
    if parsed:
        return parsed

    parsed = _parse_english_daily(normalized)
    if parsed:
        return parsed

    raise ValueError(f"Could not parse schedule text: {text}")


def _parse_daily(text: str) -> ParsedSchedule | None:
    pattern = re.compile(
        r"^每天(?:(早上|上午|中午|下午|晚上))?\s*(\d{1,2})"
        r"(?:\s*(?:[:：]\s*|点\s*)(\d{1,2})?)?\s*(?:分)?\s*(.+)$"
    )
    match = pattern.match(text)
    if not match:
        return None

    period, hour_text, minute_text, prompt = match.groups()
    hour = _normalize_hour(int(hour_text), period)
    minute = int(minute_text or 0)
    clean_prompt = prompt.strip()
    return ParsedSchedule(
        cron=f"{minute} {hour} * * *",
        title=_infer_title(clean_prompt),
        prompt=clean_prompt,
        source=text,
    )


def _parse_weekly(text: str) -> ParsedSchedule | None:
    pattern = re.compile(
        r"^每周([一二三四五六日天])\s*(?:(早上|上午|中午|下午|晚上))?\s*(\d{1,2})"
        r"(?:\s*(?:[:：]\s*|点\s*)(\d{1,2})?)?\s*(?:分)?\s*(.+)$"
    )
    match = pattern.match(text)
    if not match:
        return None

    weekday, period, hour_text, minute_text, prompt = match.groups()
    hour = _normalize_hour(int(hour_text), period)
    minute = int(minute_text or 0)
    clean_prompt = prompt.strip()
    return ParsedSchedule(
        cron=f"{minute} {hour} * * {DAY_OF_WEEK_MAP[weekday]}",
        title=_infer_title(clean_prompt),
        prompt=clean_prompt,
        source=text,
    )


def _parse_english_daily(text: str) -> ParsedSchedule | None:
    pattern = re.compile(r"^every day at (\d{1,2}):(\d{2})\s+(.+)$", re.IGNORECASE)
    match = pattern.match(text)
    if not match:
        return None

    hour_text, minute_text, prompt = match.groups()
    hour = int(hour_text)
    minute = int(minute_text)
    clean_prompt = prompt.strip()
    return ParsedSchedule(
        cron=f"{minute} {hour} * * *",
        title=_infer_title(clean_prompt),
        prompt=clean_prompt,
        source=text,
    )


def _normalize_hour(hour: int, period: str | None) -> int:
    if period in {"下午", "晚上"} and hour < 12:
        return hour + 12
    if period == "中午" and hour < 11:
        return hour + 12
    return hour


def _infer_title(prompt: str) -> str:
    stripped = prompt.strip("。.!? ")
    if not stripped:
        return "Scheduled task"
    if len(stripped) <= 24:
        return stripped
    return stripped[:24].rstrip() + "..."
