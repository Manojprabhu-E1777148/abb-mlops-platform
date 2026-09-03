import { useEffect, useState } from "react";
import type { FormEvent } from "react";

import {
  createProject,
  deleteProject,
  listProjects,
  updateProject,
} from "../api/projects";
import type { Session } from "../auth/session";
import type { Project, ProjectStatus } from "../types/projects";

interface ProjectsPageProps {
  session: Session;
  onSignOut: () => void;
}

interface ProjectFormState {
  name: string;
  description: string;
  status: ProjectStatus;
}

const initialFormState: ProjectFormState = {
  name: "",
  description: "",
  status: "draft",
};

function toFormState(project: Project): ProjectFormState {
  return {
    name: project.name,
    description: project.description,
    status: project.status,
  };
}

function canManageProject(project: Project, session: Session): boolean {
  return session.user.role === "admin" || project.owner_id === session.user.id;
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function ProjectsPage({ session, onSignOut }: ProjectsPageProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [form, setForm] = useState<ProjectFormState>(initialFormState);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [showForm, setShowForm] = useState(false);

  async function loadProjects() {
    setError(null);
    setIsLoading(true);
    try {
      const response = await listProjects();
      setProjects(response.items);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to load projects.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadProjects();
  }, []);

  function openCreateForm() {
    setEditingProject(null);
    setForm(initialFormState);
    setShowForm(true);
  }

  function openEditForm(project: Project) {
    setEditingProject(project);
    setForm(toFormState(project));
    setShowForm(true);
  }

  function closeForm() {
    setShowForm(false);
    setEditingProject(null);
    setForm(initialFormState);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSaving(true);

    try {
      if (editingProject === null) {
        const project = await createProject(form);
        setProjects((currentProjects) => [...currentProjects, project]);
      } else {
        const project = await updateProject(editingProject.id, form);
        setProjects((currentProjects) =>
          currentProjects.map((currentProject) =>
            currentProject.id === project.id ? project : currentProject,
          ),
        );
      }
      closeForm();
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to save project.");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(project: Project) {
    if (!window.confirm(`Delete ${project.name}?`)) {
      return;
    }

    setError(null);
    try {
      await deleteProject(project.id);
      setProjects((currentProjects) =>
        currentProjects.filter((currentProject) => currentProject.id !== project.id),
      );
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to delete project.");
    }
  }

  return (
    <main className="page-shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Projects</p>
          <h1>Model projects</h1>
          <p>{session.user.full_name} · {session.user.role}</p>
        </div>
        <div className="header-actions">
          <button className="secondary" onClick={onSignOut} type="button">Sign out</button>
          <button onClick={openCreateForm} type="button">Create Project</button>
        </div>
      </header>

      {error !== null && <p className="alert alert-error">{error}</p>}

      {showForm && (
        <form className="project-form" onSubmit={handleSubmit}>
          <h2>{editingProject === null ? "Create Project" : "Edit Project"}</h2>
          <label>
            Name
            <input
              minLength={3}
              required
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
            />
          </label>
          <label>
            Description
            <textarea
              minLength={10}
              required
              rows={4}
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
            />
          </label>
          <label>
            Status
            <select
              value={form.status}
              onChange={(event) => setForm({ ...form, status: event.target.value as ProjectStatus })}
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </label>
          <div className="form-actions">
            <button className="secondary" onClick={closeForm} type="button">Cancel</button>
            <button disabled={isSaving} type="submit">
              {isSaving ? "Saving..." : "Save Project"}
            </button>
          </div>
        </form>
      )}

      {isLoading ? (
        <p className="status-message">Loading projects...</p>
      ) : projects.length === 0 ? (
        <section className="empty-state">
          <h2>No projects yet</h2>
          <p>Create a project to begin managing its model lifecycle.</p>
        </section>
      ) : (
        <section className="project-table-wrapper" aria-label="Projects">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Owner</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((project) => (
                <tr key={project.id}>
                  <td>
                    <strong>{project.name}</strong>
                    <span>{project.description}</span>
                  </td>
                  <td>{project.owner.full_name}</td>
                  <td><span className={`status status-${project.status}`}>{project.status}</span></td>
                  <td>{formatDate(project.created_at)}</td>
                  <td>
                    {canManageProject(project, session) && (
                      <div className="row-actions">
                        <button className="link-button" onClick={() => openEditForm(project)} type="button">Edit</button>
                        <button className="link-button danger" onClick={() => void handleDelete(project)} type="button">Delete</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </main>
  );
}
