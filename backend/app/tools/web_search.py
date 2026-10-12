from typing import Any
import httpx
from app.config import get_settings


async def search_web(query: str, max_results: int = 5) -> dict[str, Any]:
    settings = get_settings()
    api_key = settings.web_search_api_key.strip()

    if not api_key:
        return {
            "success": False,
            "query": query,
            "error": "Web search provider API key is not configured. Please set WEB_SEARCH_API_KEY in the environment.",
            "results": [],
            "sources": [],
        }

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": False,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)

        if response.status_code == 401:
            return {
                "success": False,
                "query": query,
                "error": "Web search authentication failed. Invalid API key provided.",
                "results": [],
                "sources": [],
            }
        if response.status_code == 429:
            return {
                "success": False,
                "query": query,
                "error": "Web search rate limit exceeded. Please try again shortly.",
                "results": [],
                "sources": [],
            }
        response.raise_for_status()

        data = response.json()
        raw_results = data.get("results", [])

        formatted_results = []
        sources = []

        for item in raw_results:
            title = item.get("title", "").strip() or "Untitled Result"
            link = item.get("url", "").strip()
            content = item.get("content", "").strip()

            formatted_results.append({
                "title": title,
                "url": link,
                "content": content,
            })

            if link:
                sources.append({
                    "title": title,
                    "url": link,
                    "snippet": content[:200] if content else None,
                })

        return {
            "success": True,
            "query": query,
            "results": formatted_results,
            "sources": sources,
            "count": len(formatted_results),
            "error": None,
        }

    except httpx.TimeoutException:
        return {
            "success": False,
            "query": query,
            "error": "Web search provider request timed out.",
            "results": [],
            "sources": [],
        }
    except httpx.HTTPStatusError as exc:
        return {
            "success": False,
            "query": query,
            "error": f"Search provider HTTP error: {exc.response.status_code}",
            "results": [],
            "sources": [],
        }
    except Exception as exc:
        return {
            "success": False,
            "query": query,
            "error": f"Search request failed: {str(exc)}",
            "results": [],
            "sources": [],
        }
