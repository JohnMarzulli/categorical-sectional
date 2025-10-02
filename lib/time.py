from datetime import datetime, timedelta, timezone


def now_utc() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=timezone.utc)


def get_utc_datetime(datetime_string: str) -> datetime:
    """
    Parses the RFC format datetime into something we can use.

    Arguments:
        datetime_string {string} -- The RFC encoded datetime string.

    Returns:
        datetime -- The parsed date time.
    """

    dt = datetime.fromisoformat(datetime_string.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
