import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MlopsApiService, User } from '../mlops-api.service';

@Component({ selector: 'app-workspace-shell', imports: [RouterLink, RouterLinkActive, RouterOutlet], templateUrl: './workspace-shell.component.html', styleUrl: './workspace-shell.component.scss' })
export class WorkspaceShellComponent implements OnInit {
  private readonly api = inject(MlopsApiService);
  private readonly router = inject(Router);
  protected readonly user = signal<User | null>(null);
  protected readonly error = signal('');
  ngOnInit(): void { this.api.me().subscribe({ next: user => this.user.set(user), error: (error: Error) => { this.api.clearToken(); this.error.set(error.message); void this.router.navigate(['/login']); } }); }
  protected signOut(): void { this.api.clearToken(); void this.router.navigate(['/login']); }
}
