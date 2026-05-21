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
  styleUrl: './mes-selector.component.scss'
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
