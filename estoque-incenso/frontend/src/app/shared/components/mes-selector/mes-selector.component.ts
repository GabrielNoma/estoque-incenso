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
      <button mat-icon-button (click)="navegar(-1)" matTooltip="Mês anterior">
        <mat-icon>chevron_left</mat-icon>
      </button>

      <mat-form-field appearance="outline" class="campo-mes">
        <mat-select [(ngModel)]="mesSelecionado" (ngModelChange)="emitir()">
          <mat-option *ngFor="let m of meses" [value]="m.valor">{{ m.label }}</mat-option>
        </mat-select>
      </mat-form-field>

      <mat-form-field appearance="outline" class="campo-ano">
        <mat-select [(ngModel)]="anoSelecionado" (ngModelChange)="emitir()">
          <mat-option *ngFor="let a of anos" [value]="a">{{ a }}</mat-option>
        </mat-select>
      </mat-form-field>

      <button mat-icon-button (click)="navegar(1)" matTooltip="Próximo mês">
        <mat-icon>chevron_right</mat-icon>
      </button>
    </div>
  `,
  styles: [`
    .mes-selector { display: flex; align-items: center; gap: 2px; }
    .campo-mes { width: 118px; }
    .campo-ano { width: 86px; }

    /* Remove espaço de hint/erro */
    ::ng-deep .campo-mes .mat-mdc-form-field-subscript-wrapper,
    ::ng-deep .campo-ano .mat-mdc-form-field-subscript-wrapper { display: none; }

    /* Altura reduzida */
    ::ng-deep .campo-mes .mat-mdc-form-field-flex,
    ::ng-deep .campo-ano .mat-mdc-form-field-flex { height: 34px; align-items: center; }

    /* Bordas pill */
    ::ng-deep .campo-mes .mdc-notched-outline__leading,
    ::ng-deep .campo-ano .mdc-notched-outline__leading {
      border-radius: 17px 0 0 17px !important; min-width: 17px !important;
    }
    ::ng-deep .campo-mes .mdc-notched-outline__trailing,
    ::ng-deep .campo-ano .mdc-notched-outline__trailing {
      border-radius: 0 17px 17px 0 !important;
    }

    /* Borda mais fina */
    ::ng-deep .campo-mes .mdc-notched-outline__leading,
    ::ng-deep .campo-mes .mdc-notched-outline__notch,
    ::ng-deep .campo-mes .mdc-notched-outline__trailing,
    ::ng-deep .campo-ano .mdc-notched-outline__leading,
    ::ng-deep .campo-ano .mdc-notched-outline__notch,
    ::ng-deep .campo-ano .mdc-notched-outline__trailing { border-width: 1.5px; }

    /* Texto centralizado e sem overflow */
    ::ng-deep .campo-mes .mat-mdc-select-trigger,
    ::ng-deep .campo-ano .mat-mdc-select-trigger { overflow: visible; }
    ::ng-deep .campo-ano .mat-mdc-select-value { overflow: visible; text-overflow: unset; }
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
    if (mes < 1) { mes = 12; ano--; }
    if (mes > 12) { mes = 1; ano++; }
    this.mesSelecionado = mes;
    this.anoSelecionado = ano;
    this.emitir();
  }
}
