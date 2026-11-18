import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpContext } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SEM_AVISO_DE_ERRO } from '../../shared/interceptors/error.interceptor';

export interface ArquivoPedido { nome: string; url: string; }
export interface RespostaBot { resposta: string; arquivo: ArquivoPedido | null; }
export interface InfoModelo { versao: number; arquivo: string; produtos: number; ativado_em: string; }
export interface ResultadoImportacao {
  versao: number;
  arquivo: string;
  produtos: number;
  adicionados: string[];
  removidos: string[];
  renomeados: { de: string; para: string }[];
  apelidos_desativados: number;
}

const CHAVE_CONVERSA = 'pedido-bot-conversa-id';

@Injectable({ providedIn: 'root' })
export class PedidoBotService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/pedido-bot`;
  private idEmMemoria: string | null = null;

  /** Identificador anônimo desta pessoa/navegador; cada um tem seu próprio pedido pendente. */
  conversaId(): string {
    if (this.idEmMemoria) return this.idEmMemoria;
    let id: string | null = null;
    try { id = localStorage.getItem(CHAVE_CONVERSA); } catch { /* armazenamento indisponível */ }
    if (!id) {
      id = crypto.randomUUID();
      try { localStorage.setItem(CHAVE_CONVERSA, id); } catch { /* segue só em memória */ }
    }
    this.idEmMemoria = id;
    return id;
  }

  enviarMensagem(texto: string): Observable<RespostaBot> {
    return this.http.post<RespostaBot>(`${this.url}/mensagem`, { conversaId: this.conversaId(), texto });
  }

  /** Transforma "/api/pedido-bot/..." (devolvido pelo backend) em URL utilizável pelo navegador. */
  urlDownload(caminhoApi: string): string {
    return `${environment.apiUrl}${caminhoApi.replace(/^\/api/, '')}`;
  }

  urlModelo(): string {
    return `${this.url}/modelo`;
  }

  infoModelo(): Observable<InfoModelo> {
    return this.http.get<InfoModelo>(`${this.url}/modelo/info`, {
      context: new HttpContext().set(SEM_AVISO_DE_ERRO, true)
    });
  }

  /** Envia os bytes do .xlsx como estão; o erro do robô é mostrado pela própria tela. */
  importarModelo(arquivo: File): Observable<ResultadoImportacao> {
    return this.http.post<ResultadoImportacao>(`${this.url}/modelo`, arquivo, {
      headers: {
        'Content-Type': 'application/octet-stream',
        'X-Nome-Arquivo': encodeURIComponent(arquivo.name)
      },
      context: new HttpContext().set(SEM_AVISO_DE_ERRO, true)
    });
  }
}
