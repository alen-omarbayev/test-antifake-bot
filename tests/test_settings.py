import pytest

from bot.config.settings import _parse_admin_ids


@pytest.mark.parametrize("raw", [None, "", " "])
def test_parse_admin_ids_empty(raw):
    assert _parse_admin_ids(raw) == frozenset()


def test_parse_admin_ids_comma_separated():
    assert _parse_admin_ids("1, 2,,3 ") == frozenset({1, 2, 3})


def test_parse_admin_ids_invalid():
    with pytest.raises(RuntimeError, match="ADMIN_IDS"):
        _parse_admin_ids("1,abc")
