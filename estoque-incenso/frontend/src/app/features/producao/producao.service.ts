import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface RegistroDiario {
  id: number | null;
  data: string;
  quantidade: number | null;
  falta: boolean;
  motivoFalta: string | null;
  observacaoFalta: string | null;
}

export interface FuncionariaComRegistros {
  id: number;
  nome: string;
  ativa: boolean;
  registros: RegistroDiario[];
}

export interface GradeMensal {
  ano: number;
  mes: number;
  funcionarias: FuncionariaComRegistros[];
}

export interface UpsertRegistroDto {
  funcionariaId: number;
  data: string;
  quantidade: number | null;
  falta: boolean;
  motivoFalta: string | null;
  observacaoFalta: string | null;
}

export interface RegistroSalvo {
  id: number;
  funcionariaId: number;
  data: string;
  quantidade: number | null;
  falta: boolean;
  motivoFalta: string | null;
  observacaoFalta: string | null;
}

@Injectable({ providedIn: 'root' })
export class ProducaoService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/registros`;

  buscarGrade(ano: number, mes: number): Observable<GradeMensal> {
    return this.http.get<GradeMensal>(this.url, { params: { ano, mes } });
  }

  salvarOuAtualizar(dto: UpsertRegistroDto): Observable<RegistroSalvo> {
    return this.http.put<RegistroSalvo>(this.url, dto);
  }

  excluir(id: number): Observable<void> {
    return this.http.delete<void>(`${this.url}/${id}`);
  }
}
