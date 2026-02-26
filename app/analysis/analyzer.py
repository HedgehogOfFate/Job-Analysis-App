import re
from collections import Counter
from typing import List, Dict, Any, Optional

from .skill_extractor import SkillExtractor, _SKILL_TO_CATEGORY


class JobAnalyzer:

    _REMOTE_RE = re.compile(r"\b(remote|work from home|wfh)\b", re.IGNORECASE)
    _HYBRID_RE = re.compile(r"\b(hybrid|flexible working)\b", re.IGNORECASE)
    _ONSITE_RE = re.compile(r"\b(on-?site|in-?office|office-?based)\b", re.IGNORECASE)

    _SENIOR_RE = re.compile(r"\b(senior|lead|principal|staff|architect)\b", re.IGNORECASE)
    _MID_RE = re.compile(r"\b(mid-?level|intermediate)\b", re.IGNORECASE)
    _ENTRY_RE = re.compile(r"\b(junior|entry-?level|graduate|trainee)\b", re.IGNORECASE)

    def __init__(self, skill_extractor: Optional[SkillExtractor] = None):
        self._skill_extractor = skill_extractor or SkillExtractor()

    def analyze(self, jobs: List[Dict[str, Any]], country: str = "gb") -> Dict[str, Any]:

        total = len(jobs)
        locations = self._count_locations(jobs)
        skills = self._count_skills(jobs, country=country)
        salary_stats = self._salary_stats(jobs)
        skills_by_category = self._skills_by_category(skills)
        work_type_breakdown = self._detect_work_types(jobs)
        experience_breakdown = self._detect_experience_levels(jobs)
        salary_by_location = self._salary_by_location(jobs)

        return {
            "total_jobs": total,
            "jobs_by_location": locations,
            "top_skills": skills.most_common(20),
            "skills_by_category": skills_by_category,
            "salary_stats": salary_stats,
            "work_type_breakdown": work_type_breakdown,
            "experience_breakdown": experience_breakdown,
            "salary_by_location": salary_by_location,
        }

    def _count_locations(self, jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        c = Counter()
        for job in jobs:
            location = job.get("location", {})

            area = location.get("area", [])
            display_name = location.get("display_name", "")

            if isinstance(area, list) and area:
                loc = area[-1] if area[-1] else "Unknown"
            elif display_name:
                loc = display_name
            else:
                loc = "Unknown"

            c[loc] += 1

        return dict(c.most_common())

    def _count_skills(self, jobs: List[Dict[str, Any]], country: str = "gb") -> Counter:
        return self._skill_extractor.extract_skills_from_jobs(jobs, country=country)

    def _skills_by_category(self, skills: Counter) -> Dict[str, List]:
        cat_data: Dict[str, List] = {}
        for skill, count in skills.most_common():
            category = _SKILL_TO_CATEGORY.get(skill)
            if category:
                cat_data.setdefault(category, []).append([skill, count])
        return cat_data

    def _detect_work_types(self, jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {"remote": 0, "hybrid": 0, "onsite": 0, "unspecified": 0}
        for job in jobs:
            text = f"{job.get('title', '')} {job.get('description', '')}"
            if self._REMOTE_RE.search(text):
                counts["remote"] += 1
            elif self._HYBRID_RE.search(text):
                counts["hybrid"] += 1
            elif self._ONSITE_RE.search(text):
                counts["onsite"] += 1
            else:
                counts["unspecified"] += 1
        return counts

    def _detect_experience_levels(self, jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        counts = {"entry_level": 0, "mid_level": 0, "senior": 0, "unspecified": 0}
        for job in jobs:
            title = job.get("title", "")
            desc = job.get("description", "")

            if self._SENIOR_RE.search(title):
                counts["senior"] += 1
            elif self._ENTRY_RE.search(title):
                counts["entry_level"] += 1
            elif self._MID_RE.search(title):
                counts["mid_level"] += 1
            elif self._SENIOR_RE.search(desc):
                counts["senior"] += 1
            elif self._ENTRY_RE.search(desc):
                counts["entry_level"] += 1
            elif self._MID_RE.search(desc):
                counts["mid_level"] += 1
            else:
                counts["unspecified"] += 1
        return counts

    def _salary_by_location(self, jobs: List[Dict[str, Any]], top_n: int = 10) -> Dict[str, Dict[str, Any]]:
        loc_salaries: Dict[str, List[float]] = {}

        for job in jobs:
            location = job.get("location", {})
            area = location.get("area", [])
            display_name = location.get("display_name", "")

            if isinstance(area, list) and area:
                loc = area[-1] if area[-1] else "Unknown"
            elif display_name:
                loc = display_name
            else:
                loc = "Unknown"

            min_s = job.get("salary_min")
            max_s = job.get("salary_max")
            avg_salary = None
            if min_s and max_s:
                avg_salary = (min_s + max_s) / 2.0
            elif min_s:
                avg_salary = min_s
            elif max_s:
                avg_salary = max_s

            if avg_salary:
                normalized = self._normalize_salary(avg_salary)
                if normalized:
                    loc_salaries.setdefault(loc, []).append(normalized)

        sorted_locs = sorted(loc_salaries.items(), key=lambda x: len(x[1]), reverse=True)[:top_n]

        result = {}
        for loc, salaries in sorted_locs:
            result[loc] = {
                "avg": round(sum(salaries) / len(salaries), 2),
                "min": round(min(salaries), 2),
                "max": round(max(salaries), 2),
                "count": len(salaries),
            }
        return result

    def _normalize_salary(self, salary: float, is_predicted: bool = False) -> Optional[float]:

        if not salary or salary <= 0:
            return None

        if salary < 100:
            return salary * 40 * 52

        elif salary < 10000:
            return salary * 12

        elif salary > 1000000:
            return None

        else:
            return salary

    def _salary_stats(self, jobs: List[Dict[str, Any]]) -> Dict[str, Optional[float]]:
        salaries = []
        salary_types = {"hourly": 0, "monthly": 0, "annual": 0, "predicted": 0}

        for job in jobs:
            min_s = job.get("salary_min")
            max_s = job.get("salary_max")
            is_predicted = job.get("salary_is_predicted", False)

            if is_predicted:
                salary_types["predicted"] += 1

            avg_salary = None
            if min_s and max_s:
                avg_salary = (min_s + max_s) / 2.0
            elif min_s:
                avg_salary = min_s
            elif max_s:
                avg_salary = max_s

            if avg_salary:
                if avg_salary < 100:
                    salary_types["hourly"] += 1
                elif avg_salary < 10000:
                    salary_types["monthly"] += 1
                else:
                    salary_types["annual"] += 1

                normalized = self._normalize_salary(avg_salary, is_predicted)
                if normalized:
                    salaries.append(normalized)

        if not salaries:
            return {
                "count": 0,
                "avg": None,
                "min": None,
                "max": None,
            }

        salaries.sort()

        return {
            "count": len(salaries),
            "avg": sum(salaries) / len(salaries),
            "min": min(salaries),
            "max": max(salaries),
        }
