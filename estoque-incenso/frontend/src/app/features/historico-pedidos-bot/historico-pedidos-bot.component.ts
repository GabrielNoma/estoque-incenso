import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';

import { EstadoPedido, PedidoBotService, PedidoHistorico } from '../pedido-bot/pedido-bot.service';

const POR_PAGINA = 50;
const ROTULOS: Record<EstadoPedido, string> = {
  aguardando: 'Aguardando',
  confirmado: 'Confirmado',
  recusado: 'Recusado',
  substituido: 'Substituído'
};

@Component({
  selector: 'app-historico-pedidos-bot',
  standalone: true,
  imports: [CommonModule, FormsModule, MatButtonModule, MatIconModule, MatFormFieldModule, MatSelectModule],
  template: `
    <div class="tela">
      <div class="cabecalho">
        <h2>Histórico de pedidos bot</h2>
        <div class="acoes">
          <mat-form-field appearance="outline" class="filtro" subscriptSizing="dynamic">
            <mat-label>Estado</mat-label>
            <mat-select [(ngModel)]="estado" (ngModelChange)="carregar()" aria-label="Filtrar por estado">
              <mat-option [value]="null">Todos</mat-option>
              @for (e of estados; track e) {
                <mat-option [value]="e">{{ rotulo(e) }}</mat-option>
              }
            </mat-select>
          </mat-form-field>
          <button mat-stroked-button type="button" (click)="carregar()" [disabled]="carregando()">
            <mat-icon>refresh</mat-icon> Atualizar
          </button>
        </div>
      </div>

      <p class="resumo" aria-live="polite">
        @if (carregando() && !pedidos().length) { Carregando... }
        @else if (erro()) { }
        @else { {{ pedidos().length }} {{ pedidos().length === 1 ? 'pedido' : 'pedidos' }} exibidos }
      </p>

      @if (erro(); as mensagem) {
        <div class="erro" role="alert">
          <span>{{ mensagem }}</span>
          <button mat-stroked-button type="button" (click)="carregar()">Tentar de novo</button>
        </div>
      }

      @if (!erro() && !carregando() && !pedidos().length) {
        <p class="vazio">Nenhum pedido encontrado.</p>
      }

      <div class="lista" role="list">
        @for (p of pedidos(); track p.id) {
          <article class="cartao" role="listitem">
            <header class="topo">
              <span class="numero">Pedido {{ p.id }}</span>
              <span class="selo" [ngClass]="'estado-' + p.estado">{{ rotulo(p.estado) }}</span>
              <span class="quando">{{ quando(p.criado_em) }}</span>
              <span class="conversa" title="Final do identificador da conversa">Conversa {{ p.conversa }}</span>
            </header>

            <p class="mensagem">{{ p.mensagem }}</p>

            <ul class="itens" aria-label="Itens do pedido">
              @for (i of p.itens; track $index) {
                <li>{{ i.nome }} — {{ quantidade(i.quantidade) }} dz</li>
              }
            </ul>

            <footer class="rodape">
              @if (p.resposta) {
                <span class="resposta">Resposta: {{ p.resposta }}@if (p.respondido_em) { · {{ quando(p.respondido_em) }} }</span>
              } @else {
                <span class="resposta">Sem resposta ainda</span>
              }
              @if (p.arquivo; as a) {
                <a mat-stroked-button [href]="service.urlDownload(a.url)" download>
                  <mat-icon>download</mat-icon> Baixar planilha
                </a>
              }
            </footer>
          </article>
        }
      </div>

      @if (proximo() !== null) {
        <div class="mais">
          <button mat-stroked-button type="button" (click)="carregarMais()" [disabled]="carregando()">
            Carregar mais
          </button>
        </div>
      }
    </div>
  `,
  styleUrl: './historico-pedidos-bot.component.scss'
})
export class HistoricoPedidosBotComponent implements OnInit {
  readonly service = inject(PedidoBotService);

  readonly estados: EstadoPedido[] = ['aguardando', 'confirmado', 'recusado', 'substituido'];
  estado: EstadoPedido | null = null;

  readonly pedidos = signal<PedidoHistorico[]>([]);
  readonly proximo = signal<number | null>(null);
  readonly carregando = signal(false);
  readonly erro = signal<string | null>(null);

  ngOnInit(): void { this.carregar(); }

  rotulo(estado: EstadoPedido): string { return ROTULOS[estado] ?? estado; }

  /** 2 → "2", 0.5 → "0,5" (vírgula, sem zeros à direita). */
  quantidade(valor: number): string { return String(valor).replace('.', ','); }

  quando(iso: string): string {
    const data = new Date(iso);
    return Number.isNaN(data.getTime()) ? iso
      : data.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' });
  }

  /** Recarrega do começo (filtro novo ou botão Atualizar). */
  carregar(): void {
    this.buscar(null, true);
  }

  carregarMais(): void {
    const cursor = this.proximo();
    if (cursor !== null) this.buscar(cursor, false);
  }

  private buscar(antes: number | null, recomecar: boolean): void {
    this.carregando.set(true);
    this.erro.set(null);
    this.service.historico({ limite: POR_PAGINA, antes, estado: this.estado }).subscribe({
      next: pagina => {
        this.pedidos.set(recomecar ? pagina.pedidos : [...this.pedidos(), ...pagina.pedidos]);
        this.proximo.set(pagina.proximo);
        this.carregando.set(false);
      },
      error: (falha: HttpErrorResponse) => {
        this.erro.set(falha.error?.error ?? 'Não foi possível carregar o histórico. Tente de novo.');
        this.carregando.set(false);
      }
    });
  }
}
