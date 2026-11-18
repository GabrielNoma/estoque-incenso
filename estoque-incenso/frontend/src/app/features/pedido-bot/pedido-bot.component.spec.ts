import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule, HttpTestingController } from '@angular/common/http/testing';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { PedidoBotComponent } from './pedido-bot.component';
import { environment } from '../../../environments/environment';

describe('PedidoBotComponent', () => {
  let fixture: ComponentFixture<PedidoBotComponent>;
  let http: HttpTestingController;
  const base = `${environment.apiUrl}/pedido-bot`;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [PedidoBotComponent, HttpClientTestingModule, NoopAnimationsModule]
    }).compileComponents();
    fixture = TestBed.createComponent(PedidoBotComponent);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
    http.expectOne(`${base}/modelo/info`).flush({ versao: 2, arquivo: 'a.xlsx', produtos: 9, ativado_em: '' });
    fixture.detectChanges();
  });

  const el = () => fixture.nativeElement as HTMLElement;

  it('mostra a linha do modelo ativo', () => {
    expect(el().textContent).toContain('Versão 2');
    expect(el().textContent).toContain('9 produtos');
  });

  it('envia a mensagem, mostra "digitando..." e depois a resposta com o link da planilha', () => {
    fixture.componentInstance.texto = 'ok';
    fixture.componentInstance.enviar();
    fixture.detectChanges();
    expect(el().textContent).toContain('digitando...');
    expect(fixture.componentInstance.aguardando()).toBeTrue();

    http.expectOne(`${base}/mensagem`).flush({
      resposta: 'Pedido confirmado',
      arquivo: { nome: 'pedido-12.xlsx', url: '/api/pedido-bot/planilha/12' }
    });
    fixture.detectChanges();

    expect(el().textContent).not.toContain('digitando...');
    expect(el().textContent).toContain('Pedido confirmado');
    const link = el().querySelector('a.baixar-planilha') as HTMLAnchorElement;
    expect(link.textContent).toContain('Baixar planilha');
    expect(link.getAttribute('href')).toContain('/pedido-bot/planilha/12');
  });

  it('não envia texto vazio', () => {
    fixture.componentInstance.texto = '   ';
    fixture.componentInstance.enviar();
    http.expectNone(`${base}/mensagem`);
  });
});
