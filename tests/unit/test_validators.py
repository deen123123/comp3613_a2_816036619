from datetime import date

import pytest

from app.errors import ServiceError
from app.utilities.validators import (
    clean,
    parse_date,
    parse_float,
    parse_int,
    to_int_or_none,
)


def test_clean_trims_optional_text():
    assert clean("  Curepe  ") == "Curepe"
    assert clean(None) == ""


@pytest.mark.parametrize(
    ("value", "minimum", "maximum", "expected"),
    [("1", 1, 10, 1), ("10", 1, 10, 10), ("4", None, 5, 4)],
)
def test_parse_int_accepts_values_in_range(value, minimum, maximum, expected):
    assert parse_int(value, "Bedrooms", minimum, maximum) == expected


@pytest.mark.parametrize(
    ("value", "minimum", "maximum", "message"),
    [
        ("abc", 1, 10, "whole number"),
        ("0", 1, 10, "at least 1"),
        ("11", 1, 10, "at most 10"),
    ],
)
def test_parse_int_rejects_invalid_or_out_of_range_values(value, minimum, maximum, message):
    with pytest.raises(ServiceError, match=message):
        parse_int(value, "Bedrooms", minimum, maximum)


def test_parse_float_enforces_numeric_range():
    assert parse_float("1.25", "Distance", 0, 10) == 1.25
    with pytest.raises(ServiceError, match="at least 0"):
        parse_float("-0.1", "Distance", 0, 10)
    with pytest.raises(ServiceError, match="number"):
        parse_float("nearby", "Distance")


def test_parse_date_accepts_iso_format_and_rejects_other_formats():
    assert parse_date("2030-09-01", "Move-in date") == date(2030, 9, 1)
    with pytest.raises(ServiceError, match="YYYY-MM-DD"):
        parse_date("01/09/2030", "Move-in date")


def test_to_int_or_none_returns_none_for_blank_or_non_numeric_values():
    assert to_int_or_none("3") == 3
    assert to_int_or_none("") is None
    assert to_int_or_none("three") is None
