import { TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { PedidoBotService } from './pedido-bot.service';
import { environment } from '../../../environments/environment';

describe('PedidoBotService', () => {
  let service: PedidoBotService;
  let http: HttpTestingController;
  const base = `${environment.apiUrl}/pedido-bot`;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({ imports: [HttpClientTestingModule] });
    service = TestBed.inject(PedidoBotService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('gera o id da conversa uma vez e o reaproveita', () => {
    const primeiro = service.conversaId();
    expect(primeiro.length).toBeGreaterThan(10);
    expect(service.conversaId()).toBe(primeiro);
    expect(TestBed.inject(PedidoBotService).conversaId()).toBe(primeiro);
  });

  it('envia a mensagem com conversaId e texto', () => {
    let resposta: unknown;
    service.enviarMensagem('2 dz abre caminho').subscribe(r => (resposta = r));
    const req = http.expectOne(`${base}/mensagem`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ conversaId: service.conversaId(), texto: '2 dz abre caminho' });
    req.flush({ resposta: 'ok ou não?', arquivo: null });
    expect(resposta).toEqual({ resposta: 'ok ou não?', arquivo: null });
  });

  it('monta a url absoluta de download da planilha e do modelo', () => {
    expect(service.urlDownload('/api/pedido-bot/planilha/12')).toBe(`${environment.apiUrl}/pedido-bot/planilha/12`);
    expect(service.urlModelo()).toBe(`${base}/modelo`);
  });

  it('importa o modelo com bytes brutos e nome codificado', () => {
    const arquivo = new File(['abc'], 'Modelo Novo ç.xlsx');
    service.importarModelo(arquivo).subscribe();
    const req = http.expectOne(`${base}/modelo`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toBe(arquivo);
    expect(req.request.headers.get('Content-Type')).toBe('application/octet-stream');
    expect(req.request.headers.get('X-Nome-Arquivo')).toBe(encodeURIComponent('Modelo Novo ç.xlsx'));
    req.flush({ versao: 3, arquivo: 'x', produtos: 1, adicionados: [], removidos: [], renomeados: [], apelidos_desativados: 0 });
  });

  it('carrega as informações do modelo ativo', () => {
    service.infoModelo().subscribe(i => expect(i.versao).toBe(2));
    http.expectOne(`${base}/modelo/info`).flush({ versao: 2, arquivo: 'a.xlsx', produtos: 9, ativado_em: '' });
  });
});
