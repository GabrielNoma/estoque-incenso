import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'producao', pathMatch: 'full' },
  {
    path: 'producao',
    loadComponent: () => import('./features/producao/grade-producao/grade-producao.component')
      .then(m => m.GradeProducaoComponent)
  },
  {
    path: 'funcionarias',
    loadComponent: () => import('./features/funcionarias/funcionarias.component')
      .then(m => m.FuncionariasComponent)
  }
];
