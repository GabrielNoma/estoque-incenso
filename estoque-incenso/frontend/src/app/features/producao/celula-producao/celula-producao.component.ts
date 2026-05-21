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
        <span class="label-falta" [matTooltip]="registro?.motivoFalta ?? 'Falta'">F</span>
        <button mat-icon-button class="btn-acao" (click)="limparFalta()"
                matTooltip="Remover falta" aria-label="Remover falta">
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
          placeholder="dz"
          [disabled]="fimDeSemana"
          aria-label="Quantidade em dúzias"
        />
        <button mat-icon-button class="btn-acao btn-falta" (click)="abrirFalta()"
                matTooltip="Registrar falta" aria-label="Registrar falta"
                [disabled]="fimDeSemana">
          <mat-icon>sick</mat-icon>
        </button>
      </ng-template>
    </div>
  `,
  styleUrl: './celula-producao.component.scss'
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
