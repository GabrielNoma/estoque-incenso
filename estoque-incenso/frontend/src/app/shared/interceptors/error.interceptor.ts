import { HttpInterceptorFn, HttpErrorResponse, HttpContextToken } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, throwError } from 'rxjs';

/** Requisições que exibem o próprio erro na tela (ex.: mensagem do robô) marcam isto como true. */
export const SEM_AVISO_DE_ERRO = new HttpContextToken<boolean>(() => false);

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const snackBar = inject(MatSnackBar);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (req.context.get(SEM_AVISO_DE_ERRO)) return throwError(() => error);
      const mensagem = error.error?.error ?? mensagemPadrao(error.status);
      snackBar.open(mensagem, 'Fechar', { duration: 5000 });
      return throwError(() => error);
    })
  );
};

function mensagemPadrao(status: number): string {
  switch (status) {
    case 400: return 'Dados inválidos. Verifique as informações e tente novamente.';
    case 404: return 'Registro não encontrado.';
    case 0:   return 'Sem conexão com o servidor.';
    default:  return 'Ocorreu um erro inesperado. Tente novamente.';
  }
}
