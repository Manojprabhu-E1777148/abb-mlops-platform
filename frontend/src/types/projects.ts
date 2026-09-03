import type { UserRole } from "./auth";

export type ProjectStatus = "draft" | "active" | "archived";

export interface ProjectOwner {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface Project {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  owner: ProjectOwner;
  status: ProjectStatus;
  created_at: string;
}

export interface ProjectList {
  items: Project[];
  count: number;
}

export interface CreateProjectRequest {
  name: string;
  description: string;
  status?: ProjectStatus;
  owner_id?: string;
}

export interface UpdateProjectRequest {
  name?: string;
  description?: string;
  status?: ProjectStatus;
  owner_id?: string;
}
