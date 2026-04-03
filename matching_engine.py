def calculate_jaccard_index(required_skills: list, applicant_skills: list) -> float:
    """
    Calculates the Jaccard Similarity between two lists of integer skill IDs.
    Formula: Intersection / Union
    """
    # Convert lists to Python Sets for O(1) high-speed operations
    set_required = set(required_skills)
    set_applicant = set(applicant_skills)
    
    # Edge Case Guardrail: If the job requires zero skills, avoid division by zero.
    if not set_required:
        return 0.0
        
    # Calculate Intersection (Skills in common)
    intersection = set_required.intersection(set_applicant)
    
    # Calculate Union (Total unique skills across both sets)
    union = set_required.union(set_applicant)
    
    # Calculate raw score and round to 4 decimal places
    raw_score = len(intersection) / len(union)
    
    return round(raw_score, 4)