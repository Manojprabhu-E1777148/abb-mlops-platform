import { Routes } from '@angular/router';
import { DeploymentsPageComponent } from './pages/deployments-page.component';
import { LoginPageComponent } from './pages/login-page.component';
import { ModelDetailsPageComponent } from './pages/model-details-page.component';
import { ModelsPageComponent } from './pages/models-page.component';
import { MonitoringPageComponent } from './pages/monitoring-page.component';
import { authGuard } from './shared/auth.guard';
import { WorkspaceShellComponent } from './shared/workspace-shell.component';

export const routes: Routes = [{ path: 'login', component: LoginPageComponent }, { path: '', component: WorkspaceShellComponent, canActivate: [authGuard], children: [{ path: 'models', component: ModelsPageComponent }, { path: 'models/:modelId', component: ModelDetailsPageComponent }, { path: 'deployments', component: DeploymentsPageComponent }, { path: 'monitoring', component: MonitoringPageComponent }, { path: '', pathMatch: 'full', redirectTo: 'models' }] }, { path: '**', redirectTo: 'models' }];
