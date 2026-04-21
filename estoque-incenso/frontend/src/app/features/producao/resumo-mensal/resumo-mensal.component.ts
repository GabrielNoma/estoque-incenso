import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatDividerModule } from '@angular/material/divider';

import { GradeMensal, FuncionariaComRegistros } from '../producao.service';

interface ResumoFuncionaria {
  nome: string;
  totalProduzido: number;
  atestados: number;
  faltas: number;
  outros: number;
}

@Component({
  selector: 'app-resumo-mensal',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatTableModule, MatDividerModule],
  template: `
    <mat-card class="resumo-card">
      <mat-card-header>
        <mat-card-title>Resumo — {{ nomeMes }} {{ grade?.ano }}</mat-card-title>
      </mat-card-header>
      <mat-card-content>

        <div class="total-geral">
          <span class="label-total">Total geral produzido</span>
          <span class="valor-total">{{ totalGeral }}</span>
        </div>

        <mat-divider style="margin: 12px 0" />

        <table mat-table [dataSource]="resumos" class="tabela-resumo">
          <ng-container matColumnDef="nome">
            <th mat-header-cell *matHeaderCellDef>Funcionária</th>
            <td mat-cell *matCellDef="let r">{{ r.nome }}</td>
            <td mat-footer-cell *matFooterCellDef><strong>TOTAL</strong></td>
          </ng-container>

          <ng-container matColumnDef="totalProduzido">
            <th mat-header-cell *matHeaderCellDef>Produção</th>
            <td mat-cell *matCellDef="let r">{{ r.totalProduzido }}</td>
            <td mat-footer-cell *matFooterCellDef><strong>{{ totalGeral }}</strong></td>
          </ng-container>

          <ng-container matColumnDef="atestados">
            <th mat-header-cell *matHeaderCellDef>Atestados</th>
            <td mat-cell *matCellDef="let r">{{ r.atestados || '—' }}</td>
            <td mat-footer-cell *matFooterCellDef>{{ totalAtestados || '—' }}</td>
          </ng-container>

          <ng-container matColumnDef="faltas">
            <th mat-header-cell *matHeaderCellDef>Faltas</th>
            <td mat-cell *matCellDef="let r">{{ r.faltas || '—' }}</td>
            <td mat-footer-cell *matFooterCellDef>{{ totalFaltas || '—' }}</td>
          </ng-container>

          <ng-container matColumnDef="outros">
            <th mat-header-cell *matHeaderCellDef>Outros</th>
            <td mat-cell *matCellDef="let r">{{ r.outros || '—' }}</td>
            <td mat-footer-cell *matFooterCellDef>{{ totalOutros || '—' }}</td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="colunas"></tr>
          <tr mat-row *matRowDef="let row; columns: colunas;"></tr>
          <tr mat-footer-row *matFooterRowDef="colunas"></tr>
        </table>

      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .resumo-card { margin-top: 24px; }
    .total-geral { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; }
    .label-total { font-size: 14px; color: #555; }
    .valor-total { font-size: 28px; font-weight: 700; color: #1976d2; }
    .tabela-resumo { width: 100%; }
  `]
})
export class ResumoMensalComponent implements OnChanges {
  @Input() grade: GradeMensal | null = null;

  resumos: ResumoFuncionaria[] = [];
  colunas = ['nome', 'totalProduzido', 'atestados', 'faltas', 'outros'];

  readonly mesesNomes = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
    'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];

  get nomeMes(): string {
    return this.grade ? this.mesesNomes[this.grade.mes - 1] : '';
  }

  get totalGeral(): number { return this.resumos.reduce((s, r) => s + r.totalProduzido, 0); }
  get totalAtestados(): number { return this.resumos.reduce((s, r) => s + r.atestados, 0); }
  get totalFaltas(): number { return this.resumos.reduce((s, r) => s + r.faltas, 0); }
  get totalOutros(): number { return this.resumos.reduce((s, r) => s + r.outros, 0); }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['grade'] && this.grade) {
      this.resumos = this.grade.funcionarias.map(f => this.calcularResumo(f));
    }
  }

  private calcularResumo(f: FuncionariaComRegistros): ResumoFuncionaria {
    let totalProduzido = 0, atestados = 0, faltas = 0, outros = 0;
    for (const r of f.registros) {
      if (r.falta) {
        if (r.motivoFalta === 'atestado') atestados++;
        else if (r.motivoFalta === 'falta') faltas++;
        else outros++;
      } else {
        totalProduzido += r.quantidade ?? 0;
      }
    }
    return { nome: f.nome, totalProduzido, atestados, faltas, outros };
  }
}
