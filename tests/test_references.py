import re

import pytest
from fastapi.testclient import TestClient

from app.references import CATALOG, by_slug, format_citation, get_many

_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def test_every_entry_is_well_formed() -> None:
    for ref in CATALOG:
        assert ref.slug and ref.slug == ref.slug.lower()
        assert ref.authors and ref.title and ref.source
        assert 1900 < ref.year <= 2027
        assert ref.link.startswith("https://")
        if ref.doi is not None:
            assert _DOI_RE.match(ref.doi), ref.doi


def test_slugs_are_unique() -> None:
    slugs = [ref.slug for ref in CATALOG]
    assert len(slugs) == len(set(slugs))


def test_get_many_preserves_order() -> None:
    picked = get_many(["brzycki-1993-1rm", "acsm-2009-progression"])
    assert [ref.slug for ref in picked] == [
        "brzycki-1993-1rm",
        "acsm-2009-progression",
    ]


def test_unknown_slug_raises() -> None:
    with pytest.raises(KeyError):
        by_slug("does-not-exist")
    with pytest.raises(KeyError):
        get_many(["acsm-2009-progression", "nope"])


def test_format_citation_includes_year_and_link() -> None:
    ref = by_slug("schoenfeld-2017-volume")
    citation = format_citation(ref)
    assert "(2017)" in citation
    assert "https://doi.org/10.1080/02640414.2016.1210197" in citation


def test_references_page_renders_english(client: TestClient) -> None:
    response = client.get("/references")

    assert response.status_code == 200
    assert "References &amp; attributions" in response.text
    assert "Progression models in resistance training" in response.text
    assert "Jeff Nippard" in response.text
    assert "10.1519/JSC.0000000000001049" in response.text


def test_references_page_renders_persian(client: TestClient) -> None:
    client.get("/language/fa", follow_redirects=False)
    response = client.get("/references")

    assert response.status_code == 200
    assert 'dir="rtl"' in response.text
    assert "منابع و اسناد" in response.text


def test_footer_links_to_references(client: TestClient) -> None:
    assert 'href="/references"' in client.get("/").text
