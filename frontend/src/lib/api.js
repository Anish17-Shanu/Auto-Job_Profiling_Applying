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

function withQuery(path, params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "" && value !== false) {
      search.set(key, value);
    }
  });
  const query = search.toString();
  return query ? `${path}?${query}` : path;
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
export const listProviders = () => request("/profiles/providers");
export const listSources = () => request("/profiles/sources");
export const updateSourceAuth = (sourceId, payload) =>
  request(`/profiles/sources/${sourceId}/auth`, { method: "POST", body: JSON.stringify(payload) });
export const importSource = (payload) => request("/profiles/sources/import", { method: "POST", body: JSON.stringify(payload) });
export const listCandidates = () => request("/profiles/candidates");
export const createCandidate = (payload) => request("/profiles/candidates", { method: "POST", body: JSON.stringify(payload) });
export const listJobs = (params) => request(withQuery("/profiles/jobs", params));
export const listMatches = () => request("/profiles/matches");
export const generateMatches = (payload) => request("/profiles/matches/generate", { method: "POST", body: JSON.stringify(payload) });
export const setMatchApproval = (matchRunId, approved) =>
  request(`/profiles/matches/${matchRunId}/approval`, { method: "POST", body: JSON.stringify({ approved }) });
export const listApplicationTargets = () => request("/applications/targets");
export const queueApplicationTargets = (matchRunIds) =>
  request("/applications/targets/queue", { method: "POST", body: JSON.stringify({ match_run_ids: matchRunIds }) });
export const submitApplicationTargets = (applicationIds) =>
  request("/applications/targets/submit", { method: "POST", body: JSON.stringify({ application_target_ids: applicationIds }) });
