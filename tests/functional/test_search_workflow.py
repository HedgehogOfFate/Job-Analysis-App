import pytest
from unittest.mock import patch


class TestCompleteSearchWorkflow:

    @patch('app.main.adzuna.search_all_jobs')
    def test_basic_search_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Data Analyst&country=gb&where=London"
        )

        assert response.status_code == 200
        result = response.json()

        assert result["total_jobs"] > 0
        assert len(result["jobs_by_location"]) > 0
        assert len(result["top_skills"]) > 0
        assert result["salary_stats"]["count"] > 0

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_with_location_filter(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Developer&country=gb&where=Manchester"
        )

        assert response.status_code == 200
        result = response.json()

        assert result["total_jobs"] > 0
        assert "Manchester" in result["jobs_by_location"]

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_nationwide(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Software Engineer&country=gb"
        )

        assert response.status_code == 200
        result = response.json()

        assert result["total_jobs"] > 0
        assert len(result["jobs_by_location"]) >= 1


class TestSalaryAnalysisWorkflow:

    @patch('app.main.adzuna.search_all_jobs')
    def test_salary_statistics_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Data Scientist&country=gb"
        )

        result = response.json()
        stats = result["salary_stats"]

        assert stats["count"] > 0
        assert stats["avg"] > 0
        assert stats["min"] > 0
        assert stats["max"] > 0
        assert stats["min"] <= stats["avg"] <= stats["max"]

    @patch('app.main.adzuna.search_all_jobs')
    def test_salary_range_display(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )

        result = response.json()
        stats = result["salary_stats"]

        assert stats["min"] < stats["max"]
        assert stats["min"] <= stats["avg"] <= stats["max"]


class TestSkillsAnalysisWorkflow:

    @patch('app.main.adzuna.search_all_jobs')
    def test_skills_extraction_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Full Stack Developer&country=gb"
        )

        result = response.json()
        skills = result["top_skills"]

        assert len(skills) > 0

        for skill in skills:
            assert len(skill) == 2
            assert isinstance(skill[0], str)
            assert isinstance(skill[1], int)

    @patch('app.main.adzuna.search_all_jobs')
    def test_skills_ranking_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )

        result = response.json()
        skills = result["top_skills"]

        if len(skills) > 1:
            for i in range(len(skills) - 1):
                assert skills[i][1] >= skills[i + 1][1]


class TestLocationAnalysisWorkflow:

    @patch('app.main.adzuna.search_all_jobs')
    def test_location_distribution_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Data Analyst&country=gb"
        )

        result = response.json()
        locations = result["jobs_by_location"]

        assert isinstance(locations, dict)
        assert len(locations) > 0

        for location, count in locations.items():
            assert isinstance(location, str)
            assert isinstance(count, int)
            assert count > 0

    @patch('app.main.adzuna.search_all_jobs')
    def test_location_hotspots_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Software Engineer&country=gb"
        )

        result = response.json()
        locations = result["jobs_by_location"]

        if locations:
            max_location = max(locations, key=locations.get)
            assert locations[max_location] > 0


class TestErrorHandlingWorkflow:

    def test_invalid_search_workflow(self, test_client):
        response = test_client.get("/api/search?what=&country=gb")

        assert response.status_code == 400
        error = response.json()
        assert "detail" in error

    def test_missing_country_workflow(self, test_client):
        response = test_client.get("/api/search?what=Developer")

        assert response.status_code == 400
        error = response.json()
        assert "Country" in error["detail"]

    @patch('app.main.adzuna.search_all_jobs')
    def test_no_results_workflow(self, mock_search, test_client):
        mock_search.return_value = []

        response = test_client.get(
            "/api/search?what=VeryRareJob&country=gb"
        )

        assert response.status_code == 200
        result = response.json()
        assert result["total_jobs"] == 0
        assert result["salary_stats"]["count"] == 0


class TestMultipleSearchesWorkflow:

    @patch('app.main.adzuna.search_all_jobs')
    def test_sequential_searches_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response1 = test_client.get(
            "/api/search?what=Developer&country=gb"
        )
        assert response1.status_code == 200
        result1 = response1.json()

        response2 = test_client.get(
            "/api/search?what=Data Analyst&country=gb"
        )
        assert response2.status_code == 200
        result2 = response2.json()

        assert result1["total_jobs"] > 0
        assert result2["total_jobs"] > 0

    @patch('app.main.adzuna.search_all_jobs')
    def test_different_countries_workflow(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response_gb = test_client.get(
            "/api/search?what=Developer&country=gb"
        )
        assert response_gb.status_code == 200

        response_us = test_client.get(
            "/api/search?what=Developer&country=us"
        )
        assert response_us.status_code == 200


class TestCompleteUserJourney:

    @patch('app.main.adzuna.search_all_jobs')
    def test_research_journey(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        search_response = test_client.get(
            "/api/search?what=Data Scientist&country=gb"
        )
        assert search_response.status_code == 200
        result = search_response.json()

        assert result["total_jobs"] > 0
        assert result["salary_stats"]["count"] > 0
        assert len(result["top_skills"]) > 0

        csv_response = test_client.get("/api/export/csv")
        assert csv_response.status_code == 200

    @patch('app.main.adzuna.search_all_jobs')
    def test_job_seeker_journey(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Software Engineer&country=gb&where=London"
        )
        assert response.status_code == 200
        result = response.json()

        stats = result["salary_stats"]
        assert stats["avg"] > 0
        assert stats["min"] < stats["max"]

        skills = result["top_skills"]
        assert len(skills) > 0
        top_skill = skills[0][0] if skills else None
        assert top_skill is not None