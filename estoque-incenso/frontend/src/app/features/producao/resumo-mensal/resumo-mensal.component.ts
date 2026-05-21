import { Component, Input, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';

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
  imports: [CommonModule, MatCardModule, MatTableModule, MatDividerModule, MatIconModule],
  template: `
    <div class="resumo-card card">

      <!-- Cabeçalho do card -->
      <div class="resumo-header">
        <div class="resumo-titulo-grupo">
          <mat-icon class="resumo-icone">bar_chart</mat-icon>
          <div>
            <h2 class="resumo-titulo">Resumo Mensal</h2>
            <p class="resumo-subtitulo">{{ nomeMes }} {{ grade?.ano }}</p>
          </div>
        </div>

        <!-- Destaque do total geral -->
        <div class="total-destaque">
          <span class="total-label">Total produzido</span>
          <span class="total-valor">{{ totalGeral }}<span class="total-unidade"> dz</span></span>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Tabela de resumo -->
      <div class="tabela-container">
        <table mat-table [dataSource]="resumos" class="tabela-resumo">

          <ng-container matColumnDef="nome">
            <th mat-header-cell *matHeaderCellDef>Funcionária</th>
            <td mat-cell *matCellDef="let r">
              <div class="nome-cell-resumo">
                <span class="avatar avatar-sm resumo-avatar">{{ r.nome[0] }}</span>
                {{ r.nome }}
              </div>
            </td>
            <td mat-footer-cell *matFooterCellDef class="footer-label">TOTAL</td>
          </ng-container>

          <ng-container matColumnDef="totalProduzido">
            <th mat-header-cell *matHeaderCellDef>Produção (dz)</th>
            <td mat-cell *matCellDef="let r">
              <span class="valor-producao">{{ r.totalProduzido }}</span>
              <span class="valor-unidade"> dz</span>
            </td>
            <td mat-footer-cell *matFooterCellDef>
              <span class="valor-producao footer-total">{{ totalGeral }}</span>
              <span class="valor-unidade"> dz</span>
            </td>
          </ng-container>

          <ng-container matColumnDef="atestados">
            <th mat-header-cell *matHeaderCellDef>Atestados</th>
            <td mat-cell *matCellDef="let r">
              <span *ngIf="r.atestados > 0" class="badge badge-warning">{{ r.atestados }}</span>
              <span *ngIf="r.atestados === 0" class="valor-zero">—</span>
            </td>
            <td mat-footer-cell *matFooterCellDef>
              <span *ngIf="totalAtestados > 0" class="badge badge-warning">{{ totalAtestados }}</span>
              <span *ngIf="totalAtestados === 0" class="valor-zero">—</span>
            </td>
          </ng-container>

          <ng-container matColumnDef="faltas">
            <th mat-header-cell *matHeaderCellDef>Faltas</th>
            <td mat-cell *matCellDef="let r">
              <span *ngIf="r.faltas > 0" class="badge badge-danger">{{ r.faltas }}</span>
              <span *ngIf="r.faltas === 0" class="valor-zero">—</span>
            </td>
            <td mat-footer-cell *matFooterCellDef>
              <span *ngIf="totalFaltas > 0" class="badge badge-danger">{{ totalFaltas }}</span>
              <span *ngIf="totalFaltas === 0" class="valor-zero">—</span>
            </td>
          </ng-container>

          <ng-container matColumnDef="outros">
            <th mat-header-cell *matHeaderCellDef>Outros</th>
            <td mat-cell *matCellDef="let r">
              <span *ngIf="r.outros > 0" class="badge badge-primary">{{ r.outros }}</span>
              <span *ngIf="r.outros === 0" class="valor-zero">—</span>
            </td>
            <td mat-footer-cell *matFooterCellDef>
              <span *ngIf="totalOutros > 0" class="badge badge-primary">{{ totalOutros }}</span>
              <span *ngIf="totalOutros === 0" class="valor-zero">—</span>
            </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="colunas"></tr>
          <tr mat-row *matRowDef="let row; columns: colunas;"></tr>
          <tr mat-footer-row *matFooterRowDef="colunas"></tr>
        </table>
      </div>

    </div>
  `,
  styleUrl: './resumo-mensal.component.scss'
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

  get totalGeral():     number { return this.resumos.reduce((s, r) => s + r.totalProduzido, 0); }
  get totalAtestados(): number { return this.resumos.reduce((s, r) => s + r.atestados,     0); }
  get totalFaltas():    number { return this.resumos.reduce((s, r) => s + r.faltas,        0); }
  get totalOutros():    number { return this.resumos.reduce((s, r) => s + r.outros,        0); }

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
