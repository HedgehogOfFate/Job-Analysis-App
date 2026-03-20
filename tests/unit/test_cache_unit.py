import pytest
from unittest.mock import patch, AsyncMock


class TestSearchCacheHit:

    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_hit_returns_cached_result(self, mock_search, mock_cache_get, test_client, sample_analysis_result):
        mock_cache_get.return_value = sample_analysis_result

        response = test_client.get("/api/search?what=Developer&where=London&country=gb")

        assert response.status_code == 200
        assert response.json()["total_jobs"] == sample_analysis_result["total_jobs"]
        mock_search.assert_not_called()

    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_hit_skips_adzuna_entirely(self, mock_search, mock_cache_get, test_client, sample_analysis_result):
        mock_cache_get.return_value = sample_analysis_result

        test_client.get("/api/search?what=Developer&where=London&country=gb")

        mock_search.assert_not_called()

    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_hit_preserves_full_response_structure(self, mock_search, mock_cache_get, test_client, sample_analysis_result):
        mock_cache_get.return_value = sample_analysis_result

        response = test_client.get("/api/search?what=Developer&where=London&country=gb")
        data = response.json()

        for key in ["total_jobs", "jobs_by_location", "top_skills", "salary_stats",
                    "work_type_breakdown", "experience_breakdown", "salary_by_location"]:
            assert key in data


class TestSearchCacheMiss:

    @patch("app.main.cache.set", new_callable=AsyncMock)
    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_miss_calls_adzuna(self, mock_search, mock_cache_get, mock_cache_set, test_client, sample_jobs):
        mock_cache_get.return_value = None
        mock_search.return_value = sample_jobs

        test_client.get("/api/search?what=Developer&where=London&country=gb")

        mock_search.assert_called_once()

    @patch("app.main.cache.set", new_callable=AsyncMock)
    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_miss_stores_result_after_fetch(self, mock_search, mock_cache_get, mock_cache_set, test_client, sample_jobs):
        mock_cache_get.return_value = None
        mock_search.return_value = sample_jobs

        test_client.get("/api/search?what=Developer&where=London&country=gb")

        mock_cache_set.assert_called_once()

    @patch("app.main.cache.set", new_callable=AsyncMock)
    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_stored_with_correct_key(self, mock_search, mock_cache_get, mock_cache_set, test_client, sample_jobs):
        mock_cache_get.return_value = None
        mock_search.return_value = sample_jobs

        test_client.get("/api/search?what=Developer&where=London&country=gb")

        call_args = mock_cache_set.call_args[0]
        assert call_args[0] == "search:developer:london:gb"

    @patch("app.main.cache.set", new_callable=AsyncMock)
    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_empty_results_not_cached(self, mock_search, mock_cache_get, mock_cache_set, test_client):
        mock_cache_get.return_value = None
        mock_search.return_value = []

        test_client.get("/api/search?what=NonexistentJob&country=gb")

        mock_cache_set.assert_not_called()


class TestSearchCacheDegradation:

    @patch("app.main.cache.set", new_callable=AsyncMock)
    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_get_failure_falls_back_to_adzuna(self, mock_search, mock_cache_get, mock_cache_set, test_client, sample_jobs):
        mock_cache_get.side_effect = Exception("Redis unavailable")
        mock_search.return_value = sample_jobs

        response = test_client.get("/api/search?what=Developer&country=gb")

        assert response.status_code == 200
        mock_search.assert_called_once()

    @patch("app.main.cache.set", new_callable=AsyncMock)
    @patch("app.main.cache.get", new_callable=AsyncMock)
    @patch("app.main.adzuna.search_all_jobs", new_callable=AsyncMock)
    def test_cache_set_failure_still_returns_result(self, mock_search, mock_cache_get, mock_cache_set, test_client, sample_jobs):
        mock_cache_get.return_value = None
        mock_search.return_value = sample_jobs
        mock_cache_set.side_effect = Exception("Redis write failed")

        response = test_client.get("/api/search?what=Developer&country=gb")

        assert response.status_code == 200
        assert response.json()["total_jobs"] > 0


class TestCacheClearEndpoint:

    @patch("app.main.cache.delete", new_callable=AsyncMock)
    def test_clear_cache_success(self, mock_delete, test_client):
        mock_delete.return_value = True

        response = test_client.get("/api/search/cache/clear?what=Developer&country=gb")

        assert response.status_code == 200
        assert "Cache cleared" in response.json()["message"]

    @patch("app.main.cache.delete", new_callable=AsyncMock)
    def test_clear_cache_key_not_found(self, mock_delete, test_client):
        mock_delete.return_value = False

        response = test_client.get("/api/search/cache/clear?what=Developer&country=gb")

        assert response.status_code == 404

    def test_clear_cache_missing_what(self, test_client):
        response = test_client.get("/api/search/cache/clear?country=gb")

        assert response.status_code == 400

    def test_clear_cache_missing_country(self, test_client):
        response = test_client.get("/api/search/cache/clear?what=Developer")

        assert response.status_code == 400

    @patch("app.main.cache.delete", new_callable=AsyncMock)
    def test_clear_cache_uses_normalized_key(self, mock_delete, test_client):
        mock_delete.return_value = True

        test_client.get("/api/search/cache/clear?what=DATA+ANALYST&where=London&country=GB")

        call_args = mock_delete.call_args[0]
        assert call_args[0] == "search:data analyst:london:gb"


class TestHealthEndpointWithCache:

    @patch("app.main.cache.available", new=True)
    def test_health_reports_redis_available(self, test_client):
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json()["redis_available"] is True

    @patch("app.main.cache.available", new=False)
    def test_health_reports_redis_unavailable(self, test_client):
        response = test_client.get("/health")

        assert response.status_code == 200
        assert response.json()["redis_available"] is False