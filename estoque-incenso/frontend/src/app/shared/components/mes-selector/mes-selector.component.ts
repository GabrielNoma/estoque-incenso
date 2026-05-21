import { Component, EventEmitter, Input, OnInit, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

export interface MesAno {
  ano: number;
  mes: number;
}

@Component({
  selector: 'app-mes-selector',
  standalone: true,
  imports: [CommonModule, FormsModule, MatSelectModule, MatFormFieldModule, MatButtonModule, MatIconModule],
  template: `
    <div class="mes-selector">
      <button mat-icon-button class="nav-btn" (click)="navegar(-1)" aria-label="Mês anterior">
        <mat-icon>chevron_left</mat-icon>
      </button>

      <div class="selects-group">
        <mat-form-field appearance="outline" class="campo-mes compact">
          <mat-select [(ngModel)]="mesSelecionado" (ngModelChange)="emitir()">
            <mat-option *ngFor="let m of meses" [value]="m.valor">{{ m.label }}</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline" class="campo-ano compact">
          <mat-select [(ngModel)]="anoSelecionado" (ngModelChange)="emitir()">
            <mat-option *ngFor="let a of anos" [value]="a">{{ a }}</mat-option>
          </mat-select>
        </mat-form-field>
      </div>

      <button mat-icon-button class="nav-btn" (click)="navegar(1)" aria-label="Próximo mês">
        <mat-icon>chevron_right</mat-icon>
      </button>
    </div>
  `,
  styles: [`
    .mes-selector {
      display: flex;
      align-items: center;
      gap: var(--space-1);
    }

    .selects-group {
      display: flex;
      align-items: center;
      gap: 4px;
    }

    /* Botões de navegação */
    .nav-btn {
      width: 34px !important;
      height: 34px !important;
      padding: 5px !important;
      color: var(--color-on-surface-muted);
      transition: background-color var(--transition-fast), color var(--transition-fast);
      border-radius: var(--radius-full) !important;

      &:hover {
        background: var(--color-surface-variant) !important;
        color: var(--color-primary) !important;
      }
    }

    /* Form fields */
    .campo-mes { width: 122px; }
    .campo-ano { width: 88px; }

    /* Remove espaço do hint */
    ::ng-deep .campo-mes .mat-mdc-form-field-subscript-wrapper,
    ::ng-deep .campo-ano .mat-mdc-form-field-subscript-wrapper {
      display: none;
    }

    /* Altura compacta */
    ::ng-deep .campo-mes .mat-mdc-form-field-flex,
    ::ng-deep .campo-ano .mat-mdc-form-field-flex {
      height: 36px;
      align-items: center;
    }

    /* Padding interno */
    ::ng-deep .campo-mes .mat-mdc-select-trigger,
    ::ng-deep .campo-ano .mat-mdc-select-trigger {
      padding: 0 8px;
    }

    /* Bordas arredondadas pill */
    ::ng-deep .campo-mes .mdc-notched-outline__leading,
    ::ng-deep .campo-ano .mdc-notched-outline__leading {
      border-radius: 18px 0 0 18px !important;
      min-width: 18px !important;
    }
    ::ng-deep .campo-mes .mdc-notched-outline__trailing,
    ::ng-deep .campo-ano .mdc-notched-outline__trailing {
      border-radius: 0 18px 18px 0 !important;
    }

    /* Cor da borda */
    ::ng-deep .campo-mes .mdc-notched-outline__leading,
    ::ng-deep .campo-mes .mdc-notched-outline__notch,
    ::ng-deep .campo-mes .mdc-notched-outline__trailing,
    ::ng-deep .campo-ano .mdc-notched-outline__leading,
    ::ng-deep .campo-ano .mdc-notched-outline__notch,
    ::ng-deep .campo-ano .mdc-notched-outline__trailing {
      border-width: 1.5px;
      border-color: var(--color-border-strong) !important;
    }

    /* Hover / focus na borda */
    ::ng-deep .campo-mes:hover .mdc-notched-outline__leading,
    ::ng-deep .campo-mes:hover .mdc-notched-outline__notch,
    ::ng-deep .campo-mes:hover .mdc-notched-outline__trailing,
    ::ng-deep .campo-ano:hover .mdc-notched-outline__leading,
    ::ng-deep .campo-ano:hover .mdc-notched-outline__notch,
    ::ng-deep .campo-ano:hover .mdc-notched-outline__trailing {
      border-color: var(--color-primary) !important;
    }

    /* Texto centralizado */
    ::ng-deep .campo-mes .mat-mdc-select-value,
    ::ng-deep .campo-ano .mat-mdc-select-value {
      font-size: var(--font-size-base);
      font-weight: var(--font-weight-medium);
      color: var(--color-on-surface);
      overflow: visible;
      text-overflow: unset;
    }
  `]
})
export class MesSelectorComponent implements OnInit {
  @Input() valor: MesAno = { ano: new Date().getFullYear(), mes: new Date().getMonth() + 1 };
  @Output() mudanca = new EventEmitter<MesAno>();

  mesSelecionado = 1;
  anoSelecionado = 2026;

  meses = [
    { valor: 1, label: 'Janeiro' }, { valor: 2, label: 'Fevereiro' },
    { valor: 3, label: 'Março' }, { valor: 4, label: 'Abril' },
    { valor: 5, label: 'Maio' }, { valor: 6, label: 'Junho' },
    { valor: 7, label: 'Julho' }, { valor: 8, label: 'Agosto' },
    { valor: 9, label: 'Setembro' }, { valor: 10, label: 'Outubro' },
    { valor: 11, label: 'Novembro' }, { valor: 12, label: 'Dezembro' }
  ];

  anos = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i);

  ngOnInit() {
    this.mesSelecionado = this.valor.mes;
    this.anoSelecionado = this.valor.ano;
  }

  emitir() {
    this.mudanca.emit({ ano: this.anoSelecionado, mes: this.mesSelecionado });
  }

  navegar(delta: number) {
    let mes = this.mesSelecionado + delta;
    let ano = this.anoSelecionado;
    if (mes < 1)  { mes = 12; ano--; }
    if (mes > 12) { mes = 1;  ano++; }
    this.mesSelecionado = mes;
    this.anoSelecionado = ano;
    this.emitir();
  }
}
