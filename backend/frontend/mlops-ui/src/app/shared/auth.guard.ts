import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { MlopsApiService } from '../mlops-api.service';

export const authGuard: CanActivateFn = () => {
  const api = inject(MlopsApiService);
  const router = inject(Router);
  return api.hasToken() ? true : router.createUrlTree(['/login']);
};
