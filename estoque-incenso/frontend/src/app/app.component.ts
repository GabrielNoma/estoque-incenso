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

    <!-- Navegação mobile (bottom nav) -->
    <nav class="bottom-nav">
      <a routerLink="/producao" routerLinkActive="active" class="bottom-nav-item">
        <mat-icon>grid_view</mat-icon>
        <span>Produção</span>
      </a>
      <a routerLink="/funcionarias" routerLinkActive="active" class="bottom-nav-item">
        <mat-icon>group</mat-icon>
        <span>Funcionárias</span>
      </a>
    </nav>
  `,
  styles: [`
    /* ── Layout principal ──────────────────────────────── */
    .app-shell {
      display: flex;
      height: 100vh;
      overflow: hidden;
    }

    /* ── Sidebar ────────────────────────────────────────── */
    .sidebar {
      width: var(--sidebar-width);
      height: 100vh;
      background: var(--color-surface);
      border-right: 1px solid var(--color-border);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
      position: sticky;
      top: 0;
      overflow-y: auto;
      overflow-x: hidden;
      box-shadow: var(--shadow-xs);
      z-index: 100;
    }

    /* ── Brand ──────────────────────────────────────────── */
    .sidebar-brand {
      display: flex;
      align-items: center;
      gap: var(--space-3);
      padding: var(--space-5) var(--space-4);
      border-bottom: 1px solid var(--color-border);
      flex-shrink: 0;
    }

    .brand-icon {
      width: 36px;
      height: 36px;
      background: var(--color-primary);
      border-radius: var(--radius-md);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-primary-contrast);
      flex-shrink: 0;
      box-shadow: 0 2px 8px rgba(var(--color-primary-rgb), 0.35);

      mat-icon {
        font-size: 18px;
        width: 18px;
        height: 18px;
      }
    }

    .brand-name {
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-bold);
      color: var(--color-on-surface);
      letter-spacing: -0.01em;
      line-height: 1.2;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    /* ── Nav ────────────────────────────────────────────── */
    .sidebar-nav {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: var(--space-3) var(--space-3);
      flex: 1;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: var(--space-3);
      padding: 9px var(--space-3);
      border-radius: var(--radius-md);
      color: var(--color-on-surface-muted);
      text-decoration: none;
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-medium);
      transition:
        background-color var(--transition-fast),
        color var(--transition-fast);

      mat-icon {
        font-size: 20px;
        width: 20px;
        height: 20px;
        flex-shrink: 0;
        transition: color var(--transition-fast);
      }

      .nav-label {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      &:hover {
        background: var(--color-surface-variant);
        color: var(--color-primary);
      }

      &.active {
        background: var(--color-surface-variant);
        color: var(--color-primary);
        font-weight: var(--font-weight-semibold);

        mat-icon { color: var(--color-primary); }
      }
    }

    /* ── Footer da sidebar ──────────────────────────────── */
    .sidebar-footer {
      padding: var(--space-4);
      border-top: 1px solid var(--color-border);
      flex-shrink: 0;
    }

    .sidebar-version {
      font-size: var(--font-size-xs);
      color: var(--color-on-surface-disabled);
    }

    /* ── Conteúdo principal ─────────────────────────────── */
    .main-content {
      flex: 1;
      overflow-y: auto;
      overflow-x: hidden;
      padding: var(--space-6) var(--space-8);
      background: var(--color-background);
      min-width: 0;
    }

    /* ── Bottom nav (mobile) ────────────────────────────── */
    .bottom-nav {
      display: none;
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: 60px;
      background: var(--color-surface);
      border-top: 1px solid var(--color-border);
      box-shadow: 0 -2px 8px rgba(0,0,0,.08);
      z-index: 200;
      align-items: stretch;
    }

    .bottom-nav-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 2px;
      color: var(--color-on-surface-muted);
      text-decoration: none;
      font-size: 10px;
      font-weight: var(--font-weight-medium);
      transition: color var(--transition-fast);

      mat-icon { font-size: 22px; width: 22px; height: 22px; }

      &.active { color: var(--color-primary); }
      &:hover   { color: var(--color-primary); }
    }

    /* ── Responsivo ─────────────────────────────────────── */
    @media (max-width: 768px) {
      .sidebar     { display: none; }
      .bottom-nav  { display: flex; }
      .main-content {
        padding: var(--space-4);
        padding-bottom: 72px;
      }
    }
  `]
})
export class AppComponent {}
