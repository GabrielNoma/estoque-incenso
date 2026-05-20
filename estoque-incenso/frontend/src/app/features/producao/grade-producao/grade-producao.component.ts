import { Component, ElementRef, inject, OnInit, signal } from '@angular/core';
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

    <div *ngIf="carregando() && !grade()" class="spinner-container">
      <mat-spinner diameter="40" />
    </div>

    <div class="grade-wrapper" *ngIf="grade()" [class.atualizando]="carregando()">
      <table class="grade">
        <thead>
          <tr>
            <th class="col-nome">Funcionária</th>
            <th *ngFor="let dia of dias()"
                [class.fim-de-semana]="eFimDeSemana(dia)"
                [class.dia-hoje]="eHoje(dia)"
                class="col-dia">
              <span class="dia-semana">{{ diaSemana(dia) }}</span><br><span class="num-dia">{{ dia }}</span>
            </th>
            <th class="col-total">Total (dz)</th>
          </tr>
        </thead>
        <tbody>
          <tr *ngFor="let func of grade()!.funcionarias">
            <td class="col-nome">{{ func.nome }}</td>
            <td *ngFor="let dia of dias()" [class.fim-de-semana]="eFimDeSemana(dia)" [class.dia-hoje]="eHoje(dia)">
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
            <td *ngFor="let dia of dias()" [class.fim-de-semana]="eFimDeSemana(dia)" [class.dia-hoje]="eHoje(dia)" class="total-dia">
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
    .grade-wrapper { overflow-x: auto; transition: opacity 0.25s ease; }
    .grade-wrapper.atualizando { opacity: 0.35; pointer-events: none; }
    .grade { border-collapse: collapse; font-size: 13px; }
    .grade th, .grade td { border: 1px solid #e0e0e0; padding: 4px 6px; white-space: nowrap; }
    .grade thead th { background: #1976d2; color: white; font-weight: 600; text-align: center; }
    .grade tfoot td { background: #e3f2fd; }
    .col-nome { min-width: 140px; text-align: left; position: sticky; left: 0; z-index: 2; background: white; }
    thead .col-nome { background: #1976d2; z-index: 3; }
    tfoot .col-nome { background: #e3f2fd; }
    .col-dia { min-width: 68px; text-align: center; }
    .col-total { min-width: 70px; text-align: center; font-weight: 600; }
    .fim-de-semana { background: #f5f5f5 !important; }
    .total-dia { text-align: center; }
    .dia-hoje { box-shadow: inset 0 -4px 0 0 #ff9800; }
    tbody .dia-hoje, tfoot .dia-hoje { background-color: rgba(255, 152, 0, 0.08) !important; }
    .dia-semana { font-size: 12px; font-weight: 700; letter-spacing: 0.3px; }
    .num-dia { font-size: 10px; font-weight: 400; opacity: 0.75; }
  `]
})
export class GradeProducaoComponent implements OnInit {
  private readonly service = inject(ProducaoService);
  private readonly exportacao = inject(ExportacaoService);
  private readonly dialog = inject(MatDialog);
  private readonly elementRef = inject(ElementRef);

  grade = signal<GradeMensal | null>(null);
  carregando = signal(false);
  mesAtual: MesAno = { ano: new Date().getFullYear(), mes: new Date().getMonth() + 1 };

  ngOnInit() {
    this.carregando.set(true);
    this.service.buscarGrade(this.mesAtual.ano, this.mesAtual.mes).subscribe({
      next: g => {
        this.grade.set(g);
        this.carregando.set(false);
        setTimeout(() => {
          const el = this.elementRef.nativeElement.querySelector('.dia-hoje');
          el?.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
        });
      },
      error: () => this.carregando.set(false)
    });
  }

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

  diaSemana(dia: number): string {
    const { ano, mes } = this.grade()!;
    return ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'][new Date(ano, mes - 1, dia).getDay()];
  }

  eFimDeSemana(dia: number): boolean {
    const { ano, mes } = this.grade()!;
    const dow = new Date(ano, mes - 1, dia).getDay();
    return dow === 0 || dow === 6;
  }

  private readonly _hoje = new Date();

  eHoje(dia: number): boolean {
    const g = this.grade();
    if (!g) return false;
    return g.ano === this._hoje.getFullYear() &&
           g.mes === this._hoje.getMonth() + 1 &&
           dia === this._hoje.getDate();
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
    this.patchRegistroLocal(ev.funcionariaId, ev.data, {
      quantidade: ev.quantidade, falta: false, motivoFalta: null, observacaoFalta: null
    });
    this.service.salvarOuAtualizar(dto).subscribe({
      next: s => this.patchIdLocal(ev.funcionariaId, ev.data, s.id),
      error: () => this.carregar()
    });
  }

  aoAbrirFalta(ev: { funcionariaId: number; data: string; registro: RegistroDiario | null }) {
    import('../dialogo-falta/dialogo-falta.component').then(m => {
      const ref = this.dialog.open(m.DialogoFaltaComponent, {
        width: '420px',
        data: { funcionariaId: ev.funcionariaId, data: ev.data, registro: ev.registro }
      });
      ref.afterClosed().subscribe((dto: UpsertRegistroDto | undefined) => {
        if (!dto) return;
        this.patchRegistroLocal(dto.funcionariaId, dto.data, {
          falta: dto.falta, motivoFalta: dto.motivoFalta,
          observacaoFalta: dto.observacaoFalta, quantidade: null
        });
        this.service.salvarOuAtualizar(dto).subscribe({
          next: s => this.patchIdLocal(dto.funcionariaId, dto.data, s.id),
          error: () => this.carregar()
        });
      });
    });
  }

  aoExcluir(ev: { id: number }) {
    this.removerRegistroLocal(ev.id);
    this.service.excluir(ev.id).subscribe({ error: () => this.carregar() });
  }

  private patchRegistroLocal(funcionariaId: number, data: string, patch: Partial<RegistroDiario>) {
    const g = this.grade();
    if (!g) return;
    this.grade.set({
      ...g,
      funcionarias: g.funcionarias.map(f => {
        if (f.id !== funcionariaId) return f;
        const idx = f.registros.findIndex(r => r.data === data);
        const registros = idx >= 0
          ? f.registros.map((r, i) => i === idx ? { ...r, ...patch } : r)
          : [...f.registros, { id: null, data, quantidade: null, falta: false, motivoFalta: null, observacaoFalta: null, ...patch }];
        return { ...f, registros };
      })
    });
  }

  private patchIdLocal(funcionariaId: number, data: string, id: number) {
    const g = this.grade();
    if (!g) return;
    this.grade.set({
      ...g,
      funcionarias: g.funcionarias.map(f => {
        if (f.id !== funcionariaId) return f;
        return { ...f, registros: f.registros.map(r => r.data === data ? { ...r, id } : r) };
      })
    });
  }

  private removerRegistroLocal(id: number) {
    const g = this.grade();
    if (!g) return;
    this.grade.set({
      ...g,
      funcionarias: g.funcionarias.map(f => ({ ...f, registros: f.registros.filter(r => r.id !== id) }))
    });
  }

  exportarExcel() {
    this.exportacao.baixarExcel(this.mesAtual.ano, this.mesAtual.mes);
  }
}
