import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { MlopsApiService } from '../mlops-api.service';
@Component({ selector: 'app-login-page', imports: [FormsModule], templateUrl: './login-page.component.html', styleUrl: './login-page.component.scss' })
export class LoginPageComponent { private readonly api = inject(MlopsApiService); private readonly router = inject(Router); protected readonly email = signal(''); protected readonly password = signal(''); protected readonly error = signal(''); protected readonly isLoading = signal(false); protected login(): void { this.error.set(''); this.isLoading.set(true); this.api.login(this.email(), this.password()).subscribe({ next: ({ access_token }) => { this.api.saveToken(access_token); void this.router.navigate(['/models']); }, error: (error: Error) => { this.error.set(error.message); this.isLoading.set(false); } }); } }
