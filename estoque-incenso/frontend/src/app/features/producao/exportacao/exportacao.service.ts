import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ExportacaoService {
  private readonly http = inject(HttpClient);

  baixarExcel(ano: number, mes: number): void {
    this.http
      .get(`${environment.apiUrl}/exportacao/excel`, {
        params: { ano, mes },
        responseType: 'blob'
      })
      .subscribe(blob => {
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `producao_${ano}_${String(mes).padStart(2, '0')}.xlsx`;
        link.click();
        URL.revokeObjectURL(url);
      });
  }
}
