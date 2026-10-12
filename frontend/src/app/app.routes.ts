import { Routes } from '@angular/router';
import { AgentComponent } from './features/agent/agent.component';

export const routes: Routes = [
  { path: '', component: AgentComponent },
  { path: '**', redirectTo: '' },
];
