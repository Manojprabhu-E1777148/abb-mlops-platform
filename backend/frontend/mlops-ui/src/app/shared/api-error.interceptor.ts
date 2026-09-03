import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';
import { MlopsApiService } from '../mlops-api.service';

export const apiErrorInterceptor: HttpInterceptorFn = (request, next) => {
  const api = inject(MlopsApiService);
  const router = inject(Router);
  const token = api.getToken();
  const authenticatedRequest = request.url.startsWith('http://localhost:8000/api') && token
    ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
    : request;

  return next(authenticatedRequest).pipe(catchError((error: HttpErrorResponse) => {
    if (error.status === 401) {
      api.clearToken();
      void router.navigate(['/login']);
    }
    return throwError(() => error);
  }));
};
