import pytest

from app.config import Settings


@pytest.mark.parametrize(
    "url",
    ["postgres://u:p@host:5432/db", "postgresql://u:p@host:5432/db"],
)
def test_host_urls_get_psycopg_driver(url):
    assert Settings(database_url=url).database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_explicit_driver_is_unchanged():
    url = "postgresql+psycopg://u:p@host:5432/db"
    assert Settings(database_url=url).database_url == url
