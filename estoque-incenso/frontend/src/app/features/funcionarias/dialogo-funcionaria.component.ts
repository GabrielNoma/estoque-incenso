import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatDialogModule, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-dialogo-funcionaria',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>{{ data?.nome ? 'Editar' : 'Nova' }} funcionária</h2>
    <mat-dialog-content>
      <mat-form-field appearance="outline" style="width:100%">
        <mat-label>Nome</mat-label>
        <input matInput [(ngModel)]="nome" maxlength="100" (keyup.enter)="confirmar()" />
      </mat-form-field>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancelar</button>
      <button mat-raised-button color="primary" [disabled]="!nome.trim()" (click)="confirmar()">
        Salvar
      </button>
    </mat-dialog-actions>
  `
})
export class DialogoFuncionariaComponent {
  private readonly dialogRef = inject(MatDialogRef<DialogoFuncionariaComponent>);
  readonly data = inject<{ nome: string } | null>(MAT_DIALOG_DATA, { optional: true });

  nome = this.data?.nome ?? '';

  confirmar() {
    if (this.nome.trim()) this.dialogRef.close(this.nome.trim());
  }
}
