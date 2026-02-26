import pytest
from typing import List, Dict, Any
from unittest.mock import Mock
from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.clients.adzuna_client import AdzunaClient
from app.analysis.analyzer import JobAnalyzer
from app.analysis.skill_extractor import SkillExtractor


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def adzuna_client():
    return AdzunaClient("test_id", "test_key", results_per_page=50)


@pytest.fixture
def skill_extractor():
    return SkillExtractor()


@pytest.fixture
def job_analyzer():
    return JobAnalyzer()


@pytest.fixture
def sample_jobs() -> List[Dict[str, Any]]:
    return [
        {
            "id": "1",
            "title": "Data Analyst",
            "description": "We need Python and SQL skills for data analysis",
            "location": {
                "area": ["London", "Greater London", "England"],
                "display_name": "London"
            },
            "salary_min": 50000,
            "salary_max": 70000,
            "salary_is_predicted": False
        },
        {
            "id": "2",
            "title": "Senior Data Scientist",
            "description": "Machine learning and AWS experience required",
            "location": {
                "area": ["Manchester"],
                "display_name": "Manchester"
            },
            "salary_min": 80000,
            "salary_max": 100000,
            "salary_is_predicted": False
        },
        {
            "id": "3",
            "title": "Junior Analyst",
            "description": "Excel and data visualization skills needed",
            "location": {
                "area": ["London"],
                "display_name": "London"
            },
            "salary_min": 30000,
            "salary_max": 40000,
            "salary_is_predicted": True
        }
    ]


@pytest.fixture
def sample_analysis_result():
    return {
        "total_jobs": 150,
        "jobs_by_location": {
            "London": 100,
            "Manchester": 30,
            "Birmingham": 20
        },
        "top_skills": [
            ["Python", 80],
            ["SQL", 65],
            ["AWS", 45],
            ["Docker", 30],
            ["React", 25]
        ],
        "skills_by_category": {
            "Languages": [["Python", 80]],
            "Databases": [["SQL", 65]],
            "Cloud & DevOps": [["AWS", 45], ["Docker", 30]],
            "Frameworks": [["React", 25]],
        },
        "salary_stats": {
            "count": 150,
            "avg": 55000.0,
            "min": 30000.0,
            "max": 100000.0,
            "median": 52500.0,
            "period": "annual",
            "breakdown": {
                "hourly": 5,
                "monthly": 10,
                "annual": 135,
                "predicted": 50
            }
        },
        "work_type_breakdown": {
            "remote": 40,
            "hybrid": 30,
            "onsite": 50,
            "unspecified": 30
        },
        "experience_breakdown": {
            "entry_level": 20,
            "mid_level": 40,
            "senior": 60,
            "unspecified": 30
        },
        "salary_by_location": {
            "London": {"avg": 65000.0, "min": 30000.0, "max": 100000.0, "count": 100},
            "Manchester": {"avg": 55000.0, "min": 35000.0, "max": 80000.0, "count": 30},
            "Birmingham": {"avg": 50000.0, "min": 32000.0, "max": 75000.0, "count": 20},
        }
    }


@pytest.fixture
def large_job_dataset() -> List[Dict[str, Any]]:
    jobs = []
    for i in range(500):
        jobs.append({
            "id": str(i),
            "title": f"Software Engineer {i}",
            "description": "Experience with Python, SQL, AWS, Docker, Kubernetes, React, and Node.js required.",
            "location": {
                "area": [f"City{i % 10}"],
                "display_name": f"City{i % 10}"
            },
            "salary_min": 40000 + (i * 100),
            "salary_max": 60000 + (i * 100),
            "salary_is_predicted": False
        })
    return jobs


@pytest.fixture
def mock_api_response():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {"id": "1", "title": "Test Job"}
        ],
        "count": 1
    }
    return mock_response


@pytest.fixture
def mock_api_error():
    mock_response = Mock()
    mock_response.status_code = 500
    return mock_response