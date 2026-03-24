from app.ai.matching import compute_fit_score, identify_skill_gaps


def test_fit_score_rewards_overlap():
    score = compute_fit_score(
        required_skills=["Python", "SQL", "FastAPI"],
        preferred_skills=["Docker"],
        candidate_skills=["Python", "SQL", "Docker"],
        years_experience=4,
    )
    assert score >= 70


def test_identify_skill_gaps_returns_missing_required_skills():
    gaps = identify_skill_gaps(["Python", "SQL", "FastAPI"], ["Python", "SQL"])
    assert gaps == ["FastAPI"]

