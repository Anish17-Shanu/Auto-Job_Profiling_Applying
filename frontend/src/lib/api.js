const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const token = localStorage.getItem("autojob_token");
  const response = await fetch(`${API_BASE_URL}/api${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {})
    },
    ...options
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Request failed");
  }

  return response.json();
}

export async function login(email, password) {
  const data = await request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  localStorage.setItem("autojob_token", data.access_token);
  return data;
}

export const getCurrentUser = () => request("/auth/me");
export const getDashboard = () => request("/dashboard/summary");
export const listJobs = () => request("/profiles/jobs");
export const listCandidates = () => request("/profiles/candidates");
export const listRuns = () => request("/profiles/pipeline-runs");
export const getDraft = (pipelineRunId) => request(`/applications/drafts/${pipelineRunId}`);

export const createJob = (payload) =>
  request("/profiles/jobs", { method: "POST", body: JSON.stringify(payload) });

export const createCandidate = (payload) =>
  request("/profiles/candidates", { method: "POST", body: JSON.stringify(payload) });

export const createRun = (payload) =>
  request("/profiles/pipeline-runs", { method: "POST", body: JSON.stringify(payload) });

