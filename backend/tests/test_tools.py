import pytest
import httpx
from app.config import get_settings
from app.tools.weather import get_weather
from app.tools.web_search import search_web


@pytest.mark.asyncio
async def test_web_search_missing_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "web_search_api_key", "")
    res = await search_web("Angular 22 release notes")
    assert res["success"] is False
    assert "not configured" in res["error"]


@pytest.mark.asyncio
async def test_web_search_success(monkeypatch):
    monkeypatch.setattr(get_settings(), "web_search_api_key", "mock-tavily-key")

    mock_response = httpx.Response(
        200,
        json={
            "results": [
                {
                    "title": "Angular 22 Features",
                    "url": "https://angular.dev/releases",
                    "content": "Angular 22 brings enhanced reactivity and compiler performance.",
                }
            ]
        },
        request=httpx.Request("POST", "https://api.tavily.com/search"),
    )

    async def mock_post(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post)

    res = await search_web("Angular 22 features")
    assert res["success"] is True
    assert len(res["results"]) == 1
    assert res["results"][0]["title"] == "Angular 22 Features"
    assert len(res["sources"]) == 1
    assert res["sources"][0]["url"] == "https://angular.dev/releases"


@pytest.mark.asyncio
async def test_web_search_timeout(monkeypatch):
    monkeypatch.setattr(get_settings(), "web_search_api_key", "mock-tavily-key")

    async def mock_post_timeout(*args, **kwargs):
        raise httpx.TimeoutException("Timeout connecting to Tavily")

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_post_timeout)

    res = await search_web("Angular 22 features")
    assert res["success"] is False
    assert "timed out" in res["error"]


@pytest.mark.asyncio
async def test_weather_missing_key(monkeypatch):
    monkeypatch.setattr(get_settings(), "weather_api_key", "")
    res = await get_weather("Dehradun")
    assert res["success"] is False
    assert "not configured" in res["error"]


@pytest.mark.asyncio
async def test_weather_success(monkeypatch):
    monkeypatch.setattr(get_settings(), "weather_api_key", "mock-weather-key")

    mock_response = httpx.Response(
        200,
        json={
            "name": "Dehradun",
            "sys": {"country": "IN"},
            "weather": [{"main": "Clear", "description": "clear sky"}],
            "main": {
                "temp": 22.5,
                "feels_like": 22.0,
                "humidity": 55,
                "pressure": 1014,
            },
            "wind": {"speed": 3.1},
            "dt": 1728730000,
        },
        request=httpx.Request("GET", "https://api.openweathermap.org/data/2.5/weather"),
    )

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    res = await get_weather("Dehradun")
    assert res["success"] is True
    assert res["location"] == "Dehradun"
    assert res["data"]["temperature"] == "22.5°C"
    assert res["data"]["condition"] == "Clear"


@pytest.mark.asyncio
async def test_weather_location_not_found(monkeypatch):
    monkeypatch.setattr(get_settings(), "weather_api_key", "mock-weather-key")

    mock_response = httpx.Response(
        404,
        json={"cod": "404", "message": "city not found"},
        request=httpx.Request("GET", "https://api.openweathermap.org/data/2.5/weather"),
    )

    async def mock_get(*args, **kwargs):
        return mock_response

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    res = await get_weather("NonExistentCityXYZ")
    assert res["success"] is False
    assert "not found" in res["error"]
