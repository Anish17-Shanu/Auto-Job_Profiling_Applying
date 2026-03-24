import { useEffect, useState } from "react";
import { SectionCard } from "./components/SectionCard";
import { StatCard } from "./components/StatCard";
import {
  createCandidate,
  generateMatches,
  getCurrentUser,
  getDashboard,
  importSource,
  listApplicationTargets,
  listCandidates,
  listJobs,
  listMatches,
  listProviders,
  listSources,
  login,
  queueApplicationTargets,
  setMatchApproval,
  submitApplicationTargets,
  updateSourceAuth
} from "./lib/api";

const defaultCandidate = {
  full_name: "",
  email: "",
  years_experience: 0,
  target_role: "",
  skills: "",
  summary: "",
  resume_text: ""
};

const defaultImportForm = {
  provider: "greenhouse",
  board_token: "",
  company_slug: "",
  keywords: "",
  location: "",
  country: "us",
  api_key: "",
  user_agent: "",
  app_id: "",
  app_key: "",
  limit: 20
};

export default function App() {
  const [tokenReady, setTokenReady] = useState(Boolean(localStorage.getItem("autojob_token")));
  const [user, setUser] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [providers, setProviders] = useState([]);
  const [sources, setSources] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [matches, setMatches] = useState([]);
  const [applications, setApplications] = useState([]);
  const [selectedCandidateId, setSelectedCandidateId] = useState("");
  const [selectedJobs, setSelectedJobs] = useState([]);
  const [selectedMatches, setSelectedMatches] = useState([]);
  const [selectedApplications, setSelectedApplications] = useState([]);
  const [error, setError] = useState("");
  const [candidateForm, setCandidateForm] = useState(defaultCandidate);
  const [importForm, setImportForm] = useState(defaultImportForm);
  const [filters, setFilters] = useState({ query: "", provider: "", location: "", remote_only: false });
  const [sourceKeys, setSourceKeys] = useState({});

  async function refreshWorkspace(candidateId = selectedCandidateId) {
    try {
      const [me, dashboardData, providerData, sourceData, candidateData, matchData, applicationData] = await Promise.all([
        getCurrentUser(),
        getDashboard(),
        listProviders(),
        listSources(),
        listCandidates(),
        listMatches(),
        listApplicationTargets()
      ]);
      const effectiveCandidateId = candidateId || candidateData[0]?.id || "";
      const jobsData = await listJobs({ ...filters, candidate_profile_id: effectiveCandidateId || undefined });

      setUser(me);
      setDashboard(dashboardData);
      setProviders(providerData);
      setSources(sourceData);
      setCandidates(candidateData);
      setMatches(matchData);
      setApplications(applicationData);
      setJobs(jobsData.items);
      setSelectedCandidateId(effectiveCandidateId);
      setError("");
    } catch (err) {
      setError(err.message);
      localStorage.removeItem("autojob_token");
      setTokenReady(false);
    }
  }

  useEffect(() => {
    if (tokenReady) {
      refreshWorkspace();
    }
  }, [tokenReady]);

  async function refreshJobs(candidateId = selectedCandidateId) {
    try {
      const jobsData = await listJobs({ ...filters, candidate_profile_id: candidateId || undefined });
      setJobs(jobsData.items);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleLogin(event) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    try {
      await login(formData.get("email"), formData.get("password"));
      setTokenReady(true);
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleCreateCandidate(event) {
    event.preventDefault();
    try {
      await createCandidate({
        ...candidateForm,
        years_experience: Number(candidateForm.years_experience),
        skills: splitCsv(candidateForm.skills)
      });
      setCandidateForm(defaultCandidate);
      await refreshWorkspace();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleImport(event) {
    event.preventDefault();
    try {
      await importSource({
        ...importForm,
        limit: Number(importForm.limit)
      });
      await refreshWorkspace();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleGenerateMatches() {
    try {
      await generateMatches({
        candidate_profile_id: Number(selectedCandidateId),
        external_job_ids: selectedJobs
      });
      setSelectedJobs([]);
      await refreshWorkspace();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleApprove(matchRunId, approved) {
    try {
      await setMatchApproval(matchRunId, approved);
      await refreshWorkspace();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleQueueApplications() {
    try {
      await queueApplicationTargets(selectedMatches);
      setSelectedMatches([]);
      await refreshWorkspace();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSubmitApplications() {
    try {
      await submitApplicationTargets(selectedApplications);
      setSelectedApplications([]);
      await refreshWorkspace();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSaveProviderAuth(sourceId, payload) {
    try {
      await updateSourceAuth(sourceId, payload);
      await refreshWorkspace();
    } catch (err) {
      setError(err.message);
    }
  }

  if (!tokenReady) {
    return (
      <div className="auth-shell">
        <form className="auth-card" onSubmit={handleLogin}>
          <p className="eyebrow">AI Talent Operations</p>
          <h1>Auto-Job Portal Copilot</h1>
          <p className="subtle">Import real jobs, rank them, tailor resumes per role, approve, and then push selected applications through the safest available apply path.</p>
          <label>
            Email
            <input name="email" type="email" defaultValue="admin@autojobdemo.com" required />
          </label>
          <label>
            Password
            <input name="password" type="password" defaultValue="ChangeMe123!" required />
          </label>
          <button type="submit">Access Workspace</button>
          {error ? <div className="error-banner">{error}</div> : null}
        </form>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="eyebrow">External Job Automation Workspace</p>
          <h1>Auto-Job Portal Copilot</h1>
          <p className="subtle">{user ? `${user.full_name} · ${user.organization.name}` : "Loading workspace..."}</p>
        </div>
        <button
          className="secondary"
          onClick={() => {
            localStorage.removeItem("autojob_token");
            setTokenReady(false);
          }}
        >
          Sign Out
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <div className="stats-grid">
        <StatCard label="Imported Jobs" value={dashboard?.imported_jobs ?? 0} accent="#0d9488" />
        <StatCard label="Tailored Resumes" value={dashboard?.tailored_resumes ?? 0} accent="#2563eb" />
        <StatCard label="Approved Resumes" value={dashboard?.approved_resumes ?? 0} accent="#dc2626" />
        <StatCard label="Submitted Apps" value={dashboard?.submitted_applications ?? 0} accent="#ca8a04" />
      </div>

      <div className="content-grid">
        <SectionCard title="Import From Real Portals">
          <form className="form-grid" onSubmit={handleImport}>
            <select value={importForm.provider} onChange={(e) => setImportForm({ ...importForm, provider: e.target.value })}>
              {providers.map((provider) => (
                <option key={provider.provider} value={provider.provider}>{provider.label}</option>
              ))}
            </select>
            {importForm.provider === "greenhouse" ? (
              <input
                placeholder="Greenhouse board token, e.g. stripe"
                value={importForm.board_token}
                onChange={(e) => setImportForm({ ...importForm, board_token: e.target.value })}
                required
              />
            ) : null}
            {importForm.provider === "lever" ? (
              <input
                placeholder="Lever company slug"
                value={importForm.company_slug}
                onChange={(e) => setImportForm({ ...importForm, company_slug: e.target.value })}
                required
              />
            ) : null}
            {importForm.provider === "remotive" ? (
              <input
                placeholder="Search keywords"
                value={importForm.keywords}
                onChange={(e) => setImportForm({ ...importForm, keywords: e.target.value })}
              />
            ) : null}
            {importForm.provider === "adzuna" ? (
              <>
                <input
                  placeholder="Adzuna keywords"
                  value={importForm.keywords}
                  onChange={(e) => setImportForm({ ...importForm, keywords: e.target.value })}
                />
                <input
                  placeholder="Country code, e.g. us, gb, in"
                  value={importForm.country}
                  onChange={(e) => setImportForm({ ...importForm, country: e.target.value })}
                />
                <input
                  placeholder="Adzuna app_id"
                  value={importForm.app_id}
                  onChange={(e) => setImportForm({ ...importForm, app_id: e.target.value })}
                  required
                />
                <input
                  type="password"
                  placeholder="Adzuna app_key"
                  value={importForm.app_key}
                  onChange={(e) => setImportForm({ ...importForm, app_key: e.target.value })}
                  required
                />
              </>
            ) : null}
            {importForm.provider === "usajobs" ? (
              <>
                <input
                  placeholder="USAJOBS keywords"
                  value={importForm.keywords}
                  onChange={(e) => setImportForm({ ...importForm, keywords: e.target.value })}
                />
                <input
                  placeholder="USAJOBS API key"
                  value={importForm.api_key}
                  onChange={(e) => setImportForm({ ...importForm, api_key: e.target.value })}
                  required
                />
                <input
                  placeholder="Request email / User-Agent"
                  value={importForm.user_agent}
                  onChange={(e) => setImportForm({ ...importForm, user_agent: e.target.value })}
                  required
                />
              </>
            ) : null}
            <input
              placeholder="Optional location filter"
              value={importForm.location}
              onChange={(e) => setImportForm({ ...importForm, location: e.target.value })}
            />
            <input
              type="number"
              min="1"
              max="100"
              value={importForm.limit}
              onChange={(e) => setImportForm({ ...importForm, limit: e.target.value })}
            />
            <button type="submit">Import Jobs</button>
          </form>
          <div className="list-stack">
            {providers.map((provider) => (
              <article key={provider.provider} className="list-item">
                <h3>{provider.label}</h3>
                <p className="subtle">{provider.ingestion_support}</p>
                <p className="subtle">{provider.apply_support}</p>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Base Candidate Profile">
          <form className="form-grid" onSubmit={handleCreateCandidate}>
            <input placeholder="Full name" value={candidateForm.full_name} onChange={(e) => setCandidateForm({ ...candidateForm, full_name: e.target.value })} required />
            <input placeholder="Email" value={candidateForm.email} onChange={(e) => setCandidateForm({ ...candidateForm, email: e.target.value })} required />
            <input placeholder="Target role" value={candidateForm.target_role} onChange={(e) => setCandidateForm({ ...candidateForm, target_role: e.target.value })} required />
            <input type="number" placeholder="Years of experience" value={candidateForm.years_experience} onChange={(e) => setCandidateForm({ ...candidateForm, years_experience: e.target.value })} />
            <input placeholder="Skills (comma separated)" value={candidateForm.skills} onChange={(e) => setCandidateForm({ ...candidateForm, skills: e.target.value })} />
            <textarea placeholder="Professional summary" value={candidateForm.summary} onChange={(e) => setCandidateForm({ ...candidateForm, summary: e.target.value })} required />
            <textarea placeholder="Base resume text" value={candidateForm.resume_text} onChange={(e) => setCandidateForm({ ...candidateForm, resume_text: e.target.value })} required />
            <button type="submit">Save Candidate</button>
          </form>
          <select value={selectedCandidateId} onChange={async (e) => {
            setSelectedCandidateId(e.target.value);
            await refreshJobs(e.target.value);
          }}>
            <option value="">Choose scoring candidate</option>
            {candidates.map((candidate) => (
              <option key={candidate.id} value={candidate.id}>{candidate.full_name} · {candidate.target_role}</option>
            ))}
          </select>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Connected Sources">
          <div className="list-stack">
            {sources.map((source) => (
              <article key={source.id} className="list-item">
                <h3>{source.label}</h3>
                <p>{source.provider} · {source.supports_direct_apply ? "Direct apply-capable" : "Assisted apply"}</p>
                <p className="subtle">Last sync: {source.last_synced_at ? new Date(source.last_synced_at).toLocaleString() : "Not synced yet"}</p>
                <p className="subtle">Credentials: {source.has_auth_config ? "configured" : "not configured"}</p>
                {source.provider === "greenhouse" ? (
                  <div className="form-grid">
                    <input
                      type="password"
                      placeholder="Optional Greenhouse Job Board API key for direct apply"
                      value={sourceKeys[`api_key_${source.id}`] ?? ""}
                      onChange={(e) => setSourceKeys({ ...sourceKeys, [`api_key_${source.id}`]: e.target.value })}
                    />
                    <button
                      type="button"
                      className="secondary"
                      onClick={() => handleSaveProviderAuth(source.id, { api_key: sourceKeys[`api_key_${source.id}`] || "" })}
                    >
                      Save Portal Credential
                    </button>
                  </div>
                ) : null}
                {source.provider === "adzuna" ? (
                  <div className="form-grid">
                    <input
                      placeholder="Adzuna app_id"
                      value={sourceKeys[`app_id_${source.id}`] ?? ""}
                      onChange={(e) => setSourceKeys({ ...sourceKeys, [`app_id_${source.id}`]: e.target.value })}
                    />
                    <input
                      type="password"
                      placeholder="Adzuna app_key"
                      value={sourceKeys[`app_key_${source.id}`] ?? ""}
                      onChange={(e) => setSourceKeys({ ...sourceKeys, [`app_key_${source.id}`]: e.target.value })}
                    />
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        handleSaveProviderAuth(source.id, {
                          app_id: sourceKeys[`app_id_${source.id}`] || "",
                          app_key: sourceKeys[`app_key_${source.id}`] || ""
                        })}
                    >
                      Save Portal Credential
                    </button>
                  </div>
                ) : null}
                {source.provider === "usajobs" ? (
                  <div className="form-grid">
                    <input
                      placeholder="USAJOBS API key"
                      value={sourceKeys[`api_key_${source.id}`] ?? ""}
                      onChange={(e) => setSourceKeys({ ...sourceKeys, [`api_key_${source.id}`]: e.target.value })}
                    />
                    <input
                      placeholder="USAJOBS request email / User-Agent"
                      value={sourceKeys[`user_agent_${source.id}`] ?? ""}
                      onChange={(e) => setSourceKeys({ ...sourceKeys, [`user_agent_${source.id}`]: e.target.value })}
                    />
                    <button
                      type="button"
                      className="secondary"
                      onClick={() =>
                        handleSaveProviderAuth(source.id, {
                          api_key: sourceKeys[`api_key_${source.id}`] || "",
                          user_agent: sourceKeys[`user_agent_${source.id}`] || ""
                        })}
                    >
                      Save Portal Credential
                    </button>
                  </div>
                ) : null}
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Job Filters">
          <div className="form-grid">
            <input placeholder="Search title, company, description" value={filters.query} onChange={(e) => setFilters({ ...filters, query: e.target.value })} />
            <select value={filters.provider} onChange={(e) => setFilters({ ...filters, provider: e.target.value })}>
              <option value="">All providers</option>
              {providers.map((provider) => (
                <option key={provider.provider} value={provider.provider}>{provider.provider}</option>
              ))}
            </select>
            <input placeholder="Location contains" value={filters.location} onChange={(e) => setFilters({ ...filters, location: e.target.value })} />
            <label className="inline-check">
              <input type="checkbox" checked={filters.remote_only} onChange={(e) => setFilters({ ...filters, remote_only: e.target.checked })} />
              Remote only
            </label>
            <button onClick={() => refreshJobs()} type="button">Refresh Job Results</button>
          </div>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Filtered Jobs" actions={<button onClick={handleGenerateMatches} disabled={!selectedJobs.length || !selectedCandidateId}>Tailor Selected</button>}>
          <div className="list-stack">
            {jobs.map((job) => (
              <article key={job.id} className="list-item">
                <label className="job-select">
                  <input
                    type="checkbox"
                    checked={selectedJobs.includes(job.id)}
                    onChange={() => setSelectedJobs(toggleItem(selectedJobs, job.id))}
                  />
                  <div>
                    <h3>{job.title}</h3>
                    <p>{job.company} · {job.location} · {job.provider}</p>
                    <p className="subtle">Score: {job.score ?? "N/A"} · Skills: {job.required_skills.join(", ") || "Skill extraction pending"}</p>
                    <a href={job.apply_url} target="_blank" rel="noreferrer">Original listing</a>
                  </div>
                </label>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Tailoring Runs" actions={<button onClick={handleQueueApplications} disabled={!selectedMatches.length}>Queue Approved</button>}>
          <div className="list-stack">
            {matches.map((match) => (
              <article key={match.id} className="list-item">
                <label className="job-select">
                  <input
                    type="checkbox"
                    checked={selectedMatches.includes(match.id)}
                    onChange={() => setSelectedMatches(toggleItem(selectedMatches, match.id))}
                  />
                  <div>
                    <h3>{match.external_job.title}</h3>
                    <p>{match.external_job.company} · Fit {match.score ?? "N/A"}%</p>
                    <p className="subtle">{match.resume_version?.fit_summary}</p>
                    <pre>{match.resume_version?.tailored_resume}</pre>
                    <div className="button-row">
                      <button type="button" onClick={() => handleApprove(match.id, true)}>Approve Resume</button>
                      <button type="button" className="secondary" onClick={() => handleApprove(match.id, false)}>Reject</button>
                    </div>
                  </div>
                </label>
              </article>
            ))}
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Application Queue" actions={<button onClick={handleSubmitApplications} disabled={!selectedApplications.length}>Process Selected</button>}>
        <div className="list-stack">
          {applications.map((application) => (
            <article key={application.id} className="list-item">
              <label className="job-select">
                <input
                  type="checkbox"
                  checked={selectedApplications.includes(application.id)}
                  onChange={() => setSelectedApplications(toggleItem(selectedApplications, application.id))}
                />
                <div>
                  <h3>{application.external_job.title}</h3>
                  <p>{application.external_job.company} · {application.status} · {application.apply_mode}</p>
                  <p className="subtle">
                    {application.apply_mode === "external_redirect"
                      ? "This target will guide the user to the external portal apply flow."
                      : "This target is configured for direct API submission."}
                  </p>
                  <a href={application.external_apply_url} target="_blank" rel="noreferrer">Apply destination</a>
                </div>
              </label>
            </article>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}

function splitCsv(value) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function toggleItem(items, value) {
  return items.includes(value) ? items.filter((item) => item !== value) : [...items, value];
}
