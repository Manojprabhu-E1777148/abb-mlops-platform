import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { catchError, Observable, throwError } from 'rxjs';

export interface User { id: string; email: string; full_name: string; role: 'admin' | 'member'; }
export interface Model { id: string; name: string; description: string; tags: string[]; metadata: Record<string, unknown>; created_at: string; updated_at: string; }
export interface ModelVersion { id: string; version: string; framework: string; algorithm: string; approval_status: string; lifecycle_stage: string; }
export interface Deployment { id: string; model_version_id: string; environment: string; status: string; events: { status: string; message: string; created_at: string }[]; }
export interface Metric { prediction_latency_ms: number; throughput_per_minute: number; error_rate: number; quality_score: number; drift_score: number; availability: number; last_successful_inference_at: string; monitoring_status: string; }
export interface ModelCreateRequest { name: string; description: string; tags?: string[]; metadata?: Record<string, unknown>; }
export interface ModelVersionCreateRequest { version: string; description?: string; framework: string; algorithm: string; artifact_uri: string; training_data_reference: string; tags?: string[]; metadata?: Record<string, unknown>; }

@Injectable({ providedIn: 'root' })
export class MlopsApiService {
  private readonly baseUrl = 'http://localhost:8000/api';
  private token: string | null = localStorage.getItem('mlops-token');

  constructor(private readonly http: HttpClient) {}

  login(email: string, password: string) {
    const body = new HttpParams().set('username', email).set('password', password);
    return this.http.post<{ access_token: string }>(`${this.baseUrl}/auth/login`, body, { headers: new HttpHeaders({ 'Content-Type': 'application/x-www-form-urlencoded' }) });
  }

  me() { return this.request<User>('GET', '/auth/me'); }
  hasToken() { return this.token !== null; }
  getToken() { return this.token; }
  models() { return this.request<Model[]>('GET', '/models'); }
  model(modelId: string) { return this.request<Model>('GET', `/models/${modelId}`); }
  versions(modelId: string) { return this.request<ModelVersion[]>('GET', `/models/${modelId}/versions`); }
  deployments() { return this.request<Deployment[]>('GET', '/deployments'); }
  metrics(modelId: string) { return this.request<Metric>('GET', `/models/${modelId}/metrics`); }
  createModel(body: ModelCreateRequest) { return this.request<Model>('POST', '/models', body); }
  updateModel(modelId: string, body: { name: string; description: string }) { return this.request<Model>('PATCH', `/models/${modelId}`, body); }
  deleteModel(modelId: string) { return this.request<void>('DELETE', `/models/${modelId}`); }
  createVersion(modelId: string, body: ModelVersionCreateRequest) { return this.request<ModelVersion>('POST', `/models/${modelId}/versions`, body); }
  approve(modelId: string, versionId: string) { return this.request<ModelVersion>('PATCH', `/models/${modelId}/versions/${versionId}/approval`, { approval_status: 'APPROVED' }); }
  deploy(modelVersionId: string, environment: string, simulate_failure: boolean) { return this.request<Deployment>('POST', '/deployments', { model_version_id: modelVersionId, environment, simulate_failure }, { 'Idempotency-Key': crypto.randomUUID() }); }
  retry(id: string) { return this.request<Deployment>('POST', `/deployments/${id}/retry`); }
  rollback(id: string) { return this.request<Deployment>('POST', `/deployments/${id}/rollback`); }

  saveToken(token: string) { this.token = token; localStorage.setItem('mlops-token', token); }
  clearToken() { this.token = null; localStorage.removeItem('mlops-token'); }

  private request<T>(method: string, path: string, body?: object, headers: Record<string, string> = {}): Observable<T> {
    const requestHeaders: Record<string, string> = { ...headers };
    if (this.token) requestHeaders['Authorization'] = `Bearer ${this.token}`;
    return this.http.request<T>(method, `${this.baseUrl}${path}`, { body, headers: requestHeaders, responseType: 'json' }).pipe(catchError((error) => throwError(() => new Error(error.error?.error?.message ?? 'The request could not be completed.')))) as Observable<T>;
  }
}
