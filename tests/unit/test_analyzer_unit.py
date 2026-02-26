import pytest
from collections import Counter
from app.analysis.analyzer import JobAnalyzer


class TestSalaryNormalization:

    def test_hourly_to_annual_conversion(self, job_analyzer):
        result = job_analyzer._normalize_salary(25.0)
        assert result == 52000.0

    def test_monthly_to_annual_conversion(self, job_analyzer):
        result = job_analyzer._normalize_salary(5000.0)
        assert result == 60000.0

    def test_annual_salary_no_conversion(self, job_analyzer):
        result = job_analyzer._normalize_salary(75000.0)
        assert result == 75000.0

    def test_zero_salary_returns_none(self, job_analyzer):
        assert job_analyzer._normalize_salary(0) is None

    def test_negative_salary_returns_none(self, job_analyzer):
        assert job_analyzer._normalize_salary(-1000) is None

    def test_unreasonably_high_salary_returns_none(self, job_analyzer):
        assert job_analyzer._normalize_salary(2000000) is None


class TestLocationCounting:

    def test_count_locations_basic(self, job_analyzer, sample_jobs):
        locations = job_analyzer._count_locations(sample_jobs)

        assert locations["England"] == 1
        assert locations["Manchester"] == 1
        assert locations["London"] == 1
        assert len(locations) == 3

    def test_count_locations_empty_list(self, job_analyzer):
        locations = job_analyzer._count_locations([])
        assert locations == {}

    def test_location_from_area_array(self, job_analyzer):
        jobs = [{
            "location": {
                "area": ["Inner London", "London", "England"],
                "display_name": ""
            }
        }]
        locations = job_analyzer._count_locations(jobs)
        assert "England" in locations
        assert locations["England"] == 1

    def test_location_from_display_name(self, job_analyzer):
        jobs = [{
            "location": {
                "area": [],
                "display_name": "Birmingham"
            }
        }]
        locations = job_analyzer._count_locations(jobs)
        assert "Birmingham" in locations

    def test_unknown_location_handling(self, job_analyzer):
        jobs = [{
            "location": {
                "area": [],
                "display_name": ""
            }
        }]
        locations = job_analyzer._count_locations(jobs)
        assert "Unknown" in locations


class TestSkillExtraction:

    def test_extract_skills_returns_counter(self, job_analyzer, sample_jobs):
        skills = job_analyzer._count_skills(sample_jobs)
        assert isinstance(skills, Counter)

    def test_extract_skills_finds_items(self, job_analyzer, sample_jobs):
        skills = job_analyzer._count_skills(sample_jobs)
        assert len(skills) > 0

    def test_extract_skills_from_title_and_description(self, job_analyzer):
        jobs = [{
            "title": "Python Developer",
            "description": "Experience with SQL and Docker required"
        }]
        skills = job_analyzer._count_skills(jobs)
        assert isinstance(skills, Counter)
        assert len(skills) > 0

    def test_per_job_counting(self, job_analyzer):
        jobs = [
            {"title": "Python Developer", "description": "Python and SQL"},
            {"title": "Python Engineer", "description": "Python and AWS"},
        ]
        skills = job_analyzer._count_skills(jobs)
        assert isinstance(skills, Counter)
        assert len(skills) > 0

    def test_count_skills_with_country(self, job_analyzer):
        jobs = [{
            "title": "Python Developer",
            "description": "Experience with SQL and Docker"
        }]
        skills_gb = job_analyzer._count_skills(jobs, country="gb")
        assert isinstance(skills_gb, Counter)
        assert len(skills_gb) > 0

        skills_de = job_analyzer._count_skills(jobs, country="de")
        assert isinstance(skills_de, Counter)
        assert len(skills_de) > 0

    def test_analyze_with_country(self, job_analyzer, sample_jobs):
        result = job_analyzer.analyze(sample_jobs, country="de")
        assert "top_skills" in result
        assert isinstance(result["top_skills"], list)


class TestSalaryStatistics:

    def test_basic_salary_stats(self, job_analyzer, sample_jobs):
        stats = job_analyzer._salary_stats(sample_jobs)

        assert stats["count"] == 3

        assert stats["min"] == 35000.0
        assert stats["max"] == 90000.0
        assert stats["avg"] > 0

    def test_salary_stats_with_no_salaries(self, job_analyzer):
        jobs = [{
            "id": "1",
            "title": "Job",
            "description": "Test",
            "location": {"area": ["London"], "display_name": "London"}
        }]
        stats = job_analyzer._salary_stats(jobs)

        assert stats["count"] == 0
        assert stats["avg"] is None
        assert stats["min"] is None
        assert stats["max"] is None


class TestSkillsByCategory:

    def test_skills_by_category_basic(self, job_analyzer):
        skills = Counter({"Python": 80, "SQL": 65, "AWS": 45, "Docker": 30, "React": 25})
        result = job_analyzer._skills_by_category(skills)

        assert "Languages" in result
        assert "Databases" in result
        assert "Cloud & DevOps" in result
        assert "Frameworks" in result

        lang_skills = {s[0] for s in result["Languages"]}
        assert "Python" in lang_skills

    def test_skills_by_category_empty(self, job_analyzer):
        result = job_analyzer._skills_by_category(Counter())
        assert result == {}

    def test_skills_by_category_preserves_order(self, job_analyzer):
        skills = Counter({"AWS": 60, "Docker": 40, "Kubernetes": 20})
        result = job_analyzer._skills_by_category(skills)

        devops = result.get("Cloud & DevOps", [])
        counts = [s[1] for s in devops]
        assert counts == sorted(counts, reverse=True)


class TestWorkTypeDetection:

    def test_detect_remote(self, job_analyzer):
        jobs = [
            {"title": "Remote Python Dev", "description": "Work from home position"},
            {"title": "Backend Dev", "description": "This is a remote role"},
        ]
        result = job_analyzer._detect_work_types(jobs)
        assert result["remote"] == 2

    def test_detect_hybrid(self, job_analyzer):
        jobs = [
            {"title": "Developer", "description": "Hybrid working arrangement"},
        ]
        result = job_analyzer._detect_work_types(jobs)
        assert result["hybrid"] == 1

    def test_detect_onsite(self, job_analyzer):
        jobs = [
            {"title": "Developer", "description": "This is an on-site position"},
        ]
        result = job_analyzer._detect_work_types(jobs)
        assert result["onsite"] == 1

    def test_detect_unspecified(self, job_analyzer):
        jobs = [
            {"title": "Developer", "description": "Python and SQL required"},
        ]
        result = job_analyzer._detect_work_types(jobs)
        assert result["unspecified"] == 1

    def test_remote_takes_priority_over_hybrid(self, job_analyzer):
        jobs = [
            {"title": "Remote Dev", "description": "hybrid or remote options"},
        ]
        result = job_analyzer._detect_work_types(jobs)
        assert result["remote"] == 1
        assert result["hybrid"] == 0

    def test_empty_jobs(self, job_analyzer):
        result = job_analyzer._detect_work_types([])
        assert result == {"remote": 0, "hybrid": 0, "onsite": 0, "unspecified": 0}


class TestExperienceLevelDetection:

    def test_detect_senior_in_title(self, job_analyzer):
        jobs = [
            {"title": "Senior Python Developer", "description": "5 years experience"},
        ]
        result = job_analyzer._detect_experience_levels(jobs)
        assert result["senior"] == 1

    def test_detect_entry_level_in_title(self, job_analyzer):
        jobs = [
            {"title": "Junior Developer", "description": "Great for graduates"},
        ]
        result = job_analyzer._detect_experience_levels(jobs)
        assert result["entry_level"] == 1

    def test_detect_from_description_fallback(self, job_analyzer):
        jobs = [
            {"title": "Python Developer", "description": "Looking for a senior engineer"},
        ]
        result = job_analyzer._detect_experience_levels(jobs)
        assert result["senior"] == 1

    def test_title_takes_priority(self, job_analyzer):
        jobs = [
            {"title": "Senior Developer", "description": "junior-friendly environment"},
        ]
        result = job_analyzer._detect_experience_levels(jobs)
        assert result["senior"] == 1
        assert result["entry_level"] == 0

    def test_unspecified(self, job_analyzer):
        jobs = [
            {"title": "Developer", "description": "Python and SQL required"},
        ]
        result = job_analyzer._detect_experience_levels(jobs)
        assert result["unspecified"] == 1

    def test_empty_jobs(self, job_analyzer):
        result = job_analyzer._detect_experience_levels([])
        assert result == {"entry_level": 0, "mid_level": 0, "senior": 0, "unspecified": 0}

    def test_graduate_is_entry_level(self, job_analyzer):
        jobs = [
            {"title": "Graduate Software Engineer", "description": "Training provided"},
        ]
        result = job_analyzer._detect_experience_levels(jobs)
        assert result["entry_level"] == 1

    def test_lead_is_senior(self, job_analyzer):
        jobs = [
            {"title": "Lead Engineer", "description": "Team management"},
        ]
        result = job_analyzer._detect_experience_levels(jobs)
        assert result["senior"] == 1


class TestSalaryByLocation:

    def test_basic_salary_by_location(self, job_analyzer, sample_jobs):
        result = job_analyzer._salary_by_location(sample_jobs)
        assert isinstance(result, dict)
        assert len(result) > 0

    def test_salary_by_location_has_stats(self, job_analyzer, sample_jobs):
        result = job_analyzer._salary_by_location(sample_jobs)
        for loc, stats in result.items():
            assert "avg" in stats
            assert "min" in stats
            assert "max" in stats
            assert "count" in stats

    def test_salary_by_location_empty(self, job_analyzer):
        result = job_analyzer._salary_by_location([])
        assert result == {}

    def test_salary_by_location_no_salary_data(self, job_analyzer):
        jobs = [{"title": "Dev", "description": "Test", "location": {"area": ["London"], "display_name": "London"}}]
        result = job_analyzer._salary_by_location(jobs)
        assert result == {}

    def test_salary_by_location_top_n(self, job_analyzer):
        jobs = []
        for i in range(20):
            jobs.append({
                "title": f"Dev {i}",
                "description": "Test",
                "location": {"area": [f"City{i}"], "display_name": f"City{i}"},
                "salary_min": 40000,
                "salary_max": 60000,
            })
        result = job_analyzer._salary_by_location(jobs, top_n=5)
        assert len(result) <= 5


class TestCompleteAnalysis:

    def test_analyze_with_sample_jobs(self, job_analyzer, sample_jobs):
        result = job_analyzer.analyze(sample_jobs)

        assert "total_jobs" in result
        assert "jobs_by_location" in result
        assert "top_skills" in result
        assert "salary_stats" in result
        assert "skills_by_category" in result
        assert "work_type_breakdown" in result
        assert "experience_breakdown" in result
        assert "salary_by_location" in result

        assert result["total_jobs"] == 3
        assert isinstance(result["jobs_by_location"], dict)
        assert isinstance(result["top_skills"], list)
        assert isinstance(result["salary_stats"], dict)
        assert isinstance(result["skills_by_category"], dict)
        assert isinstance(result["work_type_breakdown"], dict)
        assert isinstance(result["experience_breakdown"], dict)
        assert isinstance(result["salary_by_location"], dict)

        assert len(result["jobs_by_location"]) == 3

    def test_analyze_empty_list(self, job_analyzer):
        result = job_analyzer.analyze([])

        assert result["total_jobs"] == 0
        assert result["salary_stats"]["count"] == 0
        assert result["salary_stats"]["avg"] is None
        assert result["work_type_breakdown"] == {"remote": 0, "hybrid": 0, "onsite": 0, "unspecified": 0}
        assert result["experience_breakdown"] == {"entry_level": 0, "mid_level": 0, "senior": 0, "unspecified": 0}
        assert result["salary_by_location"] == {}
        assert result["skills_by_category"] == {}

    def test_top_skills_limit(self, job_analyzer, sample_jobs):
        result = job_analyzer.analyze(sample_jobs)
        assert len(result["top_skills"]) <= 20
