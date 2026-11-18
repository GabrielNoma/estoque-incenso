import { AfterViewChecked, Component, ElementRef, OnInit, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpErrorResponse } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { InfoModelo, PedidoBotService, ArquivoPedido } from './pedido-bot.service';
import { DialogoConfirmarImportacaoComponent, DialogoResumoImportacaoComponent } from './dialogos-modelo.component';

interface Mensagem { autor: 'pessoa' | 'robo'; texto: string; arquivo?: ArquivoPedido | null; }

@Component({
  selector: 'app-pedido-bot',
  standalone: true,
  imports: [CommonModule, FormsModule, MatButtonModule, MatIconModule, MatFormFieldModule, MatInputModule, MatDialogModule],
  template: `
    <div class="tela">
      <div class="cabecalho">
        <h2>Pedidos</h2>
        <div class="acoes-modelo">
          <a mat-stroked-button [href]="urlModelo" download>
            <mat-icon>download</mat-icon> Exportar modelo
          </a>
          <button mat-stroked-button type="button" (click)="seletor.click()" [disabled]="importando()">
            <mat-icon>upload</mat-icon> Importar modelo
          </button>
          <input #seletor type="file" hidden accept=".xlsx" aria-label="Arquivo do novo modelo (.xlsx)"
                 (change)="aoEscolherArquivo($event)" />
        </div>
      </div>

      <p class="info-modelo" aria-live="polite">
        @if (info(); as i) {
          Modelo ativo: Versão {{ i.versao }} · {{ i.arquivo }} · {{ i.produtos }} produtos
        } @else {
          Modelo ativo: informação indisponível
        }
      </p>

      <div class="conversa" #conversa role="log" aria-live="polite" aria-label="Conversa com o robô de pedidos">
        @if (!mensagens().length) {
          <p class="vazio">Escreva o pedido em texto livre, por exemplo: 2 dz abre caminho e meia duzia de arruda.</p>
        }
        @for (m of mensagens(); track $index) {
          <div class="balao" [class.pessoa]="m.autor === 'pessoa'" [class.robo]="m.autor === 'robo'">
            <span class="texto">{{ m.texto }}</span>
            @if (m.arquivo; as a) {
              <a class="baixar-planilha" mat-stroked-button [href]="service.urlDownload(a.url)" download>
                <mat-icon>download</mat-icon> Baixar planilha
              </a>
            }
          </div>
        }
        @if (aguardando()) {
          <div class="balao robo digitando" aria-label="O robô está digitando">digitando...</div>
        }
      </div>

      <form class="entrada" (ngSubmit)="enviar()">
        <mat-form-field appearance="outline" class="campo">
          <mat-label>Mensagem</mat-label>
          <textarea matInput name="texto" rows="2" [(ngModel)]="texto" [disabled]="aguardando()"
                    (keydown.enter)="aoApertarEnter($event)" placeholder="Digite seu pedido ou responda ok"></textarea>
        </mat-form-field>
        <button mat-raised-button color="primary" type="submit" [disabled]="aguardando() || !texto.trim()">
          <mat-icon>send</mat-icon> Enviar
        </button>
      </form>
    </div>
  `,
  styleUrl: './pedido-bot.component.scss'
})
export class PedidoBotComponent implements OnInit, AfterViewChecked {
  readonly service = inject(PedidoBotService);
  private readonly dialog = inject(MatDialog);
  @ViewChild('conversa') private conversaEl?: ElementRef<HTMLElement>;

  readonly urlModelo = this.service.urlModelo();
  mensagens = signal<Mensagem[]>([]);
  aguardando = signal(false);
  importando = signal(false);
  info = signal<InfoModelo | null>(null);
  texto = '';
  private rolarParaOFim = false;

  ngOnInit() { this.carregarInfo(); }

  ngAfterViewChecked() {
    if (this.rolarParaOFim && this.conversaEl) {
      const el = this.conversaEl.nativeElement;
      el.scrollTop = el.scrollHeight;
      this.rolarParaOFim = false;
    }
  }

  aoApertarEnter(evento: Event) {
    if ((evento as KeyboardEvent).shiftKey) return; // Shift+Enter quebra linha
    evento.preventDefault();
    this.enviar();
  }

  enviar() {
    const texto = this.texto.trim();
    if (!texto || this.aguardando()) return;
    this.mensagens.update(l => [...l, { autor: 'pessoa', texto }]);
    this.texto = '';
    this.aguardando.set(true);
    this.rolarParaOFim = true;
    this.service.enviarMensagem(texto).subscribe({
      next: r => this.receber({ autor: 'robo', texto: r.resposta, arquivo: r.arquivo }),
      error: (e: HttpErrorResponse) => this.receber({
        autor: 'robo',
        texto: e.error?.error ?? 'Não foi possível enviar a mensagem. Tente novamente.'
      })
    });
  }

  private receber(m: Mensagem) {
    this.mensagens.update(l => [...l, m]);
    this.aguardando.set(false);
    this.rolarParaOFim = true;
  }

  private carregarInfo() {
    this.service.infoModelo().subscribe({ next: i => this.info.set(i), error: () => this.info.set(null) });
  }

  aoEscolherArquivo(evento: Event) {
    const input = evento.target as HTMLInputElement;
    const arquivo = input.files?.[0];
    input.value = ''; // permite escolher o mesmo arquivo de novo
    if (!arquivo) return;
    this.dialog.open(DialogoConfirmarImportacaoComponent, { data: { nomeArquivo: arquivo.name } })
      .afterClosed().subscribe(confirmou => { if (confirmou) this.importar(arquivo); });
  }

  private importar(arquivo: File) {
    this.importando.set(true);
    this.service.importarModelo(arquivo).subscribe({
      next: resultado => {
        this.importando.set(false);
        this.dialog.open(DialogoResumoImportacaoComponent, { data: { resultado } });
        this.carregarInfo();
      },
      error: (e: HttpErrorResponse) => {
        this.importando.set(false);
        const erro = e.error?.mensagem ?? e.error?.error ?? 'Não foi possível importar o modelo. Tente novamente.';
        this.dialog.open(DialogoResumoImportacaoComponent, { data: { erro } });
      }
    });
  }
}
