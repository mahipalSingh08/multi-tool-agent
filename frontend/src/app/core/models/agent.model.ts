export interface ToolExecution {
  name: string;
  status: 'success' | 'error' | 'skipped';
  summary: string;
  detail?: string | null;
}

export interface SourceItem {
  title: string;
  url: string;
  snippet?: string | null;
}

export interface AgentResponse {
  query: string;
  answer: string;
  tools_used: ToolExecution[];
  sources: SourceItem[];
  success: boolean;
  error?: string | null;
}

export interface HealthResponse {
  status: string;
  version: string;
  providers: {
    openai_configured: boolean;
    web_search_configured: boolean;
    weather_configured: boolean;
  };
}
