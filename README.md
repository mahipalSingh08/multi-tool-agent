<img width="1356" height="2021" alt="main" src="https://github.com/user-attachments/assets/0cee90d9-a2e1-476e-8e0d-12620ceb3a7c" />


# Multi-Tool AI Agent — Web Search, Calculator & Weather

A complete, production-grade Multi-Tool AI Agent built with an Angular frontend and a Python 3.12+ / FastAPI / OpenAI SDK backend.

The system accepts natural-language user queries, uses OpenAI tool calling to determine intent, executes selected tools server-side, feeds intermediate observations back to the LLM, and delivers synthesized, coherent answers with tool execution metadata.

---

## Architecture & Request Flow

All tool selection and orchestration logic resides exclusively in the FastAPI backend. The Angular application never contains routing rules for tools.

```
                    User Query (Natural Language)
                                 │
                                 ▼
                     ┌───────────────────────┐
                     │   Angular Frontend    │
                     │  (Standalone Signals) │
                     └───────────┬───────────┘
                                 │ POST /api/agent
                                 ▼
                     ┌───────────────────────┐
                     │    FastAPI Backend    │
                     │ (Orchestrator Engine) │
                     └───────────┬───────────┘
                                 │
                   OpenAI Tool Calling (Multi-turn)
                                 │
        ┌────────────────────────┼────────────────────────┐
        ▼                        ▼                        ▼
 ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
 │  Web Search  │         │  Calculator  │         │   Weather    │
 │ (Tavily API) │         │ (Safe AST)   │         │(OpenWeather) │
 └──────────────┘         └──────────────┘         └──────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                     Tool Result Observations
                                 ▼
                     ┌───────────────────────┐
                     │ OpenAI Synthesis Turn │
                     └───────────┬───────────┘
                                 │
                 Final Answer + Execution Metadata
                                 ▼
                     ┌───────────────────────┐
                     │   Angular Response    │
                     │  (UI Badges & Sources)│
                     └───────────────────────┘
```

### Key Architectural Principles
1. **Zero Client-Side Routing**: The client only collects the query and renders backend execution states.
2. **Model-Driven Tool Selection**: The model determines whether to answer directly, perform web search, execute math calculations, or fetch live weather based on query semantics.
3. **Multi-Tool Orchestration**: Handles queries that require multiple tools (e.g. comparing temperatures in multiple cities) in a single run.
4. **Safety & Sandboxing**: Math evaluation is implemented using Python's `ast` parser with strict node whitelisting. Python `eval()` is never used.
5. **Resilient Error Handling**: External service failures (network timeouts, rate limits, missing API keys) are caught and returned safely without leaking stack traces or credentials.

---

## Technology Stack

### Frontend
- **Framework**: Angular (Standalone Components, Signals)
- **Language**: TypeScript
- **HTTP**: Angular `HttpClient` with `provideHttpClient(withFetch())`
- **Styling**: Vanilla CSS (Responsive Dark Theme, flexbox/grid layout)

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **LLM SDK**: Official OpenAI Python SDK (`AsyncOpenAI`)
- **Validation**: Pydantic v2 & Pydantic Settings
- **HTTP Client**: `httpx` (async requests with timeouts)
- **Testing**: `pytest`, `pytest-asyncio`

---

## Supported Tools

| Tool | Provider / Engine | Purpose | Example Query |
|---|---|---|---|
| **Web Search** | Tavily Search API | Retrieve current events, news, and technical documentation with source URLs. | *Find recent Angular 22 news* |
| **Calculator** | Safe AST Evaluator | Perform arithmetic, percentages, powers, square roots, and parentheses. | *Calculate 15% of 2,500* |
| **Weather** | OpenWeatherMap API | Fetch live temperature, atmospheric conditions, humidity, and wind. | *What's the weather in Dehradun?* |
| **Direct AI** | OpenAI LLM | Answer conceptual, explanatory, or general reasoning questions without tools. | *Explain what an AI agent is* |

---

## Project Structure

```text
multi-tool-agent/
├── frontend/                     # Angular frontend application
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/
│   │   │   │   ├── models/       # TypeScript interfaces (Agent, ToolExecution, Source)
│   │   │   │   └── services/     # AgentService (HttpClient integration)
│   │   │   ├── features/
│   │   │   │   └── agent/        # Agent UI component (HTML, CSS, TS)
│   │   │   ├── app.config.ts     # Application config & providers
│   │   │   └── app.routes.ts     # Route definitions
│   │   ├── environments/         # API base URL configuration
│   │   ├── index.html            # HTML entry point with meta tags
│   │   └── styles.css            # Global CSS resets
│   ├── angular.json
│   └── package.json
├── backend/                      # Python FastAPI application
│   ├── app/
│   │   ├── main.py               # FastAPI entry point & CORS configuration
│   │   ├── config.py             # Pydantic Settings & environment variables
│   │   ├── models.py             # Pydantic schemas for requests & responses
│   │   ├── api/
│   │   │   └── routes.py         # /api/health and /api/agent endpoints
│   │   ├── agent/
│   │   │   └── orchestrator.py   # OpenAI tool calling loop & execution coordinator
│   │   └── tools/
│   │       ├── calculator.py     # Safe AST mathematical expression evaluator
│   │       ├── web_search.py     # Tavily Web Search API client
│   │       └── weather.py        # OpenWeatherMap API client
│   ├── tests/                    # Comprehensive unit & integration test suite
│   │   ├── test_calculator.py
│   │   ├── test_tools.py
│   │   ├── test_orchestrator.py
│   │   └── test_api.py
│   ├── requirements.txt
│   └── .env.example
├── .gitignore
├── .env.example
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Node.js (v20+ or v24+) & npm
- Python 3.12 or 3.13

---

### How to Obtain API Keys

#### 1. OpenAI API Key (`OPENAI_API_KEY`)
- **Portal**: [https://platform.openai.com](https://platform.openai.com)
- **Steps**:
  1. Sign in or create an account at [platform.openai.com](https://platform.openai.com).
  2. Go to **Dashboard** → **API keys** (or [platform.openai.com/api-keys](https://platform.openai.com/api-keys)).
  3. Click **Create new secret key**, give it a name, and copy the key (starts with `sk-...`).
  4. Ensure your account has active credit or quota.

#### 2. Web Search API Key (`WEB_SEARCH_API_KEY`)
The backend uses **Tavily Search API**, optimized specifically for AI agent tool calling.
- **Portal**: [https://tavily.com](https://tavily.com)
- **Pricing**: **Free tier** provides **1,000 searches/month** with no credit card required.
- **Steps**:
  1. Visit [https://app.tavily.com/sign-up](https://app.tavily.com/sign-up) and register (supports Google/GitHub 1-click signup).
  2. Once inside your dashboard, locate the **API Key** section on the overview page.
  3. Copy your key (starts with `tvly-...`).

#### 3. Weather API Key (`WEATHER_API_KEY`)
The backend uses **OpenWeatherMap** current weather API.
- **Portal**: [https://openweathermap.org](https://openweathermap.org)
- **Pricing**: **Free tier** includes **1,000 calls/day** and 60 calls/minute.
- **Steps**:
  1. Sign up at [https://home.openweathermap.org/users/sign_up](https://home.openweathermap.org/users/sign_up).
  2. Verify your email address.
  3. Navigate to **API keys** in your account dashboard.
  4. Copy your default API key (or generate a new named key).
  *(Note: New OpenWeather keys typically become active within 10–15 minutes after registration).*

---

### Backend Setup

1. Navigate to `backend/`:
```bash
cd backend
```

2. Create and activate a Python virtual environment:
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create configuration file:
```bash
copy .env.example .env     # Windows
cp .env.example .env       # macOS / Linux
```

5. Configure credentials in `backend/.env`:
```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
WEB_SEARCH_API_KEY=tvly-...
WEATHER_API_KEY=your_openweathermap_key
FRONTEND_ORIGIN=http://localhost:4200
PORT=8000
```

6. Start the FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```
Backend will be live at `http://localhost:8000`. Interactive OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

### Frontend Setup

1. Open a new terminal and navigate to `frontend/`:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the Angular dev server:
```bash
npm start
```
Frontend will be live at `http://localhost:4200`.

---

## API Documentation

### `GET /api/health`
Returns system health and provider configuration status without disclosing secrets.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "providers": {
    "openai_configured": true,
    "web_search_configured": true,
    "weather_configured": true
  }
}
```

### `POST /api/agent`
Accepts a natural-language query and coordinates tool execution.

**Request:**
```json
{
  "query": "What is 15% of 2400?"
}
```

**Response:**
```json
{
  "query": "What is 15% of 2400?",
  "answer": "15% of 2400 is 360.",
  "tools_used": [
    {
      "name": "calculator",
      "status": "success",
      "summary": "Calculated: 15% of 2400 = 360",
      "detail": "360"
    }
  ],
  "sources": [],
  "success": true,
  "error": null
}
```

---

## Testing

Backend unit and integration tests are located in `backend/tests/` and use mocked responses so they execute instantly without requiring real API credits.

Run the test suite:
```bash
cd backend
.\venv\Scripts\pytest tests -v
```

### Test Coverage Summary:
- **Calculator correctness**: Addition, multiplication, percentages (`15% of 2500`), powers (`2^10`), square roots (`sqrt(2025)`), discounts (`2000 / (1 - 0.20)`).
- **Calculator safety**: Rejection of `eval()`, `__import__`, syntax errors, division by zero, negative square roots, numerical overflow.
- **Web search tool**: Mocked Tavily responses, source formatting, missing key handling, timeout handling.
- **Weather tool**: Mocked OpenWeatherMap data, Celsius/Fahrenheit units, 404 location not found, missing key handling.
- **Agent orchestrator**: Mocked OpenAI client testing direct response without tools, single tool invocation, multiple tool invocations in one query, max rounds guard.
- **FastAPI routes**: Health endpoint verification and input validation (empty query rejection with 422).

---

## Example Queries to Try

| Category | Query | Tools Used |
|---|---|---|
| **Mathematics** | `Calculate 15% of 2,500` | Calculator |
| **Complex Math** | `What is (125 × 8) + 450?` | Calculator |
| **Algebra / Discount** | `If a product costs ₹2,000 after a 20% discount, what was its original price?` | Calculator |
| **Square Root** | `Calculate the square root of 2025` | Calculator |
| **Current Weather** | `What's the weather in Dehradun?` | Weather |
| **Weather Comparison** | `Is the weather in Delhi warmer than in Jaipur?` | Weather (multiple calls) |
| **Web Search** | `What are the latest developments in AI agents?` | Web Search |
| **Direct Reasoning** | `Explain what an AI agent is and how tool calling works` | Direct AI (no tools) |

---

## Limitations & Future Improvements
1. **Streaming Responses**: Currently returns complete responses via JSON; can be enhanced with Server-Sent Events (SSE) for token streaming.
2. **Additional Tools**: Support for database querying (SQL tool), code execution sandbox, or document ingestion.
3. **Multi-turn Chat Sessions**: Support optional conversation threads with session IDs if persistent history is required.

---

## Author & Connect

- **LinkedIn**: [linkedin.com/in/mahipalsingh08/](https://www.linkedin.com/in/mahipalsingh08/)
- **Website**: [mahipal.tech](https://mahipal.tech)
