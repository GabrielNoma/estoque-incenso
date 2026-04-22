import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { ProducaoService, GradeMensal, FuncionariaComRegistros, RegistroDiario, UpsertRegistroDto } from '../producao.service';
import { ExportacaoService } from '../exportacao/exportacao.service';
import { MesSelectorComponent, MesAno } from '../../../shared/components/mes-selector/mes-selector.component';
import { CelulaProducaoComponent } from '../celula-producao/celula-producao.component';
import { ResumoMensalComponent } from '../resumo-mensal/resumo-mensal.component';

@Component({
  selector: 'app-grade-producao',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MesSelectorComponent,
    CelulaProducaoComponent,
    ResumoMensalComponent
  ],
  template: `
    <div class="barra-topo">
      <app-mes-selector [valor]="mesAtual" (mudanca)="aoMudarMes($event)" />
      <button mat-raised-button color="accent" (click)="exportarExcel()">
        <mat-icon>download</mat-icon> Exportar Excel
      </button>
    </div>

    <div *ngIf="carregando()" class="spinner-container">
      <mat-spinner diameter="40" />
    </div>

    <div class="grade-wrapper" *ngIf="!carregando() && grade()">
      <table class="grade">
        <thead>
          <tr>
            <th class="col-nome">Funcionária</th>
            <th *ngFor="let dia of dias()"
                [class.fim-de-semana]="eFimDeSemana(dia)"
                class="col-dia">
              {{ dia }}
            </th>
            <th class="col-total">Total (dz)</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let func of grade()!.funcionarias">
            <td class="col-nome">{{ func.nome }}</td>
            <td *ngFor="let dia of dias()" [class.fim-de-semana]="eFimDeSemana(dia)">
              <app-celula-producao
                [funcionariaId]="func.id"
                [data]="dataStr(dia)"
                [registro]="buscarRegistro(func, dia)"
                [fimDeSemana]="eFimDeSemana(dia)"
                (salvar)="aoSalvar($event)"
                (abrirDialogoFalta)="aoAbrirFalta($event)"
                (excluir)="aoExcluir($event)"
              />
            </td>
            <td class="col-total">{{ totalFuncionaria(func) }} dz</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <td class="col-nome"><strong>TOTAL</strong></td>
            <td *ngFor="let dia of dias()" [class.fim-de-semana]="eFimDeSemana(dia)" class="total-dia">
              <strong>{{ totalDia(dia) > 0 ? totalDia(dia) + ' dz' : '' }}</strong>
            </td>
            <td class="col-total"><strong>{{ totalGeral() }} dz</strong></td>
          </tr>
        </tfoot>
      </table>
    </div>

    <app-resumo-mensal *ngIf="grade()" [grade]="grade()" />
  `,
  styles: [`
    .barra-topo { display: flex; align-items: center; justify-content: space-between; padding: 12px 0; }
    .spinner-container { display: flex; justify-content: center; padding: 40px; }
    .grade-wrapper { overflow-x: auto; }
    .grade { border-collapse: collapse; font-size: 13px; }
    .grade th, .grade td { border: 1px solid #e0e0e0; padding: 4px 6px; white-space: nowrap; }
    .grade thead th { background: #1976d2; color: white; font-weight: 600; text-align: center; }
    .grade tfoot td { background: #e3f2fd; }
    .col-nome { min-width: 140px; text-align: left; }
    .col-dia { min-width: 80px; text-align: center; }
    .col-total { min-width: 70px; text-align: center; font-weight: 600; }
    .fim-de-semana { background: #f5f5f5 !important; }
    .total-dia { text-align: center; }
  `]
})
export class GradeProducaoComponent implements OnInit {
  private readonly service = inject(ProducaoService);
  private readonly exportacao = inject(ExportacaoService);
  private readonly dialog = inject(MatDialog);

  grade = signal<GradeMensal | null>(null);
  carregando = signal(false);
  mesAtual: MesAno = { ano: new Date().getFullYear(), mes: new Date().getMonth() + 1 };

  ngOnInit() { this.carregar(); }

  carregar() {
    this.carregando.set(true);
    this.service.buscarGrade(this.mesAtual.ano, this.mesAtual.mes).subscribe({
      next: g => { this.grade.set(g); this.carregando.set(false); },
      error: () => this.carregando.set(false)
    });
  }

  aoMudarMes(mesAno: MesAno) {
    this.mesAtual = mesAno;
    this.carregar();
  }

  dias(): number[] {
    if (!this.grade()) return [];
    const { ano, mes } = this.grade()!;
    const total = new Date(ano, mes, 0).getDate();
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  dataStr(dia: number): string {
    const { ano, mes } = this.grade()!;
    return `${ano}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
  }

  eFimDeSemana(dia: number): boolean {
    const { ano, mes } = this.grade()!;
    const dow = new Date(ano, mes - 1, dia).getDay();
    return dow === 0 || dow === 6;
  }

  buscarRegistro(func: FuncionariaComRegistros, dia: number): RegistroDiario | null {
    return func.registros.find(r => r.data === this.dataStr(dia)) ?? null;
  }

  totalFuncionaria(func: FuncionariaComRegistros): number {
    return func.registros.reduce((s, r) => s + (r.falta ? 0 : (r.quantidade ?? 0)), 0);
  }

  totalDia(dia: number): number {
    return (this.grade()?.funcionarias ?? []).reduce((s, f) => {
      const r = this.buscarRegistro(f, dia);
      return s + (r && !r.falta ? (r.quantidade ?? 0) : 0);
    }, 0);
  }

  totalGeral(): number {
    return (this.grade()?.funcionarias ?? []).reduce((s, f) => s + this.totalFuncionaria(f), 0);
  }

  aoSalvar(ev: { funcionariaId: number; data: string; quantidade: number | null }) {
    const dto: UpsertRegistroDto = {
      funcionariaId: ev.funcionariaId,
      data: ev.data,
      quantidade: ev.quantidade,
      falta: false,
      motivoFalta: null,
      observacaoFalta: null
    };
    this.service.salvarOuAtualizar(dto).subscribe(() => this.carregar());
  }

  aoAbrirFalta(ev: { funcionariaId: number; data: string; registro: RegistroDiario | null }) {
    import('../dialogo-falta/dialogo-falta.component').then(m => {
      const ref = this.dialog.open(m.DialogoFaltaComponent, {
        width: '420px',
        data: { funcionariaId: ev.funcionariaId, data: ev.data, registro: ev.registro }
      });
      ref.afterClosed().subscribe(dto => {
        if (dto) this.service.salvarOuAtualizar(dto).subscribe(() => this.carregar());
      });
    });
  }

  aoExcluir(ev: { id: number }) {
    this.service.excluir(ev.id).subscribe(() => this.carregar());
  }

  exportarExcel() {
    this.exportacao.baixarExcel(this.mesAtual.ano, this.mesAtual.mes);
  }
}
