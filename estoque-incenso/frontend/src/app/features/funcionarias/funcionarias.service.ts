import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Funcionaria {
  id: number;
  nome: string;
  ativa: boolean;
}

export interface CriarFuncionariaDto {
  nome: string;
}

export interface AtualizarFuncionariaDto {
  nome: string;
}

@Injectable({ providedIn: 'root' })
export class FuncionariasService {
  private readonly http = inject(HttpClient);
  private readonly url = `${environment.apiUrl}/funcionarias`;

  listar(incluirInativas = false): Observable<Funcionaria[]> {
    return this.http.get<Funcionaria[]>(this.url, {
      params: { incluirInativas: String(incluirInativas) }
    });
  }

  criar(dto: CriarFuncionariaDto): Observable<Funcionaria> {
    return this.http.post<Funcionaria>(this.url, dto);
  }

  atualizar(id: number, dto: AtualizarFuncionariaDto): Observable<Funcionaria> {
    return this.http.put<Funcionaria>(`${this.url}/${id}`, dto);
  }

  alternarStatus(id: number, ativa: boolean): Observable<void> {
    return this.http.patch<void>(`${this.url}/${id}/status`, { ativa });
  }
}
