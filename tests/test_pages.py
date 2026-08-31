from fastapi.testclient import TestClient


def test_index_renders_english_ltr_by_default(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert 'lang="en"' in response.text
    assert 'dir="ltr"' in response.text
    assert "Your training log" in response.text


def test_language_switch_sets_cookie_and_renders_rtl(client: TestClient) -> None:
    switch = client.get("/language/fa", follow_redirects=False)

    assert switch.status_code == 303
    assert switch.cookies.get("lang") == "fa"

    page = client.get("/")
    assert 'lang="fa"' in page.text
    assert 'dir="rtl"' in page.text


def test_unknown_language_code_falls_back_to_english(client: TestClient) -> None:
    client.get("/language/xx", follow_redirects=False)

    page = client.get("/")
    assert 'lang="en"' in page.text
