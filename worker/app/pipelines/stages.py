from dataclasses import dataclass


@dataclass
class PipelineContext:
    run_id: int
    job: dict
    candidate: dict
    stage_results: dict


class PipelineStage:
    name = "base"

    def run(self, context: PipelineContext) -> dict:
        raise NotImplementedError


class ProfileExtractionStage(PipelineStage):
    name = "profile_extraction"

    def run(self, context: PipelineContext) -> dict:
        strengths = [
            skill for skill in context.candidate["skills"] if skill.lower() in {item.lower() for item in context.job["required_skills"]}
        ]
        return {
            "headline": f"{context.candidate['full_name']} targeting {context.job['title']} at {context.job['company']}",
            "matched_strengths": strengths[:5],
            "candidate_summary": context.candidate["summary"],
        }


class MatchingStage(PipelineStage):
    name = "matching"

    def run(self, context: PipelineContext) -> dict:
        required = {item.lower() for item in context.job["required_skills"]}
        preferred = {item.lower() for item in context.job["preferred_skills"]}
        candidate = {item.lower() for item in context.candidate["skills"]}
        required_match = len(required & candidate)
        preferred_match = len(preferred & candidate)
        gaps = [skill for skill in context.job["required_skills"] if skill.lower() not in candidate]
        score = min(round((required_match / max(len(required), 1)) * 72 + (preferred_match / max(len(preferred), 1) if preferred else 0.5) * 18 + min(context.candidate["years_experience"] * 2, 10), 2), 100)
        return {"fit_score": score, "required_match_count": required_match, "preferred_match_count": preferred_match, "skill_gaps": gaps}


class ResumeTailoringStage(PipelineStage):
    name = "resume_tailoring"

    def run(self, context: PipelineContext) -> dict:
        strengths = context.stage_results["profile_extraction"]["matched_strengths"]
        highlights = ", ".join(strengths) if strengths else "transferable analytical and communication strengths"
        tailored_resume = (
            f"{context.candidate['full_name']}\n"
            f"Target Role: {context.job['title']}\n\n"
            f"Professional Summary:\n{context.candidate['summary']}\n\n"
            f"Role Alignment:\n"
            f"- Prioritizes {highlights}\n"
            f"- Brings {context.candidate['years_experience']} years of experience toward {context.job['employment_type']} execution\n"
            f"- Tailored for {context.job['company']} in {context.job['location']}\n\n"
            f"Core Skills:\n- " + "\n- ".join(context.candidate["skills"])
        )
        return {"tailored_resume": tailored_resume}


class ApplicationDraftStage(PipelineStage):
    name = "application_drafting"

    def run(self, context: PipelineContext) -> dict:
        score = context.stage_results["matching"]["fit_score"]
        cover_letter = (
            f"Dear Hiring Team at {context.job['company']},\n\n"
            f"I am excited to apply for the {context.job['title']} role. My background in {', '.join(context.candidate['skills'][:4])} "
            f"and {context.candidate['years_experience']} years of experience align well with your needs.\n\n"
            f"I am particularly drawn to this role because it emphasizes {', '.join(context.job['required_skills'][:3])}. "
            f"I would welcome the chance to contribute measurable impact quickly.\n\n"
            f"Sincerely,\n{context.candidate['full_name']}"
        )
        recruiter_notes = (
            f"Run #{context.run_id} achieved a {score}% fit score. "
            f"Recommend recruiter screen if score is above 75. "
            f"Current skill gaps: {', '.join(context.stage_results['matching']['skill_gaps']) or 'none'}."
        )
        return {"cover_letter": cover_letter, "recruiter_notes": recruiter_notes}

