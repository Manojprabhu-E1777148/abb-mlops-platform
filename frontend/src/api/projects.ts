import { apiRequest } from "./client";
import type {
  CreateProjectRequest,
  Project,
  ProjectList,
  UpdateProjectRequest,
} from "../types/projects";

export function listProjects(): Promise<ProjectList> {
  return apiRequest<ProjectList>("/api/projects");
}

export function getProject(projectId: string): Promise<Project> {
  return apiRequest<Project>(`/api/projects/${projectId}`);
}

export function createProject(data: CreateProjectRequest): Promise<Project> {
  return apiRequest<Project>("/api/projects", {
    method: "POST",
    body: data,
  });
}

export function updateProject(
  projectId: string,
  data: UpdateProjectRequest,
): Promise<Project> {
  return apiRequest<Project>(`/api/projects/${projectId}`, {
    method: "PATCH",
    body: data,
  });
}

export function deleteProject(projectId: string): Promise<void> {
  return apiRequest<void>(`/api/projects/${projectId}`, {
    method: "DELETE",
  });
}
