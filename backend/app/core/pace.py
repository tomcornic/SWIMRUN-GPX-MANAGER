import re

MMSS_PATTERN = re.compile(r"^(\d{1,2}):([0-5]\d)$")


class InvalidPaceError(ValueError):
    pass


def parse_mmss(value: str) -> int:
    """Parse une allure « mm:ss » en secondes totales."""
    match = MMSS_PATTERN.match(value.strip())
    if not match:
        raise InvalidPaceError(f"Allure invalide : « {value} ». Format attendu : mm:ss.")
    minutes, seconds = match.groups()
    return int(minutes) * 60 + int(seconds)


def format_mmss(total_seconds: int) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"
