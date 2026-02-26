from pydantic import BaseModel
from typing import Dict, List, Optional

class AnalysisResult(BaseModel):
    total_jobs: int
    jobs_by_location: Dict[str, int]
    top_skills: List[List]
    salary_stats: Dict[str, Optional[float]]
