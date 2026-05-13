from datetime import datetime, timezone


def format_datetime(dt, fmt='%d %b %Y, %I:%M %p UTC'):
    if not dt:
        return '-'
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime(fmt)


def format_duration(minutes):
    try:
        minutes = int(minutes)
    except (TypeError, ValueError):
        return '0m'
    hours, mins = divmod(minutes, 60)
    return f'{hours}h {mins}m' if hours else f'{mins}m'


def truncate_text(text, max_length=120):
    if not text:
        return ''
    text = str(text).strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 3].rstrip() + '...'
