def calculate_weighted_match(job_skills: list, seeker_skills: list) -> dict:
    """
    Calculates a sophisticated match score prioritizing Mandatory skills over Optional ones.
    """
    # Edge Case Guardrail: If the job requires zero skills, return 0
    if not job_skills:
        return {
            "raw_jaccard": 0.0,
            "final_weighted_score": 0.0,
            "mandatory_met": 0,
            "optional_met": 0
        }

    # 1. Parse job skills into categorized Python Sets for O(1) high-speed operations
    mandatory_requirements = {js.skill_id for js in job_skills if js.requirement_type == 'Mandatory'}
    optional_requirements = {js.skill_id for js in job_skills if js.requirement_type == 'Optional'}
    all_requirements = mandatory_requirements.union(optional_requirements)
    
    # 2. Parse seeker skills
    applicant_skills = {ss.skill_id for ss in seeker_skills}

    # 3. Standard Jaccard (Intersection over Union) - For baseline data
    intersection = all_requirements.intersection(applicant_skills)
    union = all_requirements.union(applicant_skills)
    raw_jaccard = len(intersection) / len(union) if union else 0.0

    # 4. Weighted Calculation Engine
    mandatory_met = len(mandatory_requirements.intersection(applicant_skills))
    optional_met = len(optional_requirements.intersection(applicant_skills))

    # Weight distribution: Mandatory skills are worth 2x Optional skills
    total_possible_weight = (len(mandatory_requirements) * 2.0) + (len(optional_requirements) * 1.0)
    
    if total_possible_weight == 0:
        final_score = raw_jaccard 
    else:
        achieved_weight = (mandatory_met * 2.0) + (optional_met * 1.0)
        final_score = achieved_weight / total_possible_weight

    # Apply the 40% cap per your hybrid ATS formula requirement
    weighted_skill_score = round(final_score * 0.40, 4)

    return {
        "raw_jaccard": round(raw_jaccard, 4),
        "final_weighted_score": weighted_skill_score,
        "mandatory_met": mandatory_met,
        "optional_met": optional_met
    }