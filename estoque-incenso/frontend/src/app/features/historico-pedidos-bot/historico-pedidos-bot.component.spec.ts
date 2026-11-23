import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { HttpErrorResponse } from '@angular/common/http';
import { of, throwError } from 'rxjs';

import { HistoricoPedidosBotComponent } from './historico-pedidos-bot.component';
import { PaginaHistorico, PedidoBotService, PedidoHistorico } from '../pedido-bot/pedido-bot.service';

function pedido(id: number, estado: PedidoHistorico['estado'] = 'confirmado'): PedidoHistorico {
  return {
    id, conversa: '…0000', mensagem: `pedido ${id}`, itens: [{ nome: 'Ogum', quantidade: 0.5 }], lista: '',
    estado, resposta: estado === 'confirmado' ? 'ok' : null, criado_em: '2026-11-23T10:00:00+00:00',
    respondido_em: null, modelo_versao: 1,
    arquivo: estado === 'confirmado' ? { nome: `pedido-${id}.xlsx`, url: `/api/pedido-bot/planilha/${id}` } : null
  };
}

describe('HistoricoPedidosBotComponent', () => {
  let fixture: ComponentFixture<HistoricoPedidosBotComponent>;
  let servico: jasmine.SpyObj<PedidoBotService>;

  function criar(paginas: PaginaHistorico[]) {
    servico = jasmine.createSpyObj('PedidoBotService', ['historico', 'urlDownload']);
    servico.urlDownload.and.callFake((caminho: string) => caminho);
    servico.historico.and.returnValues(...paginas.map(p => of(p)));
    TestBed.configureTestingModule({
      imports: [HistoricoPedidosBotComponent, NoopAnimationsModule],
      providers: [{ provide: PedidoBotService, useValue: servico }]
    });
    fixture = TestBed.createComponent(HistoricoPedidosBotComponent);
    fixture.detectChanges();
  }

  it('carrega o histórico ao abrir e mostra número, estado e itens com vírgula', () => {
    criar([{ pedidos: [pedido(12), pedido(11, 'recusado')], proximo: null }]);
    const texto = fixture.nativeElement.textContent as string;
    expect(texto).toContain('Pedido 12');
    expect(texto).toContain('Confirmado');
    expect(texto).toContain('Recusado');
    expect(texto).toContain('Ogum — 0,5 dz');
    expect(servico.historico).toHaveBeenCalledWith({ limite: 50, antes: null, estado: null });
  });

  it('só mostra o botão de baixar nos confirmados', () => {
    criar([{ pedidos: [pedido(12), pedido(11, 'recusado')], proximo: null }]);
    expect(fixture.nativeElement.querySelectorAll('a[download]').length).toBe(1);
  });

  it('carregar mais usa o cursor e acrescenta à lista', () => {
    criar([{ pedidos: [pedido(12)], proximo: 12 }, { pedidos: [pedido(11)], proximo: null }]);
    fixture.componentInstance.carregarMais();
    fixture.detectChanges();
    expect(servico.historico).toHaveBeenCalledWith({ limite: 50, antes: 12, estado: null });
    expect(fixture.componentInstance.pedidos().map(p => p.id)).toEqual([12, 11]);
    expect(fixture.componentInstance.proximo()).toBeNull();
  });

  it('mudar o filtro recarrega do começo com o estado escolhido', () => {
    criar([{ pedidos: [pedido(12)], proximo: null }, { pedidos: [], proximo: null }]);
    fixture.componentInstance.estado = 'recusado';
    fixture.componentInstance.carregar();
    expect(servico.historico).toHaveBeenCalledWith({ limite: 50, antes: null, estado: 'recusado' });
    expect(fixture.componentInstance.pedidos()).toEqual([]);
  });

  it('mostra a mensagem de erro do servidor e permite tentar de novo', () => {
    servico = jasmine.createSpyObj('PedidoBotService', ['historico', 'urlDownload']);
    servico.historico.and.returnValue(throwError(() => new HttpErrorResponse({
      status: 503, error: { error: 'O serviço de pedidos não está disponível. Tente novamente em instantes.' }
    })));
    TestBed.configureTestingModule({
      imports: [HistoricoPedidosBotComponent, NoopAnimationsModule],
      providers: [{ provide: PedidoBotService, useValue: servico }]
    });
    fixture = TestBed.createComponent(HistoricoPedidosBotComponent);
    fixture.detectChanges();
    expect((fixture.nativeElement as HTMLElement).querySelector('[role=alert]')?.textContent)
      .toContain('O serviço de pedidos não está disponível');
    expect(fixture.componentInstance.carregando()).toBeFalse();
  });

  it('mostra o estado vazio quando não há pedidos', () => {
    criar([{ pedidos: [], proximo: null }]);
    expect(fixture.nativeElement.textContent).toContain('Nenhum pedido encontrado.');
  });

  it('formata quantidades com vírgula e sem zeros à direita', () => {
    criar([{ pedidos: [], proximo: null }]);
    expect(fixture.componentInstance.quantidade(2)).toBe('2');
    expect(fixture.componentInstance.quantidade(0.5)).toBe('0,5');
    expect(fixture.componentInstance.quantidade(2.25)).toBe('2,25');
  });
});
