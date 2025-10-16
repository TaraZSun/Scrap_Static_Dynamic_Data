import pytest
import scrape_data.scrape_web_data as swd

@pytest.mark.asyncio
async def test_fetch_static_data_success(monkeypatch):
    class DummyResponse:
        status_code = 200
        content = b"<html><body><h1>Hello</h1></body></html>"
        def raise_for_status(self): return None

    def fake_get(url, headers, timeout):
        return DummyResponse()

    monkeypatch.setattr("scrape_data.scrape_web_data.requests.get", fake_get)

    html = await swd.fetch_static_data("http://fake-url")
    assert "<h1>Hello</h1>" in html


@pytest.mark.asyncio
async def test_fetch_static_data_failure(monkeypatch):
    def fake_get(url, headers, timeout):
        raise swd.requests.RequestException("network down")

    monkeypatch.setattr("scrape_data.scrape_web_data.requests.get", fake_get)

    # function will retry and eventually raise
    with pytest.raises(swd.requests.RequestException):
        await swd.fetch_static_data("http://fake-url")


@pytest.mark.asyncio
async def test_fetch_dynamic_table_content_success(monkeypatch):
    

    # Patch accept_cookies used in scrape_web_data
    async def fake_accept_cookies(page):
        return None
    monkeypatch.setattr("scrape_data.scrape_web_data.accept_cookies", fake_accept_cookies)

    class DummyLocator:
        async def inner_html(self):
            return "<tr><td>data</td></tr>"
        @property
        def first(self):
            return self

    class DummyPage:
        async def goto(self, *a, **kw): return None
        async def screenshot(self, *a, **kw): return None
        async def wait_for_selector(self, *a, **kw): return None
        def locator(self, *a, **kw): return DummyLocator()
        async def close(self): return None

    class DummyContext:
        async def add_init_script(self, *a, **kw): return None
        async def new_page(self): return DummyPage()
        async def close(self): return None

    class DummyBrowser:
        async def new_context(self, *a, **kw): return DummyContext()
        async def close(self): return None

    class DummyChromium:
        async def launch(self, *a, **kw): return DummyBrowser()

    class DummyPlaywright:
        chromium = DummyChromium()
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return None

    monkeypatch.setattr("scrape_data.scrape_web_data.async_playwright", lambda: DummyPlaywright())

    html = await swd.fetch_dynamic_table_content("http://fake-url")
    assert "<table>" in html
    assert "<td>data</td>" in html


def test_main_static(monkeypatch):
    async def fake_fetch_static(url=None): return "<html><table></table></html>"
    monkeypatch.setattr(swd, "fetch_static_data", fake_fetch_static)

    # Should not raise, just log
    swd.main("static")


def test_main_dynamic(monkeypatch):
    async def fake_fetch_dynamic(*a, **kw): return "<table><tr></tr></table>"
    monkeypatch.setattr(swd, "fetch_dynamic_table_content", fake_fetch_dynamic)

    swd.main("dynamic")
