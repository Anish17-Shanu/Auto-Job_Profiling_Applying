def normalize_skill(skill: str) -> str:
    return skill.strip().lower()


def compute_fit_score(required_skills: list[str], preferred_skills: list[str], candidate_skills: list[str], years_experience: int) -> float:
    normalized_candidate = {normalize_skill(skill) for skill in candidate_skills}
    normalized_required = {normalize_skill(skill) for skill in required_skills}
    normalized_preferred = {normalize_skill(skill) for skill in preferred_skills}

    required_match = len(normalized_candidate & normalized_required)
    preferred_match = len(normalized_candidate & normalized_preferred)
    required_score = (required_match / max(len(normalized_required), 1)) * 70
    preferred_score = (preferred_match / max(len(normalized_preferred), 1)) * 20 if normalized_preferred else 10
    experience_score = min(years_experience * 2, 10)
    return round(min(required_score + preferred_score + experience_score, 100), 2)


def identify_skill_gaps(required_skills: list[str], candidate_skills: list[str]) -> list[str]:
    normalized_candidate = {normalize_skill(skill) for skill in candidate_skills}
    return [skill for skill in required_skills if normalize_skill(skill) not in normalized_candidate]

