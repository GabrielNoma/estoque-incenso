import { Component, EventEmitter, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

import { RegistroDiario } from '../producao.service';

export interface SalvarEvento {
  funcionariaId: number;
  data: string;
  quantidade: number | null;
}

export interface AbrirFaltaEvento {
  funcionariaId: number;
  data: string;
  registro: RegistroDiario | null;
}

@Component({
  selector: 'app-celula-producao',
  standalone: true,
  imports: [CommonModule, FormsModule, MatIconModule, MatButtonModule, MatTooltipModule],
  template: `
    <div class="celula" [class.falta]="registro?.falta" [class.fim-de-semana]="fimDeSemana">
      <ng-container *ngIf="registro?.falta; else inputNumero">
        <span class="label-falta" [matTooltip]="registro?.motivoFalta ?? ''">F</span>
        <button mat-icon-button class="btn-limpar" (click)="limparFalta()" matTooltip="Remover falta">
          <mat-icon>close</mat-icon>
        </button>
      </ng-container>

      <ng-template #inputNumero>
        <input
          type="number"
          min="0"
          [value]="quantidade"
          (input)="aoDigitar($event)"
          (blur)="aoSair()"
          class="input-quantidade"
          [disabled]="fimDeSemana"
        />
        <button mat-icon-button class="btn-falta" (click)="abrirFalta()" matTooltip="Registrar falta" [disabled]="fimDeSemana">
          <mat-icon>sick</mat-icon>
        </button>
      </ng-template>
    </div>
  `,
  styles: [`
    .celula { display: flex; align-items: center; gap: 2px; padding: 2px; }
    .celula.falta { background: #fff9c4; }
    .celula.fim-de-semana { background: #f5f5f5; }
    .input-quantidade {
      width: 52px; text-align: center; border: 1px solid #ccc;
      border-radius: 4px; padding: 2px 4px; font-size: 13px;
    }
    .input-quantidade:focus { outline: none; border-color: #1976d2; }
    .label-falta { font-weight: 700; color: #e65100; font-size: 13px; min-width: 20px; }
    .btn-falta, .btn-limpar { width: 24px; height: 24px; line-height: 24px; }
    .btn-falta mat-icon, .btn-limpar mat-icon { font-size: 16px; }
  `]
})
export class CelulaProducaoComponent implements OnChanges {
  @Input() funcionariaId!: number;
  @Input() data!: string;
  @Input() registro: RegistroDiario | null = null;
  @Input() fimDeSemana = false;

  @Output() salvar = new EventEmitter<SalvarEvento>();
  @Output() abrirDialogoFalta = new EventEmitter<AbrirFaltaEvento>();
  @Output() excluir = new EventEmitter<{ id: number }>();

  quantidade: number | null = null;
  private valorAnterior: number | null = null;
  private digitar$ = new Subject<number | null>();
  private sub = this.digitar$.pipe(debounceTime(500), distinctUntilChanged())
    .subscribe(v => this.emitirSalvar(v));

  ngOnChanges(changes: SimpleChanges) {
    if (changes['registro']) {
      this.quantidade = this.registro?.quantidade ?? null;
      this.valorAnterior = this.quantidade;
    }
  }

  aoDigitar(event: Event) {
    const val = (event.target as HTMLInputElement).valueAsNumber;
    this.quantidade = isNaN(val) ? null : val;
    this.digitar$.next(this.quantidade);
  }

  aoSair() {
    this.emitirSalvar(this.quantidade);
  }

  private emitirSalvar(quantidade: number | null) {
    if (quantidade === this.valorAnterior) return;
    this.valorAnterior = quantidade;
    this.salvar.emit({ funcionariaId: this.funcionariaId, data: this.data, quantidade });
  }

  abrirFalta() {
    this.abrirDialogoFalta.emit({ funcionariaId: this.funcionariaId, data: this.data, registro: this.registro });
  }

  limparFalta() {
    if (this.registro?.id) this.excluir.emit({ id: this.registro.id });
  }

  ngOnDestroy() { this.sub.unsubscribe(); }
}
