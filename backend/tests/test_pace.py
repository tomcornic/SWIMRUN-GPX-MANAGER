import pytest

from app.core.pace import InvalidPaceError, format_mmss, parse_mmss


def test_parse_mmss_basic():
    assert parse_mmss("5:00") == 300


def test_parse_mmss_two_digit_minutes():
    assert parse_mmss("12:34") == 754


def test_parse_mmss_strips_whitespace():
    assert parse_mmss(" 5:00 ") == 300


def test_parse_mmss_rejects_invalid_seconds():
    with pytest.raises(InvalidPaceError):
        parse_mmss("5:60")


def test_parse_mmss_rejects_garbage():
    with pytest.raises(InvalidPaceError):
        parse_mmss("cinq minutes")


def test_format_mmss_pads_seconds():
    assert format_mmss(300) == "5:00"
    assert format_mmss(65) == "1:05"


def test_format_mmss_roundtrip():
    for value in ["3:05", "12:00", "0:45"]:
        assert format_mmss(parse_mmss(value)) == value
