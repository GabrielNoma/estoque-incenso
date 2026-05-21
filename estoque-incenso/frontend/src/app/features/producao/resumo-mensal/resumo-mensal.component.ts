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
  styles: [`
    .resumo-card {
      margin-top: var(--space-6);
    }

    /* ── Cabeçalho ─────────────────────────────────────── */
    .resumo-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: var(--space-4);
      flex-wrap: wrap;
    }

    .resumo-titulo-grupo {
      display: flex;
      align-items: center;
      gap: var(--space-3);
    }

    .resumo-icone {
      font-size: 22px;
      width: 22px;
      height: 22px;
      color: var(--color-primary);
      flex-shrink: 0;
    }

    .resumo-titulo {
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-bold);
      color: var(--color-on-surface);
      margin: 0;
      line-height: 1.2;
    }

    .resumo-subtitulo {
      font-size: var(--font-size-sm);
      color: var(--color-on-surface-muted);
      margin: 2px 0 0;
    }

    /* ── Total destaque ──────────────────────────────────── */
    .total-destaque {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 2px;
    }

    .total-label {
      font-size: var(--font-size-xs);
      font-weight: var(--font-weight-medium);
      color: var(--color-on-surface-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .total-valor {
      font-size: var(--font-size-3xl);
      font-weight: var(--font-weight-bold);
      color: var(--color-primary);
      line-height: 1;
    }

    .total-unidade {
      font-size: var(--font-size-lg);
      font-weight: var(--font-weight-normal);
      color: var(--color-on-surface-muted);
    }

    /* ── Tabela ─────────────────────────────────────────── */
    .tabela-container {
      overflow-x: auto;
      margin: 0 calc(-1 * var(--space-6));
      padding: 0 var(--space-6);
    }

    .tabela-resumo {
      width: 100%;
      min-width: 500px;
    }

    /* Header */
    ::ng-deep .tabela-resumo .mat-mdc-header-row {
      background: var(--color-surface-variant);
      border-radius: var(--radius-sm);
    }

    ::ng-deep .tabela-resumo .mat-mdc-header-cell {
      font-size: var(--font-size-xs) !important;
      font-weight: var(--font-weight-semibold) !important;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--color-on-surface-muted) !important;
      padding: 10px 16px;
      border-bottom: 1px solid var(--color-border);
    }

    /* Células do corpo */
    ::ng-deep .tabela-resumo .mat-mdc-cell {
      font-size: var(--font-size-base);
      color: var(--color-on-surface);
      padding: 10px 16px;
      border-bottom: 1px solid var(--color-border);
    }

    /* Hover nas linhas */
    ::ng-deep .tabela-resumo .mat-mdc-row:hover .mat-mdc-cell {
      background: var(--color-surface-variant);
    }

    /* Footer */
    ::ng-deep .tabela-resumo .mat-mdc-footer-row {
      background: var(--color-surface-variant);
      border-top: 2px solid var(--color-border-strong);
    }

    ::ng-deep .tabela-resumo .mat-mdc-footer-cell {
      font-size: var(--font-size-sm);
      font-weight: var(--font-weight-bold);
      color: var(--color-on-surface);
      padding: 10px 16px;
      border-top: none;
    }

    /* ── Conteúdo das células ───────────────────────────── */
    .nome-cell-resumo {
      display: flex;
      align-items: center;
      gap: var(--space-2);
      font-weight: var(--font-weight-medium);
    }

    /* Cores de avatar por posição */
    :host ::ng-deep .mat-mdc-row:nth-child(6n+1) .resumo-avatar { background: #1565C0; }
    :host ::ng-deep .mat-mdc-row:nth-child(6n+2) .resumo-avatar { background: #7C3AED; }
    :host ::ng-deep .mat-mdc-row:nth-child(6n+3) .resumo-avatar { background: #059669; }
    :host ::ng-deep .mat-mdc-row:nth-child(6n+4) .resumo-avatar { background: #B45309; }
    :host ::ng-deep .mat-mdc-row:nth-child(6n+5) .resumo-avatar { background: #DC2626; }
    :host ::ng-deep .mat-mdc-row:nth-child(6n+6) .resumo-avatar { background: #0891B2; }

    .valor-producao {
      font-weight: var(--font-weight-semibold);
      color: var(--color-primary);
    }

    .footer-total {
      font-size: var(--font-size-md);
    }

    .valor-unidade {
      font-size: var(--font-size-xs);
      color: var(--color-on-surface-muted);
      font-weight: var(--font-weight-normal);
    }

    .footer-label {
      font-size: var(--font-size-xs) !important;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--color-on-surface-muted) !important;
    }

    .valor-zero {
      color: var(--color-on-surface-disabled);
      font-size: var(--font-size-sm);
    }
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
