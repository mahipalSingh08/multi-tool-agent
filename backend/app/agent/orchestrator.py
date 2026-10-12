import json
from typing import Any
from openai import AsyncOpenAI, APIError, AuthenticationError, RateLimitError
from app.config import get_settings
from app.models import AgentResponse, SourceItem, ToolExecution
from app.tools.calculator import calculate
from app.tools.weather import get_weather
from app.tools.web_search import search_web

SYSTEM_PROMPT = """You are a capable Multi-Tool AI Agent.
You have access to three specialized tools:
1. `web_search`: Search the live web for current events, fresh documentation, recent releases, and real-time facts.
2. `calculator`: Compute arithmetic expressions, percentages, powers, roots, and mathematical formulas safely and accurately.
3. `get_weather`: Query current real-time weather conditions, temperatures, humidity, and wind for cities.

Rules:
- For general knowledge, conceptual, reasoning, or conversational queries that do not require live information or computation, answer directly without calling tools.
- When live data, math, or weather is needed, choose and call the appropriate tool.
- You can call multiple tools if the query requires it (e.g. comparing weather between two cities).
- When tool results are returned, synthesize them into a concise, well-structured, natural-language explanation.
- Never invent weather statistics or live facts. Rely on tool outputs.
"""

TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live web for current information, documentation, news, or articles. Returns source titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to look up on the web.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate mathematical expressions including arithmetic (+, -, *, /), percentages (e.g. '15% of 2500'), powers (^ or **), and square roots (sqrt).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate, e.g. '(125 * 8) + 450', '15% of 2500', 'sqrt(2025)'.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Fetch current weather observations for a specific city or region, including temperature, conditions, humidity, and wind.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name and optional country code (e.g., 'Dehradun', 'Delhi,IN', 'Tokyo').",
                    },
                    "units": {
                        "type": "string",
                        "enum": ["metric", "imperial"],
                        "description": "Units of measurement: 'metric' for Celsius, 'imperial' for Fahrenheit.",
                    },
                },
                "required": ["location"],
            },
        },
    },
]


async def execute_tool(name: str, args: dict[str, Any]) -> tuple[dict[str, Any], ToolExecution, list[SourceItem]]:
    sources: list[SourceItem] = []

    if name == "calculator":
        expression = str(args.get("expression", ""))
        calc_result = calculate(expression)
        success = calc_result.get("success", False)

        if success:
            summary = f"Calculated: {expression} = {calc_result.get('result')}"
            status = "success"
        else:
            summary = f"Calculation failed for: {expression}"
            status = "error"

        execution = ToolExecution(
            name="calculator",
            status=status,
            summary=summary,
            detail=calc_result.get("error") if not success else str(calc_result.get("result")),
        )
        return calc_result, execution, sources

    elif name == "web_search":
        query = str(args.get("query", ""))
        search_result = await search_web(query)
        success = search_result.get("success", False)

        if success:
            count = len(search_result.get("results", []))
            summary = f"Searched web for '{query}' ({count} results found)"
            status = "success"
            for src in search_result.get("sources", []):
                sources.append(
                    SourceItem(
                        title=src.get("title", ""),
                        url=src.get("url", ""),
                        snippet=src.get("snippet"),
                    )
                )
        else:
            summary = f"Web search failed for: '{query}'"
            status = "error"

        execution = ToolExecution(
            name="web_search",
            status=status,
            summary=summary,
            detail=search_result.get("error") if not success else f"Retrieved {len(sources)} sources",
        )
        return search_result, execution, sources

    elif name == "get_weather":
        location = str(args.get("location", ""))
        units = str(args.get("units", "metric"))
        weather_result = await get_weather(location, units=units)
        success = weather_result.get("success", False)

        if success:
            data = weather_result.get("data", {})
            temp = data.get("temperature", "")
            cond = data.get("description", "")
            summary = f"Fetched weather for {data.get('city', location)}: {temp}, {cond}"
            status = "success"
        else:
            summary = f"Weather lookup failed for: {location}"
            status = "error"

        execution = ToolExecution(
            name="get_weather",
            status=status,
            summary=summary,
            detail=weather_result.get("error") if not success else None,
        )
        return weather_result, execution, sources

    else:
        err_msg = f"Unsupported tool '{name}' requested."
        execution = ToolExecution(
            name=name,
            status="error",
            summary=err_msg,
            detail=err_msg,
        )
        return {"error": err_msg}, execution, sources


async def run_agent(query: str, max_rounds: int = 5) -> AgentResponse:
    settings = get_settings()

    if not settings.is_openai_configured:
        return AgentResponse(
            query=query,
            answer="OpenAI API key is not configured. Please set OPENAI_API_KEY in backend/.env to enable the agent.",
            tools_used=[],
            sources=[],
            success=False,
            error="OpenAI API key is missing or not configured.",
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]

    tools_used: list[ToolExecution] = []
    seen_urls: set[str] = set()
    aggregated_sources: list[SourceItem] = []

    try:
        for _ in range(max_rounds):
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                tools=TOOLS_DEFINITIONS,
                tool_choice="auto",
            )

            choice = response.choices[0]
            message = choice.message

            if not message.tool_calls:
                answer = message.content or "No response generated."
                return AgentResponse(
                    query=query,
                    answer=answer,
                    tools_used=tools_used,
                    sources=aggregated_sources,
                    success=True,
                    error=None,
                )

            # Append the assistant's tool call message
            messages.append(message.model_dump())

            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                try:
                    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                except json.JSONDecodeError:
                    args = {}

                result_data, execution, new_sources = await execute_tool(tool_name, args)
                tools_used.append(execution)

                for src in new_sources:
                    if src.url not in seen_urls:
                        seen_urls.add(src.url)
                        aggregated_sources.append(src)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result_data),
                })

        # If loop reached max rounds without final answer, do a final synthesis call without tools
        final_response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=messages,
        )
        final_answer = final_response.choices[0].message.content or "Completed tool execution."

        return AgentResponse(
            query=query,
            answer=final_answer,
            tools_used=tools_used,
            sources=aggregated_sources,
            success=True,
            error=None,
        )

    except AuthenticationError:
        return AgentResponse(
            query=query,
            answer="OpenAI authentication failed. Please verify your OPENAI_API_KEY.",
            tools_used=tools_used,
            sources=aggregated_sources,
            success=False,
            error="Invalid OpenAI API key.",
        )
    except RateLimitError:
        return AgentResponse(
            query=query,
            answer="OpenAI rate limit or quota exceeded. Please check your account usage.",
            tools_used=tools_used,
            sources=aggregated_sources,
            success=False,
            error="OpenAI rate limit reached.",
        )
    except APIError as exc:
        return AgentResponse(
            query=query,
            answer=f"OpenAI service error occurred: {exc.message}",
            tools_used=tools_used,
            sources=aggregated_sources,
            success=False,
            error=exc.message,
        )
    except Exception as exc:
        return AgentResponse(
            query=query,
            answer="An unexpected error occurred while processing your request.",
            tools_used=tools_used,
            sources=aggregated_sources,
            success=False,
            error=str(exc),
        )
