import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    CommonModule,
    MatIconModule,
    MatTooltipModule,
  ],
  template: `
    <div class="app-shell">
      <aside class="sidebar">
        <div class="sidebar-brand">
          <div class="brand-icon">
            <mat-icon>inventory_2</mat-icon>
          </div>
          <span class="brand-name">EstoqueIncenso</span>
        </div>

        <nav class="sidebar-nav">
          <a routerLink="/producao" routerLinkActive="active" class="nav-item"
             matTooltip="Produção" matTooltipPosition="right" matTooltipShowDelay="300">
            <mat-icon>grid_view</mat-icon>
            <span class="nav-label">Produção</span>
          </a>
          <a routerLink="/funcionarias" routerLinkActive="active" class="nav-item"
             matTooltip="Funcionárias" matTooltipPosition="right" matTooltipShowDelay="300">
            <mat-icon>group</mat-icon>
            <span class="nav-label">Funcionárias</span>
          </a>
        </nav>

        <div class="sidebar-footer">
          <span class="sidebar-version">v1.0</span>
        </div>
      </aside>

      <div class="main-content">
        <router-outlet />
      </div>
    </div>

  `,
  styleUrl: './app.component.scss'
})
export class AppComponent {}
