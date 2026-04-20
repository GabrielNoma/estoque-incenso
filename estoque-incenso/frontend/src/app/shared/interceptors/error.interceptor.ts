import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { catchError, throwError } from 'rxjs';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const snackBar = inject(MatSnackBar);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      const mensagem = error.error?.erro ?? mensagemPadrao(error.status);
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
