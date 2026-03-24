import { useEffect, useState } from "react";
import { SectionCard } from "./components/SectionCard";
import { StatCard } from "./components/StatCard";
import {
  createCandidate,
  createJob,
  createRun,
  getCurrentUser,
  getDashboard,
  getDraft,
  listCandidates,
  listJobs,
  listRuns,
  login
} from "./lib/api";

const defaultJob = {
  title: "",
  company: "",
  location: "Remote",
  employment_type: "Full-time",
  description: "",
  required_skills: "",
  preferred_skills: "",
  salary_range: ""
};

const defaultCandidate = {
  full_name: "",
  email: "",
  years_experience: 0,
  target_role: "",
  skills: "",
  summary: "",
  resume_text: ""
};

export default function App() {
  const [tokenReady, setTokenReady] = useState(Boolean(localStorage.getItem("autojob_token")));
  const [user, setUser] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [runs, setRuns] = useState([]);
  const [selectedDraft, setSelectedDraft] = useState(null);
  const [error, setError] = useState("");
  const [jobForm, setJobForm] = useState(defaultJob);
  const [candidateForm, setCandidateForm] = useState(defaultCandidate);
  const [runForm, setRunForm] = useState({ job_profile_id: "", candidate_profile_id: "" });

  const loadData = async () => {
    try {
      const [me, dashboardData, jobsData, candidatesData, runsData] = await Promise.all([
        getCurrentUser(),
        getDashboard(),
        listJobs(),
        listCandidates(),
        listRuns()
      ]);
      setUser(me);
      setDashboard(dashboardData);
      setJobs(jobsData);
      setCandidates(candidatesData);
      setRuns(runsData);
      setError("");
    } catch (err) {
      setError(err.message);
      localStorage.removeItem("autojob_token");
      setTokenReady(false);
    }
  };

  useEffect(() => {
    if (tokenReady) {
      loadData();
    }
  }, [tokenReady]);

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

  async function handleCreateJob(event) {
    event.preventDefault();
    await createJob({
      ...jobForm,
      required_skills: splitCsv(jobForm.required_skills),
      preferred_skills: splitCsv(jobForm.preferred_skills)
    });
    setJobForm(defaultJob);
    await loadData();
  }

  async function handleCreateCandidate(event) {
    event.preventDefault();
    await createCandidate({
      ...candidateForm,
      years_experience: Number(candidateForm.years_experience),
      skills: splitCsv(candidateForm.skills)
    });
    setCandidateForm(defaultCandidate);
    await loadData();
  }

  async function handleCreateRun(event) {
    event.preventDefault();
    await createRun({
      job_profile_id: Number(runForm.job_profile_id),
      candidate_profile_id: Number(runForm.candidate_profile_id)
    });
    setRunForm({ job_profile_id: "", candidate_profile_id: "" });
    await loadData();
  }

  async function handleOpenDraft(runId) {
    try {
      const draft = await getDraft(runId);
      setSelectedDraft(draft);
    } catch (err) {
      setError(err.message);
    }
  }

  if (!tokenReady) {
    return (
      <div className="auth-shell">
        <form className="auth-card" onSubmit={handleLogin}>
          <p className="eyebrow">AI Talent Operations</p>
          <h1>Auto-Job Profiling Applying</h1>
          <p className="subtle">Job targeting, candidate fit analysis, tailored resumes, and application drafts from one secure workspace.</p>
          <label>
            Email
            <input name="email" type="email" defaultValue="admin@autojob.local" required />
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
          <p className="eyebrow">Production SaaS Workspace</p>
          <h1>Auto-Job Profiling Applying</h1>
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
        <StatCard label="Job Profiles" value={dashboard?.jobs ?? 0} accent="#0d9488" />
        <StatCard label="Candidates" value={dashboard?.candidates ?? 0} accent="#dc2626" />
        <StatCard label="Queued Pipelines" value={dashboard?.queued_runs ?? 0} accent="#7c3aed" />
        <StatCard label="Average Match Score" value={`${dashboard?.avg_score ?? 0}%`} accent="#ca8a04" />
      </div>

      <div className="content-grid">
        <SectionCard title="Add Job Profile">
          <form className="form-grid" onSubmit={handleCreateJob}>
            <input placeholder="Role title" value={jobForm.title} onChange={(e) => setJobForm({ ...jobForm, title: e.target.value })} required />
            <input placeholder="Company" value={jobForm.company} onChange={(e) => setJobForm({ ...jobForm, company: e.target.value })} required />
            <input placeholder="Location" value={jobForm.location} onChange={(e) => setJobForm({ ...jobForm, location: e.target.value })} />
            <input placeholder="Employment type" value={jobForm.employment_type} onChange={(e) => setJobForm({ ...jobForm, employment_type: e.target.value })} />
            <input placeholder="Required skills" value={jobForm.required_skills} onChange={(e) => setJobForm({ ...jobForm, required_skills: e.target.value })} />
            <input placeholder="Preferred skills" value={jobForm.preferred_skills} onChange={(e) => setJobForm({ ...jobForm, preferred_skills: e.target.value })} />
            <input placeholder="Salary range" value={jobForm.salary_range} onChange={(e) => setJobForm({ ...jobForm, salary_range: e.target.value })} />
            <textarea placeholder="Job description" value={jobForm.description} onChange={(e) => setJobForm({ ...jobForm, description: e.target.value })} required />
            <button type="submit">Create Job</button>
          </form>
        </SectionCard>

        <SectionCard title="Add Candidate">
          <form className="form-grid" onSubmit={handleCreateCandidate}>
            <input placeholder="Full name" value={candidateForm.full_name} onChange={(e) => setCandidateForm({ ...candidateForm, full_name: e.target.value })} required />
            <input placeholder="Email" value={candidateForm.email} onChange={(e) => setCandidateForm({ ...candidateForm, email: e.target.value })} required />
            <input placeholder="Target role" value={candidateForm.target_role} onChange={(e) => setCandidateForm({ ...candidateForm, target_role: e.target.value })} required />
            <input type="number" placeholder="Years of experience" value={candidateForm.years_experience} onChange={(e) => setCandidateForm({ ...candidateForm, years_experience: e.target.value })} />
            <input placeholder="Skills" value={candidateForm.skills} onChange={(e) => setCandidateForm({ ...candidateForm, skills: e.target.value })} />
            <textarea placeholder="Professional summary" value={candidateForm.summary} onChange={(e) => setCandidateForm({ ...candidateForm, summary: e.target.value })} required />
            <textarea placeholder="Resume text" value={candidateForm.resume_text} onChange={(e) => setCandidateForm({ ...candidateForm, resume_text: e.target.value })} required />
            <button type="submit">Create Candidate</button>
          </form>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Launch Pipeline">
          <form className="form-grid" onSubmit={handleCreateRun}>
            <select value={runForm.job_profile_id} onChange={(e) => setRunForm({ ...runForm, job_profile_id: e.target.value })} required>
              <option value="">Select job</option>
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>{job.title} · {job.company}</option>
              ))}
            </select>
            <select value={runForm.candidate_profile_id} onChange={(e) => setRunForm({ ...runForm, candidate_profile_id: e.target.value })} required>
              <option value="">Select candidate</option>
              {candidates.map((candidate) => (
                <option key={candidate.id} value={candidate.id}>{candidate.full_name}</option>
              ))}
            </select>
            <button type="submit">Queue AI Run</button>
          </form>
        </SectionCard>

        <SectionCard title="Pipeline Activity">
          <div className="table-shell">
            <table>
              <thead>
                <tr>
                  <th>Run</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr key={run.id}>
                    <td>#{run.id}</td>
                    <td><span className={`status-pill status-${run.status}`}>{run.status}</span></td>
                    <td>{run.score ? `${run.score}%` : "Pending"}</td>
                    <td><button className="secondary small" onClick={() => handleOpenDraft(run.id)}>View Draft</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SectionCard>
      </div>

      <div className="content-grid">
        <SectionCard title="Jobs Catalog">
          <div className="list-stack">
            {jobs.map((job) => (
              <article key={job.id} className="list-item">
                <h3>{job.title}</h3>
                <p>{job.company} · {job.location}</p>
                <p className="subtle">{job.required_skills.join(", ")}</p>
              </article>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Candidate Bench">
          <div className="list-stack">
            {candidates.map((candidate) => (
              <article key={candidate.id} className="list-item">
                <h3>{candidate.full_name}</h3>
                <p>{candidate.target_role} · {candidate.years_experience} years</p>
                <p className="subtle">{candidate.skills.join(", ")}</p>
              </article>
            ))}
          </div>
        </SectionCard>
      </div>

      {selectedDraft ? (
        <SectionCard title={`Application Draft #${selectedDraft.pipeline_run_id}`} actions={<button className="secondary" onClick={() => setSelectedDraft(null)}>Close</button>}>
          <div className="draft-grid">
            <div>
              <h3>Tailored Resume</h3>
              <pre>{selectedDraft.tailored_resume}</pre>
            </div>
            <div>
              <h3>Cover Letter</h3>
              <pre>{selectedDraft.cover_letter}</pre>
            </div>
            <div>
              <h3>Recruiter Notes</h3>
              <pre>{selectedDraft.recruiter_notes}</pre>
            </div>
          </div>
        </SectionCard>
      ) : null}
    </div>
  );
}

function splitCsv(value) {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

