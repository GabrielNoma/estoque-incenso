import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatRadioModule } from '@angular/material/radio';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

import { RegistroDiario, UpsertRegistroDto } from '../producao.service';

interface DadosDialogo {
  funcionariaId: number;
  data: string;
  registro: RegistroDiario | null;
}

@Component({
  selector: 'app-dialogo-falta',
  standalone: true,
  imports: [
    CommonModule, FormsModule,
    MatDialogModule, MatRadioModule,
    MatFormFieldModule, MatInputModule, MatButtonModule
  ],
  template: `
    <h2 mat-dialog-title>Registrar falta — {{ data.data | date:'dd/MM/yyyy' }}</h2>
    <mat-dialog-content>
      <p><strong>Motivo</strong></p>
      <mat-radio-group [(ngModel)]="motivo" class="grupo-motivo">
        <mat-radio-button value="atestado">Atestado</mat-radio-button>
        <mat-radio-button value="falta">Falta</mat-radio-button>
        <mat-radio-button value="outro">Outro</mat-radio-button>
      </mat-radio-group>

      <mat-form-field *ngIf="motivo === 'outro'" appearance="outline" style="width:100%;margin-top:12px">
        <mat-label>Observação (obrigatória)</mat-label>
        <textarea matInput [(ngModel)]="observacao" maxlength="500" rows="3"></textarea>
        <mat-hint align="end">{{ observacao.length }}/500</mat-hint>
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-raised-button color="warn" [disabled]="!podeSalvar()" (click)="confirmar()">
        Confirmar falta
      </button>
    </mat-dialog-actions>
  `,
  styles: [`.grupo-motivo { display: flex; flex-direction: column; gap: 8px; }`]
})
export class DialogoFaltaComponent {
  private readonly dialogRef = inject(MatDialogRef<DialogoFaltaComponent>);
  readonly data = inject<DadosDialogo>(MAT_DIALOG_DATA);

  motivo = this.data.registro?.motivoFalta ?? 'falta';
  observacao = this.data.registro?.observacaoFalta ?? '';

  podeSalvar(): boolean {
    return !!this.motivo && (this.motivo !== 'outro' || this.observacao.trim().length > 0);
  }

  confirmar() {
    if (!this.podeSalvar()) return;
    const dto: UpsertRegistroDto = {
      funcionariaId: this.data.funcionariaId,
      data: this.data.data,
      quantidade: null,
      falta: true,
      motivoFalta: this.motivo,
      observacaoFalta: this.motivo === 'outro' ? this.observacao.trim() : null
    };
    this.dialogRef.close(dto);
  }
}
