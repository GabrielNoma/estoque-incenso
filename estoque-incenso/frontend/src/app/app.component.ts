import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive, MatToolbarModule, MatButtonModule],
  template: `
    <mat-toolbar color="primary">
      <span>Estoque Incenso</span>
      <span style="flex:1"></span>
      <a mat-button routerLink="/producao" routerLinkActive="active">Produção</a>
      <a mat-button routerLink="/funcionarias" routerLinkActive="active">Funcionárias</a>
    </mat-toolbar>
    <main style="padding: 16px">
      <router-outlet />
    </main>
  `,
  styles: [`.active { background: rgba(255,255,255,0.15); border-radius: 4px; }`]
})
export class AppComponent {}
