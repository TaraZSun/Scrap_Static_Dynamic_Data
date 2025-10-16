import pytest
import asyncio
import scrape_data.utils.accept_cookies as ac


@pytest.mark.asyncio
async def test_accept_cookies_clicks_first_selector(monkeypatch):
    clicked = {}

    class DummyLocator:
        def __init__(self): self.first = self
        async def click(self, timeout=None):
            clicked["sel"] = True

    class DummyPage:
        frames = []
        async def evaluate(self, script): return None
        def locator(self, sel): return DummyLocator()
        def get_by_role(self, *a, **kw): return DummyLocator()

    page = DummyPage()
    result = await ac.accept_cookies(page)
    assert result is True
    assert "sel" in clicked


@pytest.mark.asyncio
async def test_accept_cookies_tries_frames(monkeypatch):
    clicked = {}

    class DummyLocator:
        def __init__(self): self.first = self
        async def click(self, timeout=None):
            clicked["frame"] = True

    class DummyFrame:
        def locator(self, sel): return DummyLocator()

    class DummyPage:
        frames = [DummyFrame()]
        async def evaluate(self, script): return None
        def locator(self, sel): 
            raise Exception("simulate no element")
        def get_by_role(self, *a, **kw): return DummyLocator()

    page = DummyPage()
    result = await ac.accept_cookies(page)
    assert result is True
    assert "frame" in clicked


@pytest.mark.asyncio
async def test_accept_cookies_falls_back_to_get_by_role(monkeypatch):
    clicked = {}

    class DummyLocator:
        def __init__(self): self.first = self
        async def click(self, timeout=None):
            clicked["role"] = True

    class DummyPage:
        frames = []
        async def evaluate(self, script): return None
        def locator(self, sel): 
            raise Exception("simulate no element")
        def get_by_role(self, *a, **kw): return DummyLocator()

    page = DummyPage()
    result = await ac.accept_cookies(page)
    assert result is True
    assert "role" in clicked


@pytest.mark.asyncio
async def test_accept_cookies_returns_false(monkeypatch):
    class DummyLocator:
        def __init__(self): self.first = self
        async def click(self, timeout=None): raise Exception("no click")

    class DummyPage:
        frames = []
        async def evaluate(self, script): return None
        def locator(self, sel): raise Exception("no element")
        def get_by_role(self, *a, **kw): raise Exception("no button")

    page = DummyPage()
    result = await ac.accept_cookies(page)
    assert result is False
