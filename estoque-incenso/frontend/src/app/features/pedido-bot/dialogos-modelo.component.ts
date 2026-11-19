import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { ResultadoImportacao } from './pedido-bot.service';

@Component({
  selector: 'app-dialogo-confirmar-importacao',
  standalone: true,
  imports: [MatDialogModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Importar novo modelo?</h2>
    <mat-dialog-content>
      <p>O arquivo <strong>{{ data.nomeArquivo }}</strong> vai substituir o modelo ativo
        <strong>para todas as pessoas</strong>. Os modelos anteriores continuam guardados.</p>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button [mat-dialog-close]="false">Cancelar</button>
      <button mat-raised-button color="primary" [mat-dialog-close]="true" cdkFocusInitial>Importar</button>
    </mat-dialog-actions>
  `
})
export class DialogoConfirmarImportacaoComponent {
  readonly data = inject<{ nomeArquivo: string }>(MAT_DIALOG_DATA);
}

export interface DadosResumo { resultado?: ResultadoImportacao; erro?: string; }

@Component({
  selector: 'app-dialogo-resumo-importacao',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatButtonModule],
  template: `
    @if (data.resultado; as r) {
      <h2 mat-dialog-title>Modelo importado</h2>
      <mat-dialog-content>
        <p>Versão <strong>{{ r.versao }}</strong> ativa, com <strong>{{ r.produtos }}</strong> produtos.</p>
        <p><strong>Adicionados ({{ r.adicionados.length }}):</strong> {{ lista(r.adicionados) }}</p>
        <p><strong>Removidos ({{ r.removidos.length }}):</strong> {{ lista(r.removidos) }}</p>
        <p><strong>Renomeados ({{ r.renomeados.length }}):</strong>
          @if (r.renomeados.length) {
            @for (n of r.renomeados; track n.de) { <span class="renomeado">{{ n.de }} → {{ n.para }}; </span> }
          } @else { nenhum }
        </p>
      </mat-dialog-content>
    } @else {
      <h2 mat-dialog-title>Não foi possível importar o modelo</h2>
      <mat-dialog-content>
        <p class="erro-modelo" role="alert">{{ data.erro }}</p>
        <p>O modelo ativo não foi alterado.</p>
      </mat-dialog-content>
    }
    <mat-dialog-actions align="end">
      <button mat-raised-button color="primary" mat-dialog-close cdkFocusInitial>Fechar</button>
    </mat-dialog-actions>
  `
})
export class DialogoResumoImportacaoComponent {
  readonly data = inject<DadosResumo>(MAT_DIALOG_DATA);
  lista(itens: string[]): string { return itens.length ? itens.join(', ') : 'nenhum'; }
}
