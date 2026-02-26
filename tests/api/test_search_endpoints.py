import pytest
from unittest.mock import patch


class TestSearchEndpointSuccess:

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_with_all_parameters(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Developer&country=gb&where=London"
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_jobs" in data
        assert "jobs_by_location" in data
        assert "top_skills" in data
        assert "salary_stats" in data

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_without_location(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] > 0

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_response_structure(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Data Analyst&country=gb"
        )

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data["total_jobs"], int)
        assert isinstance(data["jobs_by_location"], dict)
        assert isinstance(data["top_skills"], list)
        assert isinstance(data["salary_stats"], dict)

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_salary_stats_structure(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )

        data = response.json()
        stats = data["salary_stats"]

        assert "count" in stats
        assert "avg" in stats
        assert "min" in stats
        assert "max" in stats

class TestSearchEndpointValidation:

    def test_search_missing_country(self, test_client):
        response = test_client.get("/api/search?what=Developer")

        assert response.status_code == 400
        error = response.json()
        assert "Country parameter is required" in error["detail"]

    def test_search_missing_what(self, test_client):
        response = test_client.get("/api/search?country=gb")

        assert response.status_code == 400
        error = response.json()
        assert "Search term (what) is required" in error["detail"]

    def test_search_empty_what(self, test_client):
        response = test_client.get("/api/search?what=&country=gb")

        assert response.status_code == 400

    def test_search_missing_all_parameters(self, test_client):
        response = test_client.get("/api/search")

        assert response.status_code == 400


class TestSearchEndpointEdgeCases:

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_with_special_characters(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=C%2B%2B%20Developer&country=gb"
        )

        assert response.status_code == 200

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_with_spaces(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Software%20Engineer&country=gb&where=New%20York"
        )

        assert response.status_code == 200

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_returns_empty_results(self, mock_search, test_client):
        mock_search.return_value = []

        response = test_client.get(
            "/api/search?what=NonexistentJob&country=gb"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 0

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_with_different_countries(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        countries = ["gb", "us", "de", "fr", "au"]

        for country in countries:
            response = test_client.get(
                f"/api/search?what=Developer&country={country}"
            )
            assert response.status_code == 200


class TestSearchEndpointPerformance:

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_response_time(self, mock_search, test_client, sample_jobs):
        import time
        mock_search.return_value = sample_jobs

        start = time.time()
        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_handles_large_results(self, mock_search, test_client, large_job_dataset):
        mock_search.return_value = large_job_dataset

        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_jobs"] == 500


class TestSearchEndpointHeaders:

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_response_content_type(self, mock_search, test_client, sample_jobs):
        mock_search.return_value = sample_jobs

        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]


class TestSearchEndpointErrorHandling:

    def test_search_api_credentials_not_configured(self, test_client):
        with patch('app.main.config.ADZUNA_APP_ID', ''):
            response = test_client.get(
                "/api/search?what=Developer&country=gb"
            )

            assert response.status_code == 500
            error = response.json()
            assert "credentials not configured" in error["detail"].lower()

    @patch('app.main.adzuna.search_all_jobs')
    def test_search_handles_api_exception(self, mock_search, test_client):
        mock_search.side_effect = Exception("API Error")

        response = test_client.get(
            "/api/search?what=Developer&country=gb"
        )

        assert response.status_code in [200, 500]