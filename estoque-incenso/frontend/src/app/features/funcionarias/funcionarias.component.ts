import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatTooltipModule } from '@angular/material/tooltip';

import { Funcionaria, FuncionariasService } from './funcionarias.service';
import { DialogoFuncionariaComponent } from './dialogo-funcionaria.component';

@Component({
  selector: 'app-funcionarias',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatSlideToggleModule,
    MatTooltipModule
  ],
  template: `
    <div class="cabecalho">
      <h2>Funcionárias</h2>
      <button mat-raised-button color="primary" (click)="abrirDialogoCriar()">
        <mat-icon>add</mat-icon> Nova funcionária
      </button>
    </div>

    <label class="toggle-inativas">
      <mat-slide-toggle [(ngModel)]="incluirInativas" (change)="carregar()">
        Mostrar inativas
      </mat-slide-toggle>
    </label>

    <mat-table [dataSource]="funcionarias()" class="tabela">
      <ng-container matColumnDef="nome">
        <mat-header-cell *matHeaderCellDef>Nome</mat-header-cell>
        <mat-cell *matCellDef="let f">{{ f.nome }}</mat-cell>
      </ng-container>

      <ng-container matColumnDef="status">
        <mat-header-cell *matHeaderCellDef>Status</mat-header-cell>
        <mat-cell *matCellDef="let f">
          <span [class]="f.ativa ? 'badge-ativa' : 'badge-inativa'">
            {{ f.ativa ? 'Ativa' : 'Inativa' }}
          </span>
        </mat-cell>
      </ng-container>

      <ng-container matColumnDef="acoes">
        <mat-header-cell *matHeaderCellDef>Ações</mat-header-cell>
        <mat-cell *matCellDef="let f">
          <button mat-icon-button matTooltip="Editar" (click)="abrirDialogoEditar(f)">
            <mat-icon>edit</mat-icon>
          </button>
          <button mat-icon-button [matTooltip]="f.ativa ? 'Desativar' : 'Ativar'"
                  (click)="alternarStatus(f)">
            <mat-icon>{{ f.ativa ? 'toggle_on' : 'toggle_off' }}</mat-icon>
          </button>
        </mat-cell>
      </ng-container>

      <mat-header-row *matHeaderRowDef="colunas"></mat-header-row>
      <mat-row *matRowDef="let row; columns: colunas;"></mat-row>
    </mat-table>
  `,
  styles: [`
    .cabecalho { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .toggle-inativas { display: block; margin-bottom: 16px; }
    .tabela { width: 100%; }
    .badge-ativa { color: #2e7d32; font-weight: 500; }
    .badge-inativa { color: #757575; }
  `]
})
export class FuncionariasComponent implements OnInit {
  private readonly service = inject(FuncionariasService);
  private readonly dialog = inject(MatDialog);

  funcionarias = signal<Funcionaria[]>([]);
  incluirInativas = false;
  colunas = ['nome', 'status', 'acoes'];

  ngOnInit() {
    this.carregar();
  }

  carregar() {
    this.service.listar(this.incluirInativas).subscribe(lista => this.funcionarias.set(lista));
  }

  abrirDialogoCriar() {
    const ref = this.dialog.open(DialogoFuncionariaComponent, { width: '400px' });
    ref.afterClosed().subscribe(nome => {
      if (nome) this.service.criar({ nome }).subscribe(() => this.carregar());
    });
  }

  abrirDialogoEditar(funcionaria: Funcionaria) {
    const ref = this.dialog.open(DialogoFuncionariaComponent, {
      width: '400px',
      data: { nome: funcionaria.nome }
    });
    ref.afterClosed().subscribe(nome => {
      if (nome) this.service.atualizar(funcionaria.id, { nome }).subscribe(() => this.carregar());
    });
  }

  alternarStatus(funcionaria: Funcionaria) {
    this.service.alternarStatus(funcionaria.id, !funcionaria.ativa).subscribe(() => this.carregar());
  }
}
