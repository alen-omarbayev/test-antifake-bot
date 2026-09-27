import pytest

from scripts.analytics_report import DEFAULT_DAYS, parse_args


def test_parse_args_default_days():
    assert parse_args([]).days == DEFAULT_DAYS


def test_parse_args_custom_days():
    assert parse_args(["--days", "30"]).days == 30


@pytest.mark.parametrize("value", ["0", "366", "abc"])
def test_parse_args_rejects_invalid_days(value):
    with pytest.raises(SystemExit):
        parse_args(["--days", value])
