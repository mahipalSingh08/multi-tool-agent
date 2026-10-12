import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AgentService } from '../../core/services/agent.service';
import { AgentResponse, HealthResponse, ToolExecution } from '../../core/models/agent.model';

@Component({
  selector: 'app-agent',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agent.component.html',
  styleUrls: ['./agent.component.css'],
})
export class AgentComponent implements OnInit {
  private readonly agentService = inject(AgentService);

  readonly query = signal<string>('');
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly lastResponse = signal<AgentResponse | null>(null);
  readonly health = signal<HealthResponse | null>(null);
  readonly copied = signal<boolean>(false);

  readonly exampleQueries: string[] = [
    'What are the latest developments in AI agents?',
    'Calculate 25% of 8400',
    "What's the weather in Dehradun?",
    'Search for recent Angular 22 updates',
    'What is the weather difference between Delhi and Mumbai?',
  ];

  ngOnInit(): void {
    this.checkBackendHealth();
  }

  checkBackendHealth(): void {
    this.agentService.checkHealth().subscribe({
      next: (res) => this.health.set(res),
      error: () => this.health.set(null),
    });
  }

  setQuery(text: string): void {
    this.query.set(text);
  }

  handleKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.submitQuery();
    }
  }

  submitQuery(): void {
    const trimmed = this.query().trim();
    if (!trimmed || this.isLoading()) {
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    this.agentService.askAgent(trimmed).subscribe({
      next: (response) => {
        this.isLoading.set(false);
        if (!response.success && response.error) {
          this.errorMessage.set(response.error);
        }
        this.lastResponse.set(response);
      },
      error: (err) => {
        this.isLoading.set(false);
        const detail = err.error?.detail || err.error?.error || err.message || 'Failed to communicate with backend service.';
        this.errorMessage.set(detail);
      },
    });
  }

  retry(): void {
    this.submitQuery();
  }

  copyAnswer(): void {
    const answer = this.lastResponse()?.answer;
    if (answer) {
      navigator.clipboard.writeText(answer).then(() => {
        this.copied.set(true);
        setTimeout(() => this.copied.set(false), 2000);
      });
    }
  }

  getToolDisplayName(toolName: string): string {
    switch (toolName) {
      case 'web_search':
        return 'Web Search';
      case 'calculator':
        return 'Calculator';
      case 'get_weather':
        return 'Weather';
      default:
        return toolName;
    }
  }

  getToolIcon(toolName: string): string {
    switch (toolName) {
      case 'web_search':
        return 'search';
      case 'calculator':
        return 'calculate';
      case 'get_weather':
        return 'cloud';
      default:
        return 'build';
    }
  }
}
